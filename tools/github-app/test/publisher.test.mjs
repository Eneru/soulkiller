import test from 'node:test';
import assert from 'node:assert/strict';
import { generateKeyPairSync, verify as verifySignature } from 'node:crypto';
import { mkdtemp, mkdir, readFile, writeFile, symlink, rename, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {
  CONFIG, GitHubClient, Publisher, PublicationError, createJwt, permittedBranch,
  runCommand, safeTrackedPath, validateText, validateTokenScope,
} from '../publisher.mjs';

const { privateKey, publicKey } = generateKeyPairSync('rsa', {
  modulusLength: 2048,
  privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
  publicKeyEncoding: { type: 'spki', format: 'pem' },
});

function checkFixturePath(file) {
  assert.equal(typeof file, 'string');
  const normalized = path.resolve(file);
  assert.ok(normalized.startsWith(path.join(os.tmpdir(), 'soulkiller-app-test-')));
  return normalized;
}

async function fixtureWriteFile(file, ...args) {
  checkFixturePath(file);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Only generated, container-internal synthetic fixture paths pass the guard.
  return writeFile(file, ...args);
}

async function fixtureReadFile(file, ...args) {
  checkFixturePath(file);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Only generated, container-internal synthetic fixture paths pass the guard.
  return readFile(file, ...args);
}

async function fixtureMkdir(file, ...args) {
  checkFixturePath(file);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Only generated, container-internal synthetic fixture paths pass the guard.
  return mkdir(file, ...args);
}

async function fixtureSymlink(target, file, ...args) {
  checkFixturePath(file);
  if (path.isAbsolute(target)) checkFixturePath(target);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Destination and absolute target are confined to generated synthetic fixtures.
  return symlink(target, file, ...args);
}

async function fixtureRename(from, to) {
  checkFixturePath(from);
  checkFixturePath(to);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Both paths belong to generated, container-internal synthetic fixtures.
  return rename(from, to);
}

async function fixtureRm(file, options) {
  checkFixturePath(file);
  return rm(file, options);
}

const now = Date.UTC(2026, 9, 3, 12);
const token = 'synthetic-installation-token-for-offline-tests';
const bot = 'eneru-soulkiller-agent[bot]';
const code = (expected) => (error) => error instanceof PublicationError && error.code === expected;

function scope(permissions = { contents: 'read', pull_requests: 'read' }) {
  return {
    token, repositories: [{ full_name: 'Eneru/soulkiller' }],
    permissions: { ...permissions, metadata: 'read' }, expires_at: new Date(now + 3_600_000).toISOString(),
  };
}

async function fixture(t, { stage = true } = {}) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'soulkiller-app-test-'));
  t.after(() => fixtureRm(root, { recursive: true, force: true }));
  const git = (args, options = {}) => runCommand('git', [
    '-c', 'user.name=Offline Test', '-c', 'user.email=offline@example.invalid', ...args,
  ], { cwd: root, ...options });
  const text = async (args, options = {}) => (await git(args, options)).toString().trim();
  await git(['init', '--initial-branch=main']);
  await fixtureWriteFile(path.join(root, '.gitignore'), '.soulkiller-local/\n');
  await fixtureWriteFile(path.join(root, 'LICENSE'), 'Synthetic unchanged license\n');
  await fixtureWriteFile(path.join(root, 'README.md'), 'Initial synthetic document\n');
  await fixtureWriteFile(path.join(root, 'remove.txt'), 'Remove this synthetic file\n');
  await git(['add', '.']);
  await git(['commit', '-m', 'Synthetic baseline']);
  const base = await text(['rev-parse', 'HEAD']);
  const baseTree = await text(['show', '--format=%T', '--no-patch', 'HEAD']);
  await git(['remote', 'add', 'origin', 'https://github.com/Eneru/soulkiller.git']);
  await git(['update-ref', 'refs/remotes/origin/main', base]);
  await git(['switch', '-c', 'codex/test-publication']);
  await fixtureMkdir(path.join(root, '.soulkiller-local/github-app'), { recursive: true });
  await fixtureWriteFile(path.join(root, '.soulkiller-local/github-app/private-key.pem'), privateKey, { mode: 0o600 });
  await fixtureWriteFile(path.join(root, '.soulkiller-local/pr.md'), 'Synthetic review body\n\nRefs #7\n');
  if (stage) {
    await fixtureWriteFile(path.join(root, 'README.md'), 'A staged synthetic document\n');
    await fixtureWriteFile(path.join(root, 'binary.bin'), Buffer.from([0, 255, 128, 13, 10, 0, 65]));
    await fixtureWriteFile(path.join(root, 'executable.sh'), '#!/bin/sh\nexit 0\n', { mode: 0o755 });
    await fixtureRm(path.join(root, 'remove.txt'));
    await git(['add', '.']);
    await git(['update-index', '--chmod=+x', 'executable.sh']);
  }
  const calls = [];
  const command = async (file, args, options) => {
    calls.push({ file, args, options });
    if (file !== 'git' || args.includes('fetch')) return Buffer.alloc(0);
    return runCommand(file, args, options);
  };
  const state = { base, baseTree, branch: null, commits: new Map(), pulls: [], requests: [], revoked: 0 };
  const makeCommit = (sha, tree, parent) => ({
    sha, author: { login: bot }, committer: { login: 'web-flow' },
    commit: { tree: { sha: tree }, committer: { name: 'GitHub', email: 'noreply@github.com' },
      verification: { verified: true, reason: 'valid' } },
    parents: parent ? [{ sha: parent }] : [],
  });
  state.commits.set(base, makeCommit(base, baseTree));
  const client = {
    async request(method, endpoint, auth, body) {
      state.requests.push({ method, endpoint, auth, body });
      if (state.intercept) {
        const intercepted = await state.intercept({ method, endpoint, auth, body });
        if (intercepted !== undefined) return intercepted;
      }
      if (method === 'DELETE' && endpoint === '/installation/token') {
        state.revoked += 1;
        return null;
      }
      if (endpoint === '/app') return { id: CONFIG.appId, slug: CONFIG.appSlug };
      if (endpoint.endsWith('/installation')) {
        return { id: 123, app_id: CONFIG.appId, account: { login: 'Eneru' } };
      }
      if (endpoint.endsWith('/access_tokens')) return scope(body.permissions);
      if (endpoint === '/repos/Eneru/soulkiller') return { full_name: 'Eneru/soulkiller', default_branch: 'main' };
      if (method === 'GET' && endpoint.includes('/git/ref/heads/')) {
        const branch = decodeURIComponent(endpoint.split('/heads/')[1]);
        const sha = branch === 'main' ? state.base : state.branch;
        return sha ? { ref: 'refs/heads/' + branch, object: { type: 'commit', sha } } : null;
      }
      if (method === 'GET' && endpoint.includes('/commits/')) return state.commits.get(endpoint.split('/commits/')[1]);
      if (method === 'POST' && endpoint.endsWith('/git/blobs')) {
        const bytes = Buffer.from(body.content, 'base64');
        const sha = (await git(['hash-object', '--stdin'], { input: bytes })).toString().trim();
        return { sha };
      }
      if (method === 'POST' && endpoint.endsWith('/git/trees')) {
        const env = { GIT_INDEX_FILE: path.join(root, '.soulkiller-local/server-index') };
        await git(['read-tree', body.base_tree], { env });
        for (const entry of body.tree) {
          if (entry.sha === null) await git(['update-index', '--force-remove', '--', entry.path], { env });
          else await git(['update-index', '--add', '--cacheinfo', entry.mode, entry.sha, entry.path], { env });
        }
        return { sha: await text(['write-tree'], { env }) };
      }
      if (method === 'POST' && endpoint.endsWith('/git/commits')) {
        const sha = (await git(['commit-tree', body.tree, '-p', body.parents[0]], { input: body.message }))
          .toString().trim();
        state.commits.set(sha, makeCommit(sha, body.tree, body.parents[0]));
        return { sha, tree: { sha: body.tree }, parents: [{ sha: body.parents[0] }],
          verification: { verified: true, reason: 'valid' } };
      }
      if (method === 'POST' && endpoint.endsWith('/git/refs')) {
        assert.equal(state.branch, null);
        state.branch = body.sha;
        return {};
      }
      if (method === 'PATCH' && endpoint.includes('/git/refs/heads/')) {
        assert.equal(body.force, false);
        state.branch = body.sha;
        return {};
      }
      if (method === 'GET' && endpoint.includes('/pulls?')) return state.pulls;
      if (method === 'POST' && endpoint.endsWith('/pulls')) {
        const pr = {
          number: 17, user: { login: bot }, state: 'open', draft: body.draft,
          base: { ref: body.base, repo: { full_name: 'Eneru/soulkiller' } },
          head: { ref: body.head, repo: { full_name: 'Eneru/soulkiller' }, sha: state.branch },
          html_url: 'https://github.com/Eneru/soulkiller/pull/17',
        };
        state.pulls.push(pr);
        return pr;
      }
      if (method === 'GET' && /\/pulls\/\d+$/u.test(endpoint)) {
        const pr = state.pulls.find((entry) => endpoint.endsWith('/' + entry.number));
        return pr ? { ...pr, head: { ...pr.head, sha: state.branch } } : null;
      }
      if (method === 'POST' && endpoint.endsWith('/requested_reviewers')) return {};
      throw new Error('Unexpected offline API request');
    },
  };
  const publisher = new Publisher({ root, command, client, now: () => now });
  return { root, publisher, command, client, state, calls, git, text, makeCommit };
}

