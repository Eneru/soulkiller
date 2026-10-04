import assert from 'node:assert/strict';
import { BOT, REPOSITORY } from '../../constants.mjs';
import { PublicationError } from '../../errors.mjs';
import { ReviewReplyService } from '../../review-replies.mjs';

export const number = 10;
export const comment = 4176900402;
export const replyId = 4177000001;
export const head = 'a'.repeat(40);
export const tree = 'b'.repeat(40);
export const bodyFile = '.soulkiller-local/review-reply.md';
export const text = 'Fixed in the verified follow-up commit. Tests pass.';
export const options = { number, comment, bodyFile, execute: true };

export function reviewComment(id, overrides = {}) {
  return {
    id, user: { login: 'Eneru' },
    url: 'https://api.github.com/repos/' + REPOSITORY + '/pulls/comments/' + id,
    html_url: 'https://github.com/' + REPOSITORY + '/pull/' + number + '#discussion_r' + id,
    pull_request_url: 'https://api.github.com/repos/' + REPOSITORY + '/pulls/' + number,
    body: 'Please clarify this behavior.', ...overrides,
  };
}

export function createReviewReplyFixture() {
  const state = { requests: [], minted: 0, revoked: 0, scans: [], snapshots: 0, bodyAssertions: 0 };
  const snapshot = { branch: 'codex/7-quality-and-documentation-plan', head, tree, changes: [] };
  const capturedBody = { file: bodyFile, text };
  const pr = {
    number, user: { login: BOT }, state: 'open', draft: false,
    base: { ref: 'main', repo: { full_name: REPOSITORY } },
    head: { ref: snapshot.branch, sha: head, repo: { full_name: REPOSITORY } },
    html_url: 'https://github.com/' + REPOSITORY + '/pull/' + number,
  };
  const commit = {
    sha: head, author: { login: BOT }, committer: { login: 'web-flow' },
    commit: { tree: { sha: tree }, committer: { name: 'GitHub', email: 'noreply@github.com' },
      verification: { verified: true, reason: 'valid' } },
  };
  const target = reviewComment(comment);
  const reply = reviewComment(replyId, { user: { login: BOT }, in_reply_to_id: comment, body: text });
  const publisher = {
    files: {
      async readBody(file) {
        assert.equal(file, bodyFile);
        if (state.bodyError) throw state.bodyError;
        return capturedBody;
      },
      async assertBody(body) {
        assert.equal(body, capturedBody);
        state.bodyAssertions += 1;
        if (state.bodyChanged) throw new PublicationError('INDEX_CHANGED');
      },
    },
    workspace: {
      async snapshot() { return snapshot; },
      async assertSnapshot(value) {
        assert.equal(value, snapshot);
        state.snapshots += 1;
        if (state.snapshotChanged) throw new PublicationError('INDEX_CHANGED');
      },
    },
    gates: {
      async preflight(body, title, message, value) {
        state.scans.push({ body, title, message, snapshot: value });
        if (state.scannerError) throw state.scannerError;
      },
    },
    auth: {
      async withInstallation(permissions, keyFile, operation) {
        state.permissions = permissions;
        state.keyFile = keyFile;
        state.minted += 1;
        try { return { ...await operation('synthetic-transport-token'), tokenRevoked: true }; }
        finally { state.revoked += 1; }
      },
    },
    client: {
      async request(method, endpoint, token, body) {
        assert.equal(token, 'synthetic-transport-token');
        const request = { method, endpoint, body };
        state.requests.push(request);
        const intercepted = state.intercept?.(request);
        if (intercepted !== undefined) return intercepted;
        if (endpoint === '/repos/' + REPOSITORY + '/pulls/' + number) return pr;
        if (endpoint === '/repos/' + REPOSITORY + '/commits/' + head) return commit;
        if (endpoint === '/repos/' + REPOSITORY + '/pulls/comments/' + comment) return target;
        if (endpoint === '/repos/' + REPOSITORY + '/pulls/comments/' + replyId) return reply;
        if (endpoint.includes('/comments?')) return state.entries || [];
        if (method === 'POST' && endpoint.endsWith('/replies')) return reply;
        throw new Error('Unexpected synthetic API endpoint');
      },
    },
  };
  const service = new ReviewReplyService(publisher);
  return { service, publisher, state, snapshot, capturedBody, pr, commit, target, reply };
}

export function errorCode(code) {
  return (error) => error instanceof PublicationError && error.code === code;
}

export function assertNoReply(state) {
  assert.equal(state.requests.some((request) => request.method === 'POST'), false);
}
