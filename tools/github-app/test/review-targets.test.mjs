import test from 'node:test';
import assert from 'node:assert/strict';
import { PublicationError } from '../errors.mjs';
import { BOT, REPOSITORY } from '../constants.mjs';
import { comment, replyId, text, options, createReviewReplyFixture, errorCode, assertNoReply }
  from './helpers/review-reply-fixture.mjs';

test('reply validates its target and persisted bot identity with least token scope', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  // Act
  const result = await f.service.reply({ ...options, keyFile: '.soulkiller-local/github-app/synthetic.pem' });
  // Assert
  assert.equal(result.mode, 'replied');
  assert.equal(result.replyId, replyId);
  assert.equal(result.existing, false);
  assert.equal(result.tokenRevoked, true);
  assert.deepEqual(f.state.permissions, { contents: 'read', pull_requests: 'write' });
  assert.equal(f.state.revoked, 1);
  const writes = f.state.requests.filter((request) => request.method !== 'GET');
  assert.deepEqual(writes, [{
    method: 'POST', endpoint: '/repos/' + REPOSITORY + '/pulls/10/comments/' + comment + '/replies',
    body: { body: text },
  }]);
  assert.equal(f.state.requests.at(-1).endpoint, '/repos/' + REPOSITORY + '/pulls/comments/' + replyId);
  assert.equal(f.state.snapshots, 3);
});


for (const mismatch of ['number', 'author', 'draft', 'head', 'repository', 'tree', 'signature', 'committer']) {
  test('mismatched PR or verified head refuses replies: ' + mismatch, async () => {
    // Arrange
    const f = createReviewReplyFixture();
    if (mismatch === 'number') f.pr.number = 11;
    if (mismatch === 'author') f.pr.user.login = 'Eneru';
    if (mismatch === 'draft') f.pr.draft = true;
    if (mismatch === 'head') f.pr.head.sha = 'c'.repeat(40);
    if (mismatch === 'repository') f.pr.head.repo.full_name = 'Other/repository';
    if (mismatch === 'tree') f.commit.commit.tree.sha = 'c'.repeat(40);
    if (mismatch === 'signature') f.commit.commit.verification.verified = false;
    if (mismatch === 'committer') f.commit.committer.login = 'Eneru';
    // Act
    await assert.rejects(f.service.reply(options), (error) => error instanceof PublicationError);
    // Assert
    assertNoReply(f.state);
    assert.equal(f.state.revoked, 1);
  });
}


for (const mismatch of ['id', 'author', 'reply', 'foreign-pr', 'api-url', 'html-url', 'missing']) {
  test('target must be a top-level maintainer comment belonging to this PR: ' + mismatch, async () => {
    // Arrange
    const f = createReviewReplyFixture();
    if (mismatch === 'id') f.target.id = comment + 1;
    if (mismatch === 'author') f.target.user.login = BOT;
    if (mismatch === 'reply') f.target.in_reply_to_id = 123;
    if (mismatch === 'foreign-pr') f.target.pull_request_url += '1';
    if (mismatch === 'api-url') f.target.url = 'https://example.invalid/comment';
    if (mismatch === 'html-url') f.target.html_url = 'https://example.invalid/comment';
    if (mismatch === 'missing') f.state.intercept = ({ endpoint }) =>
      endpoint.endsWith('/comments/' + comment) ? null : undefined;
    // Act
    await assert.rejects(f.service.reply(options), errorCode('REVIEW_COMMENT_INVALID'));
    // Assert
    assertNoReply(f.state);
    assert.equal(f.state.revoked, 1);
  });
}


for (const changed of ['body', 'snapshot', 'pr', 'target']) {
  test('input and remote target are rechecked immediately before writing: ' + changed, async () => {
    // Arrange
    const f = createReviewReplyFixture();
    f.state.intercept = ({ endpoint }) => {
      if (endpoint.includes('/comments?')) {
        if (changed === 'body') f.state.bodyChanged = true;
        if (changed === 'snapshot') f.state.snapshotChanged = true;
        if (changed === 'pr') f.pr.head.sha = 'c'.repeat(40);
        if (changed === 'target') f.target.user.login = 'Other';
      }
    };
    // Act
    await assert.rejects(f.service.reply(options), (error) => error instanceof PublicationError);
    // Assert
    assertNoReply(f.state);
    assert.equal(f.state.revoked, 1);
  });
}