const publication = { execute: true, title: 'Publish the synthetic change', bodyFile: '.soulkiller-local/pr.md' };

test('branch/path/text validation rejects protected, traversal and secret paths', () => {
  for (const branch of ['main', 'tags/v1', 'codex/../x', 'codex/x.lock', 'codex/x//y', 'codex/.x', 'codex/x/']) {
    assert.equal(permittedBranch(branch), false);
  }
  for (const branch of ['codex/10-publisher', 'feature/first-step', 'fix/a/b', 'docs/readme']) {
    assert.equal(permittedBranch(branch), true);
  }
  for (const file of ['', '../key', '/abs', 'a\\b', '.soulkiller-local/key', '.git/config', '.env',
    'secrets/private.pem', 'id_rsa', 'dir\nname']) assert.equal(safeTrackedPath(file), false);
  for (const file of ['README.md', '.env.example', 'docs/guide.md']) assert.equal(safeTrackedPath(file), true);
  assert.equal(validateText(' title '), 'title');
  for (const text of ['', 'x\nsecret', 'x'.repeat(201)]) assert.throws(() => validateText(text), code('BAD_ARGUMENT'));
});

test('JWT is RSA signed with fixed App identity and bounded validity', () => {
  const jwt = createJwt(privateKey, now);
  const parts = jwt.split('.');
  assert.deepEqual(JSON.parse(Buffer.from(parts[0], 'base64url')), { alg: 'RS256', typ: 'JWT' });
  const payload = JSON.parse(Buffer.from(parts[1], 'base64url'));
  assert.equal(payload.iss, String(CONFIG.appId));
  assert.equal(payload.iat, now / 1000 - 60);
  assert.equal(payload.exp, now / 1000 + 540);
  assert.equal(verifySignature('RSA-SHA256', Buffer.from(parts[0] + '.' + parts[1]), publicKey,
    Buffer.from(parts[2], 'base64url')), true);
  assert.throws(() => createJwt('invalid secret key content'), code('KEY_INVALID'));
  const otherKey = generateKeyPairSync('ed25519').privateKey.export({ format: 'pem', type: 'pkcs8' });
  assert.throws(() => createJwt(otherKey), code('KEY_INVALID'));
});

