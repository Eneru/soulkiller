import { BOT, CONFIG, REPOSITORY } from './constants.mjs';
import { ensure, fail } from './guards.mjs';
import { verifyBotCommit, verifyPr } from './verification.mjs';
import { PAGE_SIZE, MAX_PAGES, REPLY_METADATA, positiveInteger, verifyCommentLocation, verifyTarget, verifyReply }
  from './review-validation.mjs';

export class ReviewReplyService {
  constructor(publisher) {
    this.publisher = publisher;
  }

  async assertInputs(snapshot, body) {
    await this.publisher.workspace.assertSnapshot(snapshot);
    await this.publisher.files.assertBody(body);
  }

  async inspect(token, number, comment, snapshot) {
    const client = this.publisher.client;
    const pr = await client.request('GET', '/repos/' + REPOSITORY + '/pulls/' + number, token);
    ensure(pr.number === number, 'PR_FAILED');
    verifyPr(pr, snapshot.branch, snapshot.head);
    const commit = await client.request('GET', '/repos/' + REPOSITORY + '/commits/' + snapshot.head, token);
    verifyBotCommit(commit, snapshot.head, snapshot.tree);
    const target = await client.request('GET', '/repos/' + REPOSITORY + '/pulls/comments/' + comment, token);
    verifyTarget(target, number, comment);
  }

  async existingReply(token, number, comment, text) {
    const matches = [];
    const seen = new Set();
    for (let page = 1; page <= MAX_PAGES; page += 1) {
      const entries = await this.publisher.client.request('GET', '/repos/' + REPOSITORY + '/pulls/'
        + number + '/comments?per_page=' + PAGE_SIZE + '&page=' + page, token);
      ensure(Array.isArray(entries) && entries.length <= PAGE_SIZE, 'REPLY_FAILED');
      for (const entry of entries) {
        verifyCommentLocation(entry, number);
        ensure(!seen.has(entry.id), 'REPLY_FAILED');
        seen.add(entry.id);
        if (entry.user?.login === BOT && entry.in_reply_to_id === comment && entry.body === text) {
          verifyReply(entry, number, comment, text);
          matches.push(entry);
        }
      }
      ensure(matches.length <= 1, 'REPLY_FAILED');
      if (entries.length < PAGE_SIZE) return matches.at(0);
    }
    fail('REPLY_FAILED');
  }

  async reply({ execute = false, keyFile, bodyFile, number, comment } = {}) {
    ensure(typeof execute === 'boolean' && positiveInteger(number) && positiveInteger(comment), 'BAD_ARGUMENT');
    const body = await this.publisher.files.readBody(bodyFile);
    ensure(body.text.trim(), 'BODY_INVALID');
    const snapshot = await this.publisher.workspace.snapshot();
    ensure(snapshot.changes.length === 0, 'WORKSPACE_DIRTY');
    await this.publisher.gates.preflight(body, REPLY_METADATA, REPLY_METADATA, snapshot);
    await this.assertInputs(snapshot, body);
    const result = {
      mode: 'dry-run', command: 'reply', repository: REPOSITORY, appId: CONFIG.appId,
      branch: snapshot.branch, head: snapshot.head, tree: snapshot.tree,
      prNumber: number, commentId: comment, remoteChecks: 'not-run',
    };
    if (!execute) return result;
    return this.publisher.auth.withInstallation({ contents: 'read', pull_requests: 'write' }, keyFile,
      async (token) => {
        await this.inspect(token, number, comment, snapshot);
        const existing = await this.existingReply(token, number, comment, body.text);
        await this.assertInputs(snapshot, body);
        await this.inspect(token, number, comment, snapshot);
        await this.assertInputs(snapshot, body);
        const response = existing || await this.publisher.client.request('POST', '/repos/' + REPOSITORY
          + '/pulls/' + number + '/comments/' + comment + '/replies', token, { body: body.text });
        verifyReply(response, number, comment, body.text);
        const confirmed = await this.publisher.client.request('GET', '/repos/' + REPOSITORY
          + '/pulls/comments/' + response.id, token);
        verifyReply(confirmed, number, comment, body.text);
        ensure(confirmed.id === response.id, 'REPLY_FAILED');
        return {
          ...result, mode: existing ? 'existing-reply' : 'replied', remoteChecks: 'passed',
          replyId: confirmed.id, url: confirmed.html_url, botLogin: BOT, existing: Boolean(existing),
        };
      });
  }
}
