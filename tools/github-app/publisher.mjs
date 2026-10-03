import { createHash, createPrivateKey, createSign } from 'node:crypto';
import { execFile } from 'node:child_process';
import { realpath, stat, open, mkdtemp, writeFile, rm } from 'node:fs/promises';
import { readFileSync, constants } from 'node:fs';
import { TextDecoder } from 'node:util';
import os from 'node:os';
import path from 'node:path';

const { AbortSignal } = globalThis;
// eslint-disable-next-line security/detect-non-literal-fs-filename -- Fixed module-relative public configuration; no caller-selected path.
export const CONFIG = Object.freeze(JSON.parse(readFileSync(new URL('./config.json', import.meta.url), 'utf8')));
const REPOSITORY = 'Eneru/soulkiller';
const BOT = 'eneru-soulkiller-agent[bot]';
const API = 'https://api.github.com';
const SHA = /^[a-f0-9]{40}$/u;
const MAX_BLOB = 16 * 1024 * 1024;

const messages = {
  BAD_ARGUMENT: 'Unsupported or invalid command argument.',
  BAD_BRANCH: 'Use a permitted short-lived development branch.',
  BAD_PATH: 'A local or staged path is not permitted.',
  KEY_INVALID: 'The ignored local RSA key is missing or invalid.',
  BODY_INVALID: 'The ignored UTF-8 PR body is missing or invalid.',
  WORKSPACE_DIRTY: 'Stage all intended files and resolve other workspace changes first.',
  LICENSE_CHANGED: 'LICENSE differs from the starting main revision.',
  COMMAND_FAILED: 'A required local command failed; its output is withheld.',
  PREFLIGHT_FAILED: 'A required validation or secret scan failed; its output is withheld.',
  API_FAILED: 'A GitHub API request failed; its response is withheld.',
  APP_MISMATCH: 'The authenticated App or installation does not match public configuration.',
  TOKEN_SCOPE: 'The installation token is not restricted to the required repository and permissions.',
  REPOSITORY_MISMATCH: 'The repository, default branch or origin does not match Soulkiller.',
  STALE_PARENT: 'The local or remote parent changed or is not an eligible verified bot revision.',
  INDEX_CHANGED: 'The branch, files, index or PR body changed during publication.',
  TREE_MISMATCH: 'GitHub did not return the exact staged Git object.',
  COMMIT_UNVERIFIED: 'The commit is not verified as the configured App bot.',
  REF_RACE: 'The remote development ref changed during publication.',
  NOTHING_STAGED: 'There are no staged changes or verified published branch to resume.',
  PR_FAILED: 'The branch is published but the ready PR could not be created or verified.',
  TOKEN_REVOCATION_FAILED: 'Token revocation could not be confirmed; the token remains time-limited.',
};

export class PublicationError extends Error {
  constructor(code, details = {}) {
    super(new Map(Object.entries(messages)).get(code) || 'Publication stopped.');
    this.name = 'PublicationError';
    this.code = code;
    // Only callers construct these public identifiers; never attach raw causes or API bodies.
    this.details = details;
  }
}

function hasControl(value) {
  return [...value].some((character) => character.codePointAt(0) < 32 || character.codePointAt(0) === 127);
}

function fail(code, details) {
  throw new PublicationError(code, details);
}

function ensure(condition, code, details) {
  if (!condition) fail(code, details);
}

export function permittedBranch(branch) {
  return /^(?:codex|feature|fix|docs)\/[a-z0-9][a-z0-9._/-]{0,99}$/u.test(branch)
    && !branch.includes('..') && !branch.includes('//') && !branch.endsWith('/')
    && !branch.split('/').some((part) => part.endsWith('.lock') || part.startsWith('.'));
}