test('tokens must be single-repository, short-lived and exact permission scope', () => {
  const wanted = { contents: 'read', pull_requests: 'read' };
  validateTokenScope(scope(wanted), wanted, now);
  const mutations = [
    { token: '' }, { repositories: [] }, { repositories: [{ full_name: 'Other/repo' }] },
    { repositories: [{ full_name: 'Eneru/soulkiller' }, { full_name: 'Other/repo' }] },
    { permissions: { contents: 'write', pull_requests: 'read' } },
    { permissions: { ...wanted, issues: 'write' } },
    { expires_at: new Date(now - 1).toISOString() }, { expires_at: new Date(now + 9_000_000).toISOString() },
  ];
  for (const mutation of mutations) {
    assert.throws(() => validateTokenScope({ ...scope(wanted), ...mutation }, wanted, now), code('TOKEN_SCOPE'));
  }
});

test('transport fixes host/version, rejects redirects, bounds requests and redacts response failures', async () => {
  let options;
  const client = new GitHubClient({ timeout: 250, fetchImpl: async (url, passed) => {
    assert.equal(url, 'https://api.github.com/app');
    options = passed;
    return new Response('{"id":5174172}', { status: 200 });
  } });
  assert.deepEqual(await client.request('GET', '/app', token), { id: 5174172 });
  assert.equal(options.redirect, 'error');
  assert.ok(options.signal instanceof AbortSignal);
  assert.equal(options.headers['X-GitHub-Api-Version'], '2026-03-10');
  assert.equal(options.headers.Authorization, 'Bearer ' + token);
  for (const endpoint of ['https://evil.invalid', '//evil.invalid/a', '/x/../a', '/a#b']) {
    await assert.rejects(client.request('GET', endpoint, token), code('BAD_ARGUMENT'));
  }
  await assert.rejects(client.request('PUT', '/app', token), code('BAD_ARGUMENT'));
  for (const response of [new Response('private secret response', { status: 403 }),
    new Response('not-json'), new Response('x'.repeat(2 * 1024 * 1024 + 1))]) {
    const failing = new GitHubClient({ fetchImpl: async () => response });
    await assert.rejects(failing.request('POST', '/app', token, { safe: true }), (error) =>
      code('API_FAILED')(error) && !JSON.stringify(error).includes('private secret'));
  }
  const empty = new GitHubClient({ fetchImpl: async () => new Response(null, { status: 204 }) });
  assert.equal(await empty.request('DELETE', '/installation/token', token), null);
  const absent = new GitHubClient({ fetchImpl: async () => new Response(null, { status: 404 }) });
  assert.equal(await absent.request('GET', '/missing', token, undefined, { missing: true }), null);
  const network = new GitHubClient({ fetchImpl: async () => { throw new Error(token); } });
  await assert.rejects(network.request('GET', '/app', token), code('API_FAILED'));
});

test('command execution redacts failures and supports binary stdin/stdout', async () => {
  assert.deepEqual(await runCommand(process.execPath,
    ['-e', 'process.stdin.pipe(process.stdout)'], { input: Buffer.from([0, 255, 1]) }), Buffer.from([0, 255, 1]));
  await assert.rejects(runCommand(process.execPath,
    ['-e', 'console.error("synthetic secret");process.exit(1)']), (error) =>
    code('COMMAND_FAILED')(error) && !error.message.includes('synthetic secret'));
});

