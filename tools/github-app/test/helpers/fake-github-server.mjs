import assert from 'node:assert/strict';
import path from 'node:path';
import { CONFIG } from '../../constants.mjs';
import { bot, scope } from './synthetic-data.mjs';

export class FakeGitHubServer {
  constructor(repository) {
    this.repository = repository;
    this.base = repository.base;
    this.baseTree = repository.baseTree;
    this.branch = null;
    this.commits = new Map();
    this.pulls = [];
    this.requests = [];
    this.revoked = 0;
    this.intercept = undefined;
    this.commits.set(this.base, this.makeCommit(this.base, this.baseTree));
  }

  makeCommit(sha, tree, parent) {
    return ({
    sha, author: { login: bot }, committer: { login: 'web-flow' },
    commit: { tree: { sha: tree }, committer: { name: 'GitHub', email: 'noreply@github.com' },
      verification: { verified: true, reason: 'valid' } },
    parents: parent ? [{ sha: parent }] : [],
    });
  }

  async request(method, endpoint, auth, body) {
    const state = this;
    const { git, text } = this.repository;
    const root = this.repository.root;
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
        state.commits.set(sha, this.makeCommit(sha, body.tree, body.parents[0]));
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
          number: 17, user: { login: bot }, state: 'open', draft: body.draft, title: body.title, body: body.body,
          base: { ref: body.base, repo: { full_name: 'Eneru/soulkiller' } },
          head: { ref: body.head, repo: { full_name: 'Eneru/soulkiller' }, sha: state.branch },
          html_url: 'https://github.com/Eneru/soulkiller/pull/17',
        };
        state.pulls.push(pr);
        return pr;
      }
      if (method === 'PATCH' && /\/pulls\/\d+$/u.test(endpoint)) {
        const pr = state.pulls.find((entry) => endpoint.endsWith('/' + entry.number));
        assert.ok(pr);
        Object.assign(pr, body);
        return pr;
      }
      if (method === 'GET' && /\/pulls\/\d+$/u.test(endpoint)) {
        const pr = state.pulls.find((entry) => endpoint.endsWith('/' + entry.number));
        return pr ? { ...pr, head: { ...pr.head, sha: state.branch } } : null;
      }
      if (method === 'POST' && endpoint.endsWith('/requested_reviewers')) return {};
      throw new Error('Unexpected offline API request');
  }
}