export function safeTrackedPath(file) {
  const parts = file.split('/');
  return Boolean(file) && !path.posix.isAbsolute(file) && !file.includes('\\')
    && !hasControl(file)
    && !parts.some((part) => part === '..' || part === '.' || !part)
    && !parts.some((part) => /^\.soulkiller-local$/iu.test(part) || /^\.git$/iu.test(part))
    && !parts.some((part) => /^\.env(?:$|\.(?!example$|sample$))/iu.test(part)
      || /\.(?:pem|key|p12|pfx)$/iu.test(part) || /^id_(?:rsa|ed25519)$/u.test(part));
}

export function validateText(value, limit = 200) {
  ensure(typeof value === 'string' && value.trim() && value.length <= limit
    && !hasControl(value), 'BAD_ARGUMENT');
  return value.trim();
}

export function createJwt(pem, now = Date.now()) {
  try {
    const key = createPrivateKey(pem);
    ensure(key.asymmetricKeyType === 'rsa', 'KEY_INVALID');
    const header = Buffer.from(JSON.stringify({ alg: 'RS256', typ: 'JWT' })).toString('base64url');
    const payload = Buffer.from(JSON.stringify({
      iat: Math.floor(now / 1000) - 60,
      exp: Math.floor(now / 1000) + 540,
      iss: String(CONFIG.appId),
    })).toString('base64url');
    const signingInput = header + '.' + payload;
    const signer = createSign('RSA-SHA256');
    signer.update(signingInput);
    return signingInput + '.' + signer.sign(key, 'base64url');
  } catch {
    fail('KEY_INVALID');
  }
}

export function validateTokenScope(response, requested, now = Date.now()) {
  ensure(typeof response.token === 'string' && response.token.length >= 20, 'TOKEN_SCOPE');
  ensure(Array.isArray(response.repositories) && response.repositories.length === 1
    && response.repositories[0].full_name === REPOSITORY, 'TOKEN_SCOPE');
  const expires = Date.parse(response.expires_at);
  ensure(Number.isFinite(expires) && expires > now + 1000 && expires <= now + 3_660_000, 'TOKEN_SCOPE');
  const expected = new Map(Object.entries(requested));
  const actual = new Map(Object.entries(response.permissions || {}));
  ensure([...expected].every(([name, value]) => actual.get(name) === value), 'TOKEN_SCOPE');
  ensure([...actual].every(([name, value]) =>
    (name === 'metadata' && value === 'read') || expected.get(name) === value), 'TOKEN_SCOPE');
}

export function runCommand(file, args, { cwd, input, env = {} } = {}) {
  return new Promise((resolve, reject) => {
    const childEnv = { ...process.env };
    for (const key of Object.keys(childEnv)) {
      if (/^(?:GIT_|GH_TOKEN$|GITHUB_TOKEN$)/u.test(key)) Reflect.deleteProperty(childEnv, key);
    }
    Object.assign(childEnv, {
      GIT_TERMINAL_PROMPT: '0', GIT_ASKPASS: '/bin/false',
      GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_NOSYSTEM: '1',
      GIT_NO_REPLACE_OBJECTS: '1', GIT_OPTIONAL_LOCKS: '0',
      OPENSPEC_TELEMETRY: '0', OPENSPEC_NO_UPDATE_CHECK: '1',
    }, env);
    const child = execFile(file, args, {
      cwd, env: childEnv, encoding: 'buffer', timeout: 60_000, maxBuffer: 64 * 1024 * 1024,
    }, (error, stdout) => {
      if (error) reject(new PublicationError('COMMAND_FAILED'));
      else resolve(stdout);
    });
    child.stdin?.on('error', () => {});
    child.stdin?.end(input);
  });
}

export class GitHubClient {
  constructor({ fetchImpl = globalThis.fetch, now = Date.now, timeout = 15_000 } = {}) {
    this.fetchImpl = fetchImpl;
    this.now = now;
    this.timeout = timeout;
  }