test('ignored local paths allow synthetic key/body and reject missing, tracked and symlink escapes', async (t) => {
  const f = await fixture(t);
  assert.equal(await f.publisher.localPath('.soulkiller-local/github-app/private-key.pem', 'key'),
    path.join(f.root, '.soulkiller-local/github-app/private-key.pem'));
  for (const file of ['LICENSE', '../outside.pem', '.soulkiller-local/pr.md',
    '.soulkiller-local/github-app/missing.pem']) {
    await assert.rejects(f.publisher.localPath(file, 'key'), code('KEY_INVALID'));
  }
  await fixtureSymlink(path.join(f.root, 'LICENSE'), path.join(f.root, '.soulkiller-local/github-app/escape.pem'));
  await assert.rejects(f.publisher.localPath('.soulkiller-local/github-app/escape.pem', 'key'), code('KEY_INVALID'));
  await f.git(['add', '-f', '.soulkiller-local/github-app/private-key.pem']);
  await assert.rejects(f.publisher.localPath('.soulkiller-local/github-app/private-key.pem', 'key'), code('KEY_INVALID'));
  await fixtureWriteFile(path.join(f.root, '.soulkiller-local/bad.md'), Buffer.from([255, 254]));
  await assert.rejects(f.publisher.readBody('.soulkiller-local/bad.md'), code('BODY_INVALID'));
  await fixtureWriteFile(path.join(f.root, '.soulkiller-local/empty.md'), '');
  await assert.rejects(f.publisher.readBody('.soulkiller-local/empty.md'), code('BODY_INVALID'));
});


test('descriptor reads reject leaf replacement during ignored-path Git checks', async (t) => {
  for (const category of ['body', 'key']) {
    const f = await fixture(t);
    const relative = category === 'body' ? '.soulkiller-local/pr.md' : CONFIG.keyFile;
    let swapped = false;
    f.publisher.command = async (file, args, options) => {
      const result = await f.command(file, args, options);
      if (!swapped && file === 'git' && args.includes('ls-files') && args.includes(relative)) {
        swapped = true;
        await fixtureRm(path.join(f.root, relative));
        await fixtureSymlink(path.join(f.root, 'README.md'), path.join(f.root, relative));
      }
      return result;
    };
    await assert.rejects(f.publisher.readLocal(relative, category),
      code(category === 'body' ? 'BODY_INVALID' : 'KEY_INVALID'));
    assert.equal(swapped, true);
    assert.equal(f.state.requests.length, 0);
  }
});

test('descriptor reads reject ancestor replacement after path validation', async (t) => {
  for (const category of ['body', 'key']) {
    const f = await fixture(t);
    const relative = category === 'body' ? '.soulkiller-local/pr.md' : CONFIG.keyFile;
    const directory = path.join(f.root, category === 'body' ? '.soulkiller-local' : '.soulkiller-local/github-app');
    const archive = path.join(f.root, category === 'body' ? 'local-archive' : '.soulkiller-local/key-archive');
    let swapped = false;
    f.publisher.command = async (file, args, options) => {
      const result = await f.command(file, args, options);
      if (!swapped && file === 'git' && args.includes('ls-files') && args.includes(relative)) {
        swapped = true;
        await fixtureRename(directory, archive);
        await fixtureSymlink(archive, directory);
      }
      return result;
    };
    await assert.rejects(f.publisher.readLocal(relative, category),
      code(category === 'body' ? 'BODY_INVALID' : 'KEY_INVALID'));
    assert.equal(swapped, true);
    assert.equal(f.state.requests.length, 0);
  }
});

test('snapshot and uploads derive entries from frozen bytes despite a live-index ABA swap', async (t) => {
  const f = await fixture(t);
  const index = path.join(f.root, '.git/index');
  const original = await fixtureReadFile(index);
  const originalReadme = await fixtureReadFile(path.join(f.root, 'README.md'));
  await fixtureWriteFile(path.join(f.root, 'README.md'), 'UNSCANNED SYNTHETIC INDEX B');
  await f.git(['add', 'README.md']);
  const substituted = await fixtureReadFile(index);
  await fixtureWriteFile(path.join(f.root, 'README.md'), originalReadme);
  await fixtureWriteFile(index, original);
  let swapped = false;
  f.publisher.command = async (file, args, options) => {
    if (!swapped && file === 'git' && args.includes('--stage') && options.env?.GIT_INDEX_FILE) {
      swapped = true;
      await fixtureWriteFile(index, substituted);
      const result = await f.command(file, args, options);
      await fixtureWriteFile(index, original);
      return result;
    }
    return f.command(file, args, options);
  };
  const result = await f.publisher.publish(publication);
  assert.equal(result.verified, true);
  assert.equal(swapped, true);
  const uploads = f.state.requests.filter((request) => request.endpoint.endsWith('/git/blobs'));
  assert.ok(uploads.some((request) => Buffer.from(request.body.content, 'base64').equals(originalReadme)));
  assert.equal(uploads.some((request) => Buffer.from(request.body.content, 'base64')
    .includes(Buffer.from('UNSCANNED SYNTHETIC INDEX B'))), false);
});

