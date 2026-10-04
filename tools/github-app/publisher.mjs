import path from 'node:path';
import { CONFIG, BOT, REPOSITORY, DEFAULT_ROOT } from './constants.mjs';
import { PublicationError } from './errors.mjs';
import { ensure } from './guards.mjs';
import { validateText } from './validation.mjs';
import { runCommand } from './command.mjs';
import { GitHubClient } from './github-client.mjs';
import { GitWorkspace } from './git-workspace.mjs';
import { LocalFiles } from './local-files.mjs';
import { QualityGates } from './quality-gates.mjs';
import { InstallationAuth } from './installation-auth.mjs';
import { GitHubRepository } from './github-repository.mjs';
import { CommitPublisher } from './commit-publisher.mjs';
import { verifyBotCommit, verifyPr } from './verification.mjs';

export class Publisher {
  constructor({ root = DEFAULT_ROOT, command = runCommand, client = new GitHubClient(), now = Date.now } = {}) {
    this.root = path.resolve(root);
    this.command = command;
    this.client = client;
    this.now = now;
    // Explicit composition preserves injected dependencies without inheritance or installed methods.
    const invoke = (...args) => this.command(...args);
    const transport = { request: (...args) => this.client.request(...args) };
    this.workspace = new GitWorkspace({ root: this.root, command: invoke });
    this.files = new LocalFiles({ root: this.root, workspace: this.workspace });
    this.gates = new QualityGates({ root: this.root, workspace: this.workspace, command: invoke });
    this.auth = new InstallationAuth({ files: this.files, client: transport, now: () => this.now() });
    this.repository = new GitHubRepository({ client: transport, workspace: this.workspace });
    this.commits = new CommitPublisher({ client: transport, workspace: this.workspace });
  }

  async assertSnapshot(snapshot, body) {
    await this.workspace.assertSnapshot(snapshot);
    if (body) await this.files.assertBody(body);
  }

  async check({ execute = false, keyFile } = {}) {
    ensure(typeof execute === 'boolean', 'BAD_ARGUMENT');
    const snapshot = await this.workspace.snapshot();
    await this.gates.preflight(undefined, undefined, undefined, snapshot);
    await this.assertSnapshot(snapshot);
    const result = {
      mode: 'dry-run', command: 'check', repository: REPOSITORY, appId: CONFIG.appId,
      branch: snapshot.branch, head: snapshot.head, base: snapshot.base, tree: snapshot.tree,
      changedFiles: snapshot.changes.length, remoteChecks: 'not-run',
    };
    if (!execute) return result;
    return this.auth.withInstallation({ contents: 'read', pull_requests: 'read' }, keyFile, async (token, installationId) => {
      const remote = await this.repository.remoteState(token, snapshot);
      await this.assertSnapshot(snapshot);
      return { ...result, mode: 'authenticated-check', remoteChecks: 'passed', installationId,
        botLogin: BOT, remoteBranch: remote.branch };
    });
  }

  async publish({ execute = false, updatePr = false, keyFile, bodyFile, title, message } = {}) {
    ensure(typeof execute === 'boolean', 'BAD_ARGUMENT');
    ensure(typeof updatePr === 'boolean', 'BAD_ARGUMENT');
    title = validateText(title);
    message = validateText(message || title, 500);
    const body = await this.files.readBody(bodyFile);
    const snapshot = await this.workspace.snapshot();
    await this.gates.preflight(body, title, message, snapshot);
    await this.assertSnapshot(snapshot, body);
    const result = {
      mode: 'dry-run', command: 'publish', repository: REPOSITORY, appId: CONFIG.appId,
      branch: snapshot.branch, head: snapshot.head, base: snapshot.base, tree: snapshot.tree,
      changedFiles: snapshot.changes.length, remoteChecks: 'not-run',
    };
    ensure(snapshot.changes.length > 0 || snapshot.head !== snapshot.base, 'NOTHING_STAGED');
    if (!execute) return result;
    const permissions = { contents: 'write', pull_requests: 'write' };
    if (snapshot.changes.some((file) => file.startsWith('.github/workflows/'))) permissions.workflows = 'write';
    return this.auth.withInstallation(permissions, keyFile, async (token, installationId) => {
      const remote = await this.repository.remoteState(token, snapshot);
      let pr = await this.repository.existingPr(token, snapshot.branch);
      const reusedPr = Boolean(pr);
      let commit = snapshot.head;
      if (snapshot.changes.length) {
        await this.assertSnapshot(snapshot, body);
        await this.gates.preflight(body, title, message, snapshot);
        await this.assertSnapshot(snapshot, body);
        await this.repository.recheckRemote(token, snapshot, remote.branch);
        commit = await this.commits.createVerifiedCommit(token, snapshot, remote.parentTree, message);
        await this.assertSnapshot(snapshot, body);
        await this.repository.recheckRemote(token, snapshot, remote.branch);
        await this.repository.publishRef(token, snapshot, remote.branch, commit);
        try {
          await this.assertSnapshot(snapshot, body);
          await this.workspace.fetchPublished(token, snapshot, commit);
        } catch (error) {
          if (error instanceof PublicationError) {
            error.details.branch = snapshot.branch;
            error.details.commit = commit;
            error.details.branchPublished = true;
          }
          throw error;
        }
      }
      pr = await this.repository.readyPr(token, {
        pr, snapshot, commit, title, body, updatePr,
        beforeUpdate: async () => {
          await this.workspace.assertPublishedSnapshot(snapshot, commit);
          await this.files.assertBody(body);
        },
      });
      const reviewRequested = await this.repository.requestReview(token, pr.number);
      return { ...result, mode: 'published', remoteChecks: 'passed', installationId,
        commit, tree: snapshot.tree, verified: true, botLogin: BOT, prNumber: pr.number,
        url: pr.html_url, reviewRequested, existingPrMetadataPreserved: reusedPr && !updatePr };
    });
  }

  async verify({ execute = false, keyFile, number } = {}) {
    ensure(typeof execute === 'boolean', 'BAD_ARGUMENT');
    ensure(Number.isSafeInteger(number) && number > 0, 'BAD_ARGUMENT');
    const snapshot = await this.workspace.snapshot();
    if (!execute) return { mode: 'dry-run', command: 'verify', repository: REPOSITORY,
      branch: snapshot.branch, head: snapshot.head, number, remoteChecks: 'not-run' };
    return this.auth.withInstallation({ contents: 'read', pull_requests: 'read' }, keyFile, async (token) => {
      const pr = await this.client.request('GET', '/repos/' + REPOSITORY + '/pulls/' + number, token);
      verifyPr(pr, snapshot.branch, snapshot.head);
      const commit = await this.client.request('GET', '/repos/' + REPOSITORY + '/commits/' + snapshot.head, token);
      verifyBotCommit(commit, snapshot.head, snapshot.tree);
      await this.assertSnapshot(snapshot);
      return { mode: 'verified', repository: REPOSITORY, branch: snapshot.branch,
        commit: snapshot.head, tree: snapshot.tree, verified: true, botLogin: BOT, url: pr.html_url, prNumber: number };
    });
  }
}