  async request(method, endpoint, auth, body, { missing = false } = {}) {
    ensure(endpoint.startsWith('/') && !endpoint.startsWith('//')
      && !endpoint.includes('..') && !endpoint.includes('#')
      && ['GET', 'POST', 'PATCH', 'DELETE'].includes(method), 'BAD_ARGUMENT');
    // This internal API transport is deliberately fixed; the CLI exposes no URL override.
    const url = new URL(endpoint, API);
    ensure(url.origin === API, 'BAD_ARGUMENT');
    try {
      const response = await this.fetchImpl(url.href, {
        method, redirect: 'error', signal: AbortSignal.timeout(this.timeout),
        headers: {
          Accept: 'application/vnd.github+json', Authorization: 'Bearer ' + auth,
          'X-GitHub-Api-Version': CONFIG.apiVersion, 'Content-Type': 'application/json',
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
      if (missing && response.status === 404) return null;
      if (!response.ok) fail('API_FAILED', { status: response.status });
      if (response.status === 204) return null;
      const raw = await response.text();
      ensure(Buffer.byteLength(raw) <= 2 * 1024 * 1024, 'API_FAILED');
      return JSON.parse(raw);
    } catch (error) {
      if (error instanceof PublicationError) throw error;
      fail('API_FAILED');
    }
  }
}

function parseIndex(raw) {
  return raw.toString('utf8').split('\0').filter(Boolean).map((record) => {
    const split = record.indexOf('\t');
    const [mode, sha, stage] = record.slice(0, split).split(' ');
    ensure(split > 0 && SHA.test(sha) && stage === '0'
      && ['100644', '100755'].includes(mode), 'WORKSPACE_DIRTY');
    const file = record.slice(split + 1);
    ensure(safeTrackedPath(file), 'BAD_PATH');
    return { mode, sha, path: file };
  });
}

function hash(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

async function confinedRead(file, allowed, code, maximum) {
  let handle;
  try {
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Caller validated the ignored path; O_NOFOLLOW rejects a swapped leaf symlink.
    handle = await open(file, constants.O_RDONLY | constants.O_NOFOLLOW);
    const info = await handle.stat();
    ensure(info.isFile() && info.size <= maximum, code);
    // Linux descriptor resolution checks the file actually opened, including ancestor swaps.
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- This is the process-owned opened descriptor, not a caller-controlled path.
    const target = await realpath('/proc/self/fd/' + handle.fd);
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Recheck the confined lexical path against the open descriptor before reading.
    ensure(target.startsWith(allowed + path.sep) && target === await realpath(file), code);
    return await handle.readFile();
  } catch {
    fail(code);
  } finally {
    await handle?.close();
  }
}

async function withFrozenIndex(bytes, operation) {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'soulkiller-publish-index-'));
  const file = path.join(directory, 'index');
  try {
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Fresh process-owned temporary directory stores the captured index only.
    await writeFile(file, bytes, { mode: 0o600 });
    return await operation({ GIT_INDEX_FILE: file });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

export class Publisher {
  constructor({
    root = '/workspaces/soulkiller', command = runCommand,
    client = new GitHubClient(), now = Date.now,
  } = {}) {
    this.root = path.resolve(root);
    this.command = command;
    this.client = client;
    this.now = now;
  }

  async git(args, options = {}) {
    return this.command('git', ['-c', 'safe.directory=' + this.root, ...args], { cwd: this.root, ...options });
  }

  async gitText(args, options = {}) {
    return (await this.git(args, options)).toString('utf8').trim();
  }

  async localPath(value, category) {
    const relative = path.relative(this.root, path.resolve(this.root, value));
    const prefix = category === 'key' ? '.soulkiller-local/github-app/' : '.soulkiller-local/';
    const code = category === 'key' ? 'KEY_INVALID' : 'BODY_INVALID';
    try {
      ensure(relative.startsWith(prefix) && !hasControl(relative)
        && !relative.split('/').some((part) => part === '..' || part === '.' || !part), code);
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Lexically confined ignored input; resolved containment is checked next.
      const full = await realpath(path.join(this.root, relative));
      const allowed = path.join(this.root, category === 'key' ? '.soulkiller-local/github-app' : '.soulkiller-local');
      // Compare to the lexical directory: escaping ancestor symlinks are rejected too.
      ensure(full.startsWith(allowed + path.sep), code);
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Contained resolved path; descriptor read later rechecks identity.
      ensure((await stat(full)).isFile(), code);
      await this.git(['check-ignore', '--quiet', '--', relative]);
      const tracked = await this.git(['ls-files', '-z', '--', relative, path.relative(this.root, full)]);
      ensure(tracked.length === 0, code);
      return full;
    } catch {
      fail(code);
    }
  }

  async readLocal(value, category) {
    const file = await this.localPath(value, category);
    const allowed = path.join(this.root, category === 'key' ? '.soulkiller-local/github-app' : '.soulkiller-local');
    const bytes = await confinedRead(file, allowed, category === 'key' ? 'KEY_INVALID' : 'BODY_INVALID',
      category === 'key' ? 16_384 : 65_536);
    return { file, bytes };
  }

  async readBody(value) {
    const { file, bytes } = await this.readLocal(value, 'body');
    ensure(bytes.length > 0 && bytes.length <= 65_536, 'BODY_INVALID');
    try {
      return { file, bytes, text: new TextDecoder('utf-8', { fatal: true }).decode(bytes), hash: hash(bytes) };
    } catch {
      fail('BODY_INVALID');
    }
  }

  async snapshot() {
    ensure(await this.gitText(['rev-parse', '--show-toplevel']) === this.root, 'REPOSITORY_MISMATCH');
    ensure(await this.gitText(['rev-parse', '--show-object-format']) === 'sha1', 'REPOSITORY_MISMATCH');
    const origin = await this.gitText(['remote', 'get-url', 'origin']);
    ensure(origin === 'https://github.com/' + REPOSITORY + '.git', 'REPOSITORY_MISMATCH');
    const branch = await this.gitText(['branch', '--show-current']);
    ensure(permittedBranch(branch), 'BAD_BRANCH');
    await this.git(['check-ref-format', '--branch', branch]);
    const head = await this.gitText(['rev-parse', 'HEAD']);
    const base = await this.gitText(['rev-parse', 'refs/remotes/origin/main']);
    ensure(SHA.test(head) && SHA.test(base), 'STALE_PARENT');
    ensure((await this.git(['diff', '--name-only', '-z'])).length === 0
      && (await this.git(['ls-files', '--others', '--exclude-standard', '-z'])).length === 0
      && (await this.git(['ls-files', '-u'])).length === 0, 'WORKSPACE_DIRTY');
    const indexFile = path.resolve(this.root, await this.gitText(['rev-parse', '--git-path', 'index']));
    ensure(indexFile.startsWith(this.root + path.sep), 'BAD_PATH');
    const indexBytes = await confinedRead(indexFile, this.root, 'BAD_PATH', 16 * 1024 * 1024);
    const indexHash = hash(indexBytes);
    const { entries, changes, tree } = await withFrozenIndex(indexBytes, async (env) => {
      const options = { env };
      const entries = parseIndex(await this.git(['ls-files', '--stage', '-z'], options));
      const againstBase = (await this.git(['diff', '--cached', '--no-renames', '--name-only', '-z', base], options))
        .toString('utf8').split('\0').filter(Boolean);
      ensure(!againstBase.some((file) => file.toLowerCase() === 'license'), 'LICENSE_CHANGED');
      const changes = (await this.git(['diff', '--cached', '--no-renames', '--name-only', '-z', head], options))
        .toString('utf8').split('\0').filter(Boolean);
      ensure(changes.every(safeTrackedPath), 'BAD_PATH');
      const tree = await this.gitText(['write-tree'], options);
      ensure(SHA.test(tree), 'TREE_MISMATCH');
      return { entries, changes, tree };
    });
    ensure(hash(await confinedRead(indexFile, this.root, 'BAD_PATH', 16 * 1024 * 1024)) === indexHash
      && await this.gitText(['rev-parse', 'HEAD']) === head
      && await this.gitText(['branch', '--show-current']) === branch, 'INDEX_CHANGED');
    return { branch, head, base, tree, entries, changes, indexFile, indexHash, indexBytes };
  }

  async preflight(body, title, message, snapshot) {
    const args = ['tools/checks/check.sh', body ? 'secrets-publication' : 'secrets'];
    if (body) args.push('--body-file', body.file, '--metadata-stdin');
    try {
      ensure(snapshot?.indexBytes, 'INDEX_CHANGED');
      await withFrozenIndex(snapshot.indexBytes, async (env) => {
        await this.command('bash', args, {
          cwd: this.root, env,
          input: body ? title + '\n' + message + '\n' + body.text + '\n' : undefined,
        });
        await this.command('openspec', ['validate', '--all', '--strict', '--no-interactive'], { cwd: this.root });
        await this.git(['diff', '--check'], { env });
        await this.git(['diff', '--cached', '--check'], { env });
      });
    } catch {
      fail('PREFLIGHT_FAILED');
    }
  }

  async assertSnapshot(snapshot, body) {
    const latest = await this.snapshot();
    ensure(latest.branch === snapshot.branch && latest.head === snapshot.head && latest.base === snapshot.base
      && latest.tree === snapshot.tree && latest.indexHash === snapshot.indexHash, 'INDEX_CHANGED');
    if (body) ensure(hash((await this.readLocal(body.file, 'body')).bytes) === body.hash, 'INDEX_CHANGED');
  }

  async withInstallation(permissions, keyFile, operation) {
    const { bytes: pem } = await this.readLocal(keyFile || CONFIG.keyFile, 'key');
    let jwt;
    try { jwt = createJwt(pem, this.now()); } finally { pem.fill(0); }
    const app = await this.client.request('GET', '/app', jwt);
    ensure(app.id === CONFIG.appId && app.slug === CONFIG.appSlug, 'APP_MISMATCH');
    const installation = await this.client.request('GET', '/repos/' + REPOSITORY + '/installation', jwt);
    ensure(Number.isSafeInteger(installation.id) && installation.app_id === CONFIG.appId
      && installation.account?.login === 'Eneru', 'APP_MISMATCH');
    const minted = await this.client.request('POST', '/app/installations/' + installation.id + '/access_tokens',
      jwt, { repositories: ['soulkiller'], permissions });
    let token = typeof minted.token === 'string' ? minted.token : '';
    let result;
    let error;
    try {
      validateTokenScope(minted, permissions, this.now());
      delete minted.token;
      result = await operation(token, installation.id);
    } catch (caught) {
      error = caught instanceof PublicationError ? caught : new PublicationError('API_FAILED');
    } finally {
      if (token) {
        try {
          await this.client.request('DELETE', '/installation/token', token);
        } catch {
          if (error) error.details.tokenRevocationFailed = true;
          else error = new PublicationError('TOKEN_REVOCATION_FAILED', result ? {
            branch: result.branch, commit: result.commit, url: result.url,
          } : {});
        }
      }
    }
    if (error) throw error;
    return { ...result, tokenRevoked: true };
  }

  async remoteRef(token, branch) {
    const value = await this.client.request('GET',
      '/repos/' + REPOSITORY + '/git/ref/heads/' + encodeURIComponent(branch), token, undefined, { missing: true });
    if (!value) return null;
    ensure(value.ref === 'refs/heads/' + branch && SHA.test(value.object?.sha)
      && value.object.type === 'commit', 'REF_RACE');
    return value.object.sha;
  }

  async remoteState(token, snapshot) {
    const repo = await this.client.request('GET', '/repos/' + REPOSITORY, token);
    ensure(repo.full_name === REPOSITORY && repo.default_branch === 'main', 'REPOSITORY_MISMATCH');
    const main = await this.remoteRef(token, 'main');
    ensure(main === snapshot.base, 'STALE_PARENT');
    const branch = await this.remoteRef(token, snapshot.branch);
    ensure(branch === null ? snapshot.head === main : branch === snapshot.head, 'STALE_PARENT');
    const parent = await this.client.request('GET', '/repos/' + REPOSITORY + '/commits/' + snapshot.head, token);
    ensure(parent.sha === snapshot.head && SHA.test(parent.commit?.tree?.sha), 'STALE_PARENT');
    if (snapshot.head !== main) this.verifyBotCommit(parent, snapshot.head);
    await this.git(['merge-base', '--is-ancestor', snapshot.base, snapshot.head]);
    return { main, branch, parentTree: parent.commit.tree.sha };
  }

  verifyBotCommit(commit, sha, tree, parent) {
    ensure(commit.sha === sha && commit.author?.login === BOT && commit.committer?.login === 'web-flow'
      && commit.commit?.committer?.name === 'GitHub'
      && commit.commit.committer.email === 'noreply@github.com'
      && commit.commit?.verification?.verified === true
      && commit.commit.verification.reason === 'valid', 'COMMIT_UNVERIFIED',
      SHA.test(sha) ? { commit: sha } : {});
    if (tree) ensure(commit.commit.tree.sha === tree, 'TREE_MISMATCH');
    if (parent) ensure(commit.parents?.length === 1 && commit.parents[0].sha === parent, 'STALE_PARENT');
  }

  async recheckRemote(token, snapshot, expectedBranch) {
    ensure(await this.remoteRef(token, 'main') === snapshot.base
      && await this.remoteRef(token, snapshot.branch) === expectedBranch, 'REF_RACE');
  }

  async existingPr(token, branch) {
    const pulls = await this.client.request('GET', '/repos/' + REPOSITORY
      + '/pulls?state=open&base=main&head=' + encodeURIComponent('Eneru:' + branch), token);
    ensure(Array.isArray(pulls) && pulls.length <= 1, 'PR_FAILED');
    if (!pulls.length) return null;
    this.verifyPr(pulls[0], branch);
    return pulls[0];
  }

  verifyPr(pr, branch, commit) {
    ensure(Number.isSafeInteger(pr.number) && pr.number > 0 && pr.user?.login === BOT
      && pr.state === 'open' && pr.draft === false && pr.base?.ref === 'main'
      && pr.base.repo?.full_name === REPOSITORY && pr.head?.ref === branch
      && pr.head.repo?.full_name === REPOSITORY
      && pr.html_url === 'https://github.com/' + REPOSITORY + '/pull/' + pr.number, 'PR_FAILED');
    if (commit) ensure(pr.head.sha === commit, 'PR_FAILED');
  }

  async check({ execute = false, keyFile } = {}) {
    const snapshot = await this.snapshot();
    await this.preflight(undefined, undefined, undefined, snapshot);
    await this.assertSnapshot(snapshot);
    const result = {
      mode: 'dry-run', command: 'check', repository: REPOSITORY, appId: CONFIG.appId,
      branch: snapshot.branch, head: snapshot.head, base: snapshot.base, tree: snapshot.tree,
      changedFiles: snapshot.changes.length, remoteChecks: 'not-run',
    };
    if (!execute) return result;
    return this.withInstallation({ contents: 'read', pull_requests: 'read' }, keyFile, async (token, installationId) => {
      const remote = await this.remoteState(token, snapshot);
      await this.assertSnapshot(snapshot);
      return { ...result, mode: 'authenticated-check', remoteChecks: 'passed', installationId,
        botLogin: BOT, remoteBranch: remote.branch };
    });
  }

  async publish({ execute = false, keyFile, bodyFile, title, message } = {}) {
    title = validateText(title);
    message = validateText(message || title, 500);
    const body = await this.readBody(bodyFile);
    const snapshot = await this.snapshot();
    await this.preflight(body, title, message, snapshot);
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
    return this.withInstallation(permissions, keyFile, async (token, installationId) => {
      const remote = await this.remoteState(token, snapshot);
      let pr = await this.existingPr(token, snapshot.branch);
      const reusedPr = Boolean(pr);
      let commit = snapshot.head;
      if (snapshot.changes.length) {
        await this.assertSnapshot(snapshot, body);
        await this.preflight(body, title, message, snapshot);
        await this.assertSnapshot(snapshot, body);
        await this.recheckRemote(token, snapshot, remote.branch);
        const entries = new Map(snapshot.entries.map((entry) => [entry.path, entry]));
        const treeEntries = [];
        for (const file of snapshot.changes) {
          const entry = entries.get(file);
          if (!entry) {
            treeEntries.push({ path: file, mode: '100644', type: 'blob', sha: null });
            continue;
          }
          const bytes = await this.git(['cat-file', 'blob', entry.sha]);
          ensure(bytes.length <= MAX_BLOB, 'BAD_PATH');
          const localBlob = createHash('sha1').update('blob ' + bytes.length + '\0').update(bytes).digest('hex');
          ensure(localBlob === entry.sha, 'TREE_MISMATCH');
          const blob = await this.client.request('POST', '/repos/' + REPOSITORY + '/git/blobs', token,
            { content: bytes.toString('base64'), encoding: 'base64' });
          ensure(blob.sha === entry.sha, 'TREE_MISMATCH');
          treeEntries.push({ path: file, mode: entry.mode, type: 'blob', sha: blob.sha });
        }
        const tree = await this.client.request('POST', '/repos/' + REPOSITORY + '/git/trees', token,
          { base_tree: remote.parentTree, tree: treeEntries });
        ensure(tree.sha === snapshot.tree, 'TREE_MISMATCH');
        const created = await this.client.request('POST', '/repos/' + REPOSITORY + '/git/commits', token,
          { message, tree: tree.sha, parents: [snapshot.head] });
        ensure(SHA.test(created.sha), 'COMMIT_UNVERIFIED');
        ensure(created.tree?.sha === snapshot.tree && created.parents?.length === 1
          && created.parents[0].sha === snapshot.head, 'TREE_MISMATCH');
        ensure(created.verification?.verified === true && created.verification.reason === 'valid',
          'COMMIT_UNVERIFIED', { commit: created.sha });
        commit = created.sha;
        const inspected = await this.client.request('GET', '/repos/' + REPOSITORY + '/commits/' + commit, token);
        this.verifyBotCommit(inspected, commit, snapshot.tree, snapshot.head);
        await this.assertSnapshot(snapshot, body);
        await this.recheckRemote(token, snapshot, remote.branch);
        if (remote.branch === null) {
          await this.client.request('POST', '/repos/' + REPOSITORY + '/git/refs', token,
            { ref: 'refs/heads/' + snapshot.branch, sha: commit });
        } else {
          await this.client.request('PATCH', '/repos/' + REPOSITORY + '/git/refs/heads/'
            + encodeURIComponent(snapshot.branch), token, { sha: commit, force: false });
        }
        ensure(await this.remoteRef(token, snapshot.branch) === commit, 'REF_RACE', {
          branch: snapshot.branch, commit, branchPublished: true,
        });
        try {
          await this.assertSnapshot(snapshot, body);
          await this.fetchPublished(token, snapshot, commit);
        } catch (error) {
          if (error instanceof PublicationError) {
            error.details.branch = snapshot.branch;
            error.details.commit = commit;
            error.details.branchPublished = true;
          }
          throw error;
        }
      }
      try {
        if (!pr) {
          pr = await this.client.request('POST', '/repos/' + REPOSITORY + '/pulls', token,
            { title, body: body.text, head: snapshot.branch, base: 'main', draft: false });
        }
        pr = await this.client.request('GET', '/repos/' + REPOSITORY + '/pulls/' + pr.number, token);
        this.verifyPr(pr, snapshot.branch, commit);
      } catch {
        fail('PR_FAILED', { branch: snapshot.branch, commit, tree: snapshot.tree, branchPublished: true });
      }
      let reviewRequested = false;
      try {
        await this.client.request('POST', '/repos/' + REPOSITORY + '/pulls/' + pr.number + '/requested_reviewers',
          token, { reviewers: ['Eneru'] });
        reviewRequested = true;
      } catch {
        // The valid PR remains available; report the review-request limitation explicitly.
      }
      return { ...result, mode: 'published', remoteChecks: 'passed', installationId,
        commit, tree: snapshot.tree, verified: true, botLogin: BOT, prNumber: pr.number,
        url: pr.html_url, reviewRequested, existingPrMetadataPreserved: reusedPr };
    });
  }

  async fetchPublished(token, snapshot, commit) {
    const basic = Buffer.from('x-access-token:' + token).toString('base64');
    await this.git(['-c', 'credential.helper=', '-c', 'http.followRedirects=false',
      'fetch', '--no-tags', '--no-write-fetch-head', '--no-recurse-submodules',
      'https://github.com/' + REPOSITORY + '.git', 'refs/heads/' + snapshot.branch], {
      env: { GIT_CONFIG_COUNT: '2', GIT_CONFIG_KEY_0: 'http.https://github.com/.extraheader',
        GIT_CONFIG_VALUE_0: '', GIT_CONFIG_KEY_1: 'http.https://github.com/.extraheader',
        GIT_CONFIG_VALUE_1: 'AUTHORIZATION: basic ' + basic },
    });
    ensure(await this.gitText(['show', '--format=%T', '--no-patch', commit]) === snapshot.tree, 'TREE_MISMATCH');
    ensure(await this.gitText(['show', '--format=%P', '--no-patch', commit]) === snapshot.head, 'STALE_PARENT');
    await this.git(['merge-base', '--is-ancestor', snapshot.head, commit]);
    await this.assertSnapshot(snapshot);
    await this.git(['update-ref', 'refs/heads/' + snapshot.branch, commit, snapshot.head]);
    // update-ref leaves the staged index and working files intact; their tree is now HEAD's tree.
    ensure(await this.gitText(['rev-parse', 'HEAD']) === commit
      && await this.gitText(['write-tree']) === snapshot.tree, 'INDEX_CHANGED');
  }

  async verify({ execute = false, keyFile, number } = {}) {
    ensure(Number.isSafeInteger(number) && number > 0, 'BAD_ARGUMENT');
    const snapshot = await this.snapshot();
    if (!execute) return { mode: 'dry-run', command: 'verify', repository: REPOSITORY,
      branch: snapshot.branch, head: snapshot.head, number, remoteChecks: 'not-run' };
    return this.withInstallation({ contents: 'read', pull_requests: 'read' }, keyFile, async (token) => {
      const pr = await this.client.request('GET', '/repos/' + REPOSITORY + '/pulls/' + number, token);
      this.verifyPr(pr, snapshot.branch, snapshot.head);
      const commit = await this.client.request('GET', '/repos/' + REPOSITORY + '/commits/' + snapshot.head, token);
      this.verifyBotCommit(commit, snapshot.head, snapshot.tree);
      await this.assertSnapshot(snapshot);
      return { mode: 'verified', repository: REPOSITORY, branch: snapshot.branch,
        commit: snapshot.head, tree: snapshot.tree, verified: true, botLogin: BOT, url: pr.html_url, prNumber: number };
    });
  }
}