test('snapshot rejects a live index edit before any authentication or upload', async (t) => {
  const f = await fixture(t);
  let edited = false;
  f.publisher.command = async (file, args, options) => {
    const result = await f.command(file, args, options);
    if (!edited && file === 'git' && args.includes('--stage') && options.env?.GIT_INDEX_FILE) {
      edited = true;
      await fixtureWriteFile(path.join(f.root, 'README.md'), 'Concurrent synthetic index edit');
      await f.git(['add', 'README.md']);
    }
    return result;
  };
  await assert.rejects(f.publisher.publish(publication), code('INDEX_CHANGED'));
  assert.equal(f.state.requests.length, 0);
});

test('the immutable captured PR body reaches secret scanning even if its file is swapped temporarily', async (t) => {
  const f = await fixture(t);
  const body = await f.publisher.readBody(publication.bodyFile);
  const snapshot = await f.publisher.snapshot();
  let scanned = false;
  f.publisher.command = async (file, args, options) => {
    if (file === 'bash') {
      await fixtureWriteFile(body.file, 'Different mutable synthetic body');
      assert.ok(options.input.includes(body.text));
      scanned = true;
      await fixtureWriteFile(body.file, body.bytes);
    }
    return f.command(file, args, options);
  };
  await f.publisher.preflight(body, publication.title, publication.title, snapshot);
  await f.publisher.assertSnapshot(snapshot, body);
  assert.equal(scanned, true);
});

test('dry run performs fixed local gates without key reads or any API request', async (t) => {
  const f = await fixture(t);
  await fixtureRm(path.join(f.root, '.soulkiller-local/github-app/private-key.pem'));
  const result = await f.publisher.publish({ ...publication, execute: false });
  assert.equal(result.mode, 'dry-run');
  assert.equal(result.changedFiles, 4);
  assert.equal(f.state.requests.length, 0);
  const scan = f.calls.find((call) => call.file === 'bash');
  assert.deepEqual(scan.args, ['tools/checks/check.sh', 'secrets-publication', '--body-file',
    path.join(f.root, '.soulkiller-local/pr.md'), '--metadata-stdin']);
  assert.equal(scan.options.input, publication.title + '\n' + publication.title + '\n'
    + 'Synthetic review body\n\nRefs #7\n\n');
  assert.ok(scan.options.env.GIT_INDEX_FILE.startsWith(path.join(os.tmpdir(), 'soulkiller-publish-index-')));
  assert.ok(f.calls.some((call) => call.file === 'openspec'
    && call.args.join(' ') === 'validate --all --strict --no-interactive'));
  assert.ok(f.calls.some((call) => call.args.join(' ').endsWith('diff --cached --check')));
  assert.equal((await f.publisher.check()).mode, 'dry-run');
  assert.equal((await f.publisher.verify({ number: 17 })).mode, 'dry-run');
});

test('preflight failure blocks authentication and does not echo scanner output', async (t) => {
  const f = await fixture(t);
  f.publisher.command = async (file, args, options) => {
    if (file === 'bash') throw new Error('secret scanner output');
    return f.command(file, args, options);
  };
  await assert.rejects(f.publisher.publish(publication), (error) =>
    code('PREFLIGHT_FAILED')(error) && !error.message.includes('secret scanner output'));
  assert.equal(f.state.requests.length, 0);
});

test('snapshot rejects dirty work, unknown files, LICENSE changes, unsafe index entries and protected branch', async (t) => {
  const f = await fixture(t);
  await fixtureWriteFile(path.join(f.root, 'untracked.txt'), 'untracked');
  await assert.rejects(f.publisher.snapshot(), code('WORKSPACE_DIRTY'));
  await fixtureRm(path.join(f.root, 'untracked.txt'));
  await fixtureWriteFile(path.join(f.root, 'README.md'), 'unstaged');
  await assert.rejects(f.publisher.snapshot(), code('WORKSPACE_DIRTY'));
  await f.git(['add', 'README.md']);
  await fixtureWriteFile(path.join(f.root, 'LICENSE'), 'Changed');
  await f.git(['add', 'LICENSE']);
  await assert.rejects(f.publisher.snapshot(), code('LICENSE_CHANGED'));
  await f.git(['restore', '--source=HEAD', '--staged', '--worktree', 'LICENSE']);
  await fixtureWriteFile(path.join(f.root, '.env'), 'synthetic local env');
  await f.git(['add', '.env']);
  await assert.rejects(f.publisher.snapshot(), code('BAD_PATH'));
  await f.git(['rm', '-f', '.env']);
  await fixtureSymlink('README.md', path.join(f.root, 'link.md'));
  await f.git(['add', 'link.md']);
  await assert.rejects(f.publisher.snapshot(), code('WORKSPACE_DIRTY'));
  await f.git(['rm', '-f', 'link.md']);
  await f.git(['switch', 'main']);
  await assert.rejects(f.publisher.snapshot(), code('BAD_BRANCH'));
});

