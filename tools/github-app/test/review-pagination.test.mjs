import test from 'node:test';
import assert from 'node:assert/strict';
import { PublicationError } from '../errors.mjs';
import { BOT } from '../constants.mjs';
import { comment, replyId, text, options, reviewComment, createReviewReplyFixture, errorCode, assertNoReply }
  from './helpers/review-reply-fixture.mjs';

test('retry discovers an exact bot reply on a later page and performs no new write', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  f.state.intercept = ({ endpoint }) => {
    if (endpoint.endsWith('&page=1')) return Array.from({ length: 100 }, (_, index) => reviewComment(index + 1));
    if (endpoint.endsWith('&page=2')) return [f.reply];
  };
  // Act
  const result = await f.service.reply(options);
  // Assert
  assert.equal(result.mode, 'existing-reply');
  assert.equal(result.existing, true);
  assert.equal(result.replyId, replyId);
  assertNoReply(f.state);
  assert.equal(f.state.revoked, 1);
});

test('a reply by another user, for another target or with different body does not suppress the requested reply', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  f.state.entries = [
    reviewComment(201, { user: { login: 'Eneru' }, in_reply_to_id: comment, body: text }),
    reviewComment(202, { user: { login: BOT }, in_reply_to_id: comment + 1, body: text }),
    reviewComment(203, { user: { login: BOT }, in_reply_to_id: comment, body: 'Different reply' }),
  ];
  // Act
  const result = await f.service.reply(options);
  // Assert
  assert.equal(result.mode, 'replied');
  assert.equal(f.state.requests.filter((request) => request.method === 'POST').length, 1);
});

for (const malformed of ['duplicates', 'repeated-page', 'not-array', 'oversized', 'foreign-pr', 'limit']) {
  test('ambiguous or incomplete pagination refuses to create duplicate replies: ' + malformed, async () => {
    // Arrange
    const f = createReviewReplyFixture();
    if (malformed === 'duplicates') f.state.entries = [f.reply, reviewComment(replyId + 1,
      { user: { login: BOT }, in_reply_to_id: comment, body: text })];
    if (malformed === 'not-array') f.state.entries = {};
    if (malformed === 'oversized') f.state.entries = Array.from({ length: 101 }, (_, index) => reviewComment(index + 1));
    if (malformed === 'foreign-pr') f.state.entries = [reviewComment(1, { pull_request_url: 'https://example.invalid/pr' })];
    if (malformed === 'repeated-page' || malformed === 'limit') {
      f.state.intercept = ({ endpoint }) => {
        if (!endpoint.includes('/comments?')) return undefined;
        const page = Number(endpoint.split('&page=')[1]);
        return Array.from({ length: 100 }, (_, index) => reviewComment(index + 1
          + (malformed === 'limit' ? page * 100 : 0)));
      };
    }
    // Act
    await assert.rejects(f.service.reply(options), (error) => error instanceof PublicationError);
    // Assert
    assertNoReply(f.state);
    assert.equal(f.state.revoked, 1);
  });
}

for (const mismatch of ['author', 'parent', 'body', 'location', 'persisted', 'persisted-id']) {
  test('posted response and persisted reply must retain exact bot body and thread: ' + mismatch, async () => {
    // Arrange
    const f = createReviewReplyFixture();
    if (mismatch === 'author') f.reply.user.login = 'Eneru';
    if (mismatch === 'parent') f.reply.in_reply_to_id = comment + 1;
    if (mismatch === 'body') f.reply.body = 'Unexpected body';
    if (mismatch === 'location') f.reply.html_url = 'https://example.invalid/comment';
    if (mismatch === 'persisted') f.state.intercept = ({ method, endpoint }) =>
      method === 'GET' && endpoint.endsWith('/comments/' + replyId) ? { ...f.reply, body: 'Edited' } : undefined;
    if (mismatch === 'persisted-id') f.state.intercept = ({ method, endpoint }) =>
      method === 'GET' && endpoint.endsWith('/comments/' + replyId)
        ? reviewComment(replyId + 1, { user: { login: BOT }, in_reply_to_id: comment, body: text }) : undefined;
    // Act
    await assert.rejects(f.service.reply(options), (error) => error instanceof PublicationError);
    // Assert
    assert.equal(f.state.requests.filter((request) => request.method === 'POST').length, 1);
    assert.equal(f.state.revoked, 1);
  });
}

test('ambiguous network failure does not auto-retry a possibly accepted POST', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  f.state.intercept = ({ method }) => {
    if (method === 'POST') throw new PublicationError('API_FAILED');
  };
  // Act
  await assert.rejects(f.service.reply(options), errorCode('API_FAILED'));
  // Assert
  assert.equal(f.state.requests.filter((request) => request.method === 'POST').length, 1);
  assert.equal(f.state.revoked, 1);
});


test('an existing matching reply edited after enumeration is not reported as a successful retry', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  f.state.entries = [f.reply];
  f.state.intercept = ({ method, endpoint }) => method === 'GET'
    && endpoint.endsWith('/comments/' + replyId) ? { ...f.reply, body: 'Edited since enumeration' } : undefined;
  // Act
  await assert.rejects(f.service.reply(options), errorCode('REPLY_FAILED'));
  // Assert
  assertNoReply(f.state);
  assert.equal(f.state.revoked, 1);
});