test('snapshot rejects incorrect origin and detects index/body/branch changes', async (t) => {
  const f = await fixture(t);
  await f.git(['remote', 'set-url', 'origin', 'https://github.com/Other/repo.git']);
  await assert.rejects(f.publisher.snapshot(), code('REPOSITORY_MISMATCH'));
  await f.git(['remote', 'set-url', 'origin', 'https://github.com/Eneru/soulkiller.git']);
  const snapshot = await f.publisher.snapshot();
  const body = await f.publisher.readBody(publication.bodyFile);
  await fixtureWriteFile(body.file, 'Edited ignored body');
  await assert.rejects(f.publisher.assertSnapshot(snapshot, body), code('INDEX_CHANGED'));
  await fixtureWriteFile(path.join(f.root, 'README.md'), 'new staged document');
  await f.git(['add', 'README.md']);
  await assert.rejects(f.publisher.assertSnapshot(snapshot), code('INDEX_CHANGED'));
});

test('authenticated check verifies fixed installation and repository then revokes its read token', async (t) => {
  const f = await fixture(t);
  const result = await f.publisher.check({ execute: true });
  assert.equal(result.remoteChecks, 'passed');
  assert.equal(result.installationId, 123);
  assert.equal(result.tokenRevoked, true);
  assert.equal(f.state.revoked, 1);
  const mint = f.state.requests.find((request) => request.endpoint.endsWith('/access_tokens'));
  assert.deepEqual(mint.body, { repositories: ['soulkiller'],
    permissions: { contents: 'read', pull_requests: 'read' } });
  assert.equal(f.state.requests.some((request) => request.endpoint.endsWith('/git/commits')), false);
});

test('App and installation mismatch stop before minting a token', async (t) => {
  const f = await fixture(t);
  f.state.intercept = ({ endpoint }) => endpoint === '/app' ? { id: 1, slug: 'other' } : undefined;
  await assert.rejects(f.publisher.check({ execute: true }), code('APP_MISMATCH'));
  assert.equal(f.state.requests.some((request) => request.endpoint.endsWith('/access_tokens')), false);
  f.state.intercept = ({ endpoint }) => endpoint.endsWith('/installation')
    ? { id: 123, app_id: CONFIG.appId, account: { login: 'Other' } } : undefined;
  await assert.rejects(f.publisher.check({ execute: true }), code('APP_MISMATCH'));
});

test('invalid token scope is revoked before rejecting and revocation errors remain explicit', async (t) => {
  const f = await fixture(t);
  f.state.intercept = ({ endpoint, body }) => endpoint.endsWith('/access_tokens')
    ? { ...scope(body.permissions), permissions: { ...body.permissions, administration: 'write' } } : undefined;
  await assert.rejects(f.publisher.check({ execute: true }), code('TOKEN_SCOPE'));
  assert.equal(f.state.revoked, 1);
  f.state.intercept = ({ method }) => {
    if (method === 'DELETE') throw new Error('revocation secret response');
    return undefined;
  };
  await assert.rejects(f.publisher.check({ execute: true }), code('TOKEN_REVOCATION_FAILED'));
  f.state.intercept = ({ method, endpoint, body }) => {
    if (method === 'DELETE') throw new Error('revocation secret');
    if (endpoint.endsWith('/access_tokens')) return { ...scope(body.permissions), repositories: [] };
    return undefined;
  };
  await assert.rejects(f.publisher.check({ execute: true }), (error) =>
    code('TOKEN_SCOPE')(error) && error.details.tokenRevocationFailed === true);
});

test('remote main/branch mismatch, wrong repository and unsigned prior parent fail closed', async (t) => {
  const f = await fixture(t);
  f.state.base = 'a'.repeat(40);
  await assert.rejects(f.publisher.publish(publication), code('STALE_PARENT'));
  f.state.base = await f.text(['rev-parse', 'HEAD']);
  f.state.branch = 'b'.repeat(40);
  await assert.rejects(f.publisher.publish(publication), code('STALE_PARENT'));
  f.state.branch = null;
  f.state.intercept = ({ endpoint }) => endpoint === '/repos/Eneru/soulkiller'
    ? { full_name: 'Other/repo', default_branch: 'main' } : undefined;
  await assert.rejects(f.publisher.publish(publication), code('REPOSITORY_MISMATCH'));
  f.state.intercept = undefined;
  await f.git(['commit', '-m', 'Unverified local commit']);
  const snapshot = await f.publisher.snapshot();
  f.state.branch = snapshot.head;
  f.state.commits.set(snapshot.head, {
    ...f.makeCommit(snapshot.head, snapshot.tree, snapshot.base), author: { login: 'Eneru' },
  });
  await assert.rejects(f.publisher.publish(publication), code('COMMIT_UNVERIFIED'));
  assert.equal(f.state.requests.some((request) => request.endpoint.endsWith('/git/refs')), false);
});

test('publication preserves binary bytes, executable mode, deletion, parent, index and ready independent PR', async (t) => {
  const f = await fixture(t);
  const before = await f.publisher.snapshot();
  const result = await f.publisher.publish(publication);
  assert.equal(result.mode, 'published');
  assert.equal(result.verified, true);
  const inspected = f.state.commits.get(result.commit);
  assert.equal(inspected.author.login, bot);
  assert.equal(inspected.committer.login, 'web-flow');
  assert.deepEqual(inspected.commit.committer, { name: 'GitHub', email: 'noreply@github.com' });
  assert.equal(result.reviewRequested, true);
  assert.equal(result.url, 'https://github.com/Eneru/soulkiller/pull/17');
  assert.equal(f.state.revoked, 1);
  assert.equal(await f.text(['rev-parse', 'HEAD']), result.commit);
  assert.equal(await f.text(['write-tree']), before.tree);
  assert.equal(await f.text(['diff', '--cached', '--name-only']), '');
  assert.deepEqual(await fixtureReadFile(path.join(f.root, 'binary.bin')), Buffer.from([0, 255, 128, 13, 10, 0, 65]));
  const blobs = f.state.requests.filter((request) => request.endpoint.endsWith('/git/blobs'));
  assert.ok(blobs.some((request) => Buffer.from(request.body.content, 'base64')
    .equals(Buffer.from([0, 255, 128, 13, 10, 0, 65]))));
  assert.ok(blobs.every((request) => request.body.encoding === 'base64'));
  const tree = f.state.requests.find((request) => request.endpoint.endsWith('/git/trees')).body;
  assert.equal(tree.base_tree, f.state.baseTree);
  assert.ok(tree.tree.some((entry) => entry.path === 'executable.sh' && entry.mode === '100755'));
  assert.ok(tree.tree.some((entry) => entry.path === 'remove.txt' && entry.sha === null));
  const commit = f.state.requests.find((request) => request.endpoint.endsWith('/git/commits')).body;
  assert.deepEqual(Object.keys(commit).sort(), ['message', 'parents', 'tree']);
  assert.deepEqual(commit.parents, [before.head]);
  const pr = f.state.requests.find((request) => request.method === 'POST' && request.endpoint.endsWith('/pulls')).body;
  assert.equal(pr.draft, false);
  assert.equal(pr.base, 'main');
  assert.equal(pr.head, before.branch);
  const fetchCall = f.calls.find((call) => call.file === 'git' && call.args.includes('fetch'));
  assert.equal(fetchCall.options.env.GIT_CONFIG_VALUE_0, '');
  assert.ok(fetchCall.options.env.GIT_CONFIG_VALUE_1.startsWith('AUTHORIZATION: basic '));
  assert.equal(fetchCall.args.some((arg) => arg.includes(token)), false);
  const checked = await f.publisher.verify({ execute: true, number: 17 });
  assert.equal(checked.verified, true);
  assert.equal(checked.tokenRevoked, true);
});


test('verified App-author commits require the exact GitHub platform committer before any ref is published', async (t) => {
  for (const scenario of ['login', 'name', 'email', 'missing', 'signature']) {
    const f = await fixture(t);
    f.state.intercept = ({ method, endpoint }) => {
      if (method !== 'GET' || !endpoint.includes('/commits/') || endpoint.endsWith(f.state.base)) return undefined;
      const saved = f.state.commits.get(endpoint.split('/commits/')[1]);
      if (scenario === 'login') return { ...saved, committer: { login: 'Eneru' } };
      if (scenario === 'name') return { ...saved, commit: { ...saved.commit,
        committer: { ...saved.commit.committer, name: 'Unexpected signer' } } };
      if (scenario === 'email') return { ...saved, commit: { ...saved.commit,
        committer: { ...saved.commit.committer, email: 'other@example.invalid' } } };
      if (scenario === 'missing') return { ...saved, commit: { ...saved.commit, committer: undefined } };
      return { ...saved, commit: { ...saved.commit, verification: { verified: false, reason: 'unsigned' } } };
    };
    await assert.rejects(f.publisher.publish(publication), code('COMMIT_UNVERIFIED'));
    assert.equal(f.state.branch, null);
    assert.equal(f.state.requests.some((request) => request.method === 'POST'
      && request.endpoint.endsWith('/git/refs')), false);
    assert.equal(f.state.requests.some((request) => request.method === 'PATCH'
      && request.endpoint.includes('/git/refs/heads/')), false);
    assert.equal(await f.text(['rev-parse', 'HEAD']), f.state.base);
    assert.equal(f.state.revoked, 1);
  }
});

test('workflow write permission is requested only when staged workflow changes need it', async (t) => {
  const f = await fixture(t);
  await fixtureMkdir(path.join(f.root, '.github/workflows'), { recursive: true });
  await fixtureWriteFile(path.join(f.root, '.github/workflows/check.yml'), 'name: synthetic\n');
  await f.git(['add', '.github/workflows/check.yml']);
  await f.publisher.publish(publication);
  const mint = f.state.requests.find((request) => request.endpoint.endsWith('/access_tokens'));
  assert.deepEqual(mint.body.permissions, { contents: 'write', pull_requests: 'write', workflows: 'write' });
});

test('blob/tree mismatch and unverified/wrong-identity commit do not publish a ref', async (t) => {
  for (const scenario of ['blob', 'tree', 'signature', 'identity']) {
    const f = await fixture(t);
    f.state.intercept = async ({ method, endpoint, body }) => {
      if (scenario === 'blob' && endpoint.endsWith('/git/blobs')) return { sha: 'a'.repeat(40) };
      if (scenario === 'tree' && endpoint.endsWith('/git/trees')) return { sha: 'a'.repeat(40) };
      if (scenario === 'signature' && endpoint.endsWith('/git/commits')) {
        return { sha: 'a'.repeat(40), tree: { sha: body.tree }, parents: [{ sha: body.parents[0] }],
          verification: { verified: false, reason: 'unsigned' } };
      }
      if (scenario === 'identity' && method === 'GET' && endpoint.includes('/commits/')
        && !endpoint.endsWith(f.state.base)) {
        const saved = f.state.commits.get(endpoint.split('/commits/')[1]);
        return { ...saved, author: { login: 'Eneru' } };
      }
      return undefined;
    };
    await assert.rejects(f.publisher.publish(publication), (error) => {
      assert.equal(code(['blob', 'tree'].includes(scenario) ? 'TREE_MISMATCH' : 'COMMIT_UNVERIFIED')(error), true);
      if (['signature', 'identity'].includes(scenario)) assert.match(error.details.commit, /^[a-f0-9]{40}$/u);
      assert.deepEqual(Object.keys(error.details), ['signature', 'identity'].includes(scenario) ? ['commit'] : []);
      return true;
    });
    assert.equal(f.state.branch, null);
    assert.equal(f.state.revoked, 1);
    assert.equal(await f.text(['rev-parse', 'HEAD']), f.state.base);
  }
});

test('changing index/body or advancing remote head before ref publication refuses without overwrite', async (t) => {
  for (const scenario of ['index', 'body', 'branch']) {
    const f = await fixture(t);
    f.state.intercept = async ({ method, endpoint }) => {
      if (method === 'GET' && endpoint.includes('/commits/') && !endpoint.endsWith(f.state.base)) {
        if (scenario === 'index') {
          await fixtureWriteFile(path.join(f.root, 'README.md'), 'concurrently staged change');
          await f.git(['add', 'README.md']);
        } else if (scenario === 'body') {
          await fixtureWriteFile(path.join(f.root, '.soulkiller-local/pr.md'), 'concurrent body');
        } else {
          f.state.branch = 'a'.repeat(40);
        }
      }
      return undefined;
    };
    await assert.rejects(f.publisher.publish(publication), code(scenario === 'branch' ? 'REF_RACE' : 'INDEX_CHANGED'));
    assert.equal(f.state.requests.some((request) => request.method === 'POST'
      && request.endpoint.endsWith('/git/refs')), false);
    assert.equal(await f.text(['rev-parse', 'HEAD']), f.state.base);
  }
});

test('existing verified bot branch advances only with force=false and reuses its PR', async (t) => {
  const f = await fixture(t);
  await f.publisher.publish(publication);
  await fixtureWriteFile(path.join(f.root, 'README.md'), 'Second staged change\n');
  await f.git(['add', 'README.md']);
  const second = await f.publisher.publish(publication);
  assert.equal(second.existingPrMetadataPreserved, true);
  assert.ok(f.state.requests.some((request) => request.method === 'PATCH' && request.body.force === false));
  assert.equal(f.state.requests.filter((request) => request.method === 'POST'
    && request.endpoint.endsWith('/pulls')).length, 1);
});

test('PR creation failure reports preserved branch and retry creates one PR without another commit', async (t) => {
  const f = await fixture(t);
  f.state.intercept = ({ method, endpoint }) => {
    if (method === 'POST' && endpoint.endsWith('/pulls')) throw new Error('private failure body');
    return undefined;
  };
  await assert.rejects(f.publisher.publish(publication), (error) =>
    code('PR_FAILED')(error) && error.details.branchPublished === true
    && error.details.commit === f.state.branch && !error.message.includes('private'));
  assert.equal(await f.text(['rev-parse', 'HEAD']), f.state.branch);
  f.state.intercept = undefined;
  const resumed = await f.publisher.publish(publication);
  assert.equal(resumed.url, 'https://github.com/Eneru/soulkiller/pull/17');
  assert.equal(f.state.requests.filter((request) => request.endpoint.endsWith('/git/commits')).length, 1);
  assert.equal(f.state.pulls.length, 1);
});

test('ambiguous/external PR ownership is refused and review-request failure is reported without hiding a valid PR', async (t) => {
  const f = await fixture(t);
  f.state.intercept = ({ method, endpoint }) => {
    if (method === 'POST' && endpoint.endsWith('/requested_reviewers')) throw new Error('private denied body');
    return undefined;
  };
  const result = await f.publisher.publish(publication);
  assert.equal(result.reviewRequested, false);
  assert.equal(result.mode, 'published');
  f.state.intercept = undefined;
  f.state.pulls[0].user.login = 'Eneru';
  await assert.rejects(f.publisher.publish(publication), code('PR_FAILED'));
});

test('no staged publication at main base and invalid PR number are rejected', async (t) => {
  const f = await fixture(t, { stage: false });
  await assert.rejects(f.publisher.publish(publication), code('NOTHING_STAGED'));
  await assert.rejects(f.publisher.verify({ number: 0 }), code('BAD_ARGUMENT'));
});
