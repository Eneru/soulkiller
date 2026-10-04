import test from 'node:test';
import assert from 'node:assert/strict';
import { PublicationError } from '../errors.mjs';
import { runCommand } from '../command.mjs';
import { ReviewReplyService } from '../review-replies.mjs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';
import { fixtureWriteFile } from './helpers/filesystem.mjs';
import { options, createReviewReplyFixture, errorCode, assertNoReply } from './helpers/review-reply-fixture.mjs';

test('offline reply scans captured bytes without authentication or transport calls', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  // Act
  const result = await f.service.reply({ ...options, execute: false });
  // Assert
  assert.equal(result.mode, 'dry-run');
  assert.equal(result.remoteChecks, 'not-run');
  assert.equal(f.state.minted, 0);
  assert.deepEqual(f.state.requests, []);
  assert.equal(f.state.scans[0].body, f.capturedBody);
  assert.equal(f.state.scans[0].snapshot, f.snapshot);
});


for (const invalid of [0, -1, 1.2, '10', Number.MAX_SAFE_INTEGER + 1]) {
  test('invalid numeric reply identifier fails before body or authentication: ' + String(invalid), async () => {
    // Arrange
    const f = createReviewReplyFixture();
    // Act
    await assert.rejects(f.service.reply({ ...options, comment: invalid }), errorCode('BAD_ARGUMENT'));
    // Assert
    assert.equal(f.state.minted, 0);
    assertNoReply(f.state);
  });
}

test('confined body rejection and whitespace-only bodies fail before authentication', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  f.state.bodyError = new PublicationError('BODY_INVALID');
  // Act
  await assert.rejects(f.service.reply(options), errorCode('BODY_INVALID'));
  // Assert
  assert.equal(f.state.minted, 0);
  assertNoReply(f.state);
});

test('whitespace-only body is not sent', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  f.capturedBody.text = ' \n ';
  // Act
  await assert.rejects(f.service.reply(options), errorCode('BODY_INVALID'));
  // Assert
  assert.equal(f.state.minted, 0);
});

test('unpublished staged changes cannot receive a reply claiming their delivery', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  f.snapshot.changes.push('pending.md');
  // Act
  await assert.rejects(f.service.reply(options), errorCode('WORKSPACE_DIRTY'));
  // Assert
  assert.equal(f.state.minted, 0);
  assertNoReply(f.state);
});

test('secret-scanner refusal blocks authentication and withholds synthetic sensitive output', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  f.capturedBody.text = 'SYNTHETIC_SECRET_SCANNER_INPUT';
  f.state.scannerError = new PublicationError('PREFLIGHT_FAILED');
  // Act
  await assert.rejects(f.service.reply(options), (error) => {
    assert.equal(errorCode('PREFLIGHT_FAILED')(error), true);
    return !error.message.includes(f.capturedBody.text);
  });
  // Assert
  assert.equal(f.state.minted, 0);
  assertNoReply(f.state);
});


test('real Gitleaks rejects a synthetic installation token in the ignored reply body before auth', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t, { stage: false });
  const secret = 'ghs_' + '5174172_' + [
    'eyJhbGciOiJIUzI1NiJ9', 'eyJzdWIiOiJzeW50aGV0aWMifQ', 'a'.repeat(32),
  ].join('.');
  await fixtureWriteFile(path.join(f.root, '.soulkiller-local/pr.md'), secret);
  const scanner = fileURLToPath(new URL('../../checks/check.sh', import.meta.url));
  f.publisher.command = (file, args, passed) => file === 'bash'
    ? runCommand('bash', [scanner, ...args.slice(1)], passed) : f.command(file, args, passed);
  const service = new ReviewReplyService(f.publisher);
  // Act
  await assert.rejects(service.reply({ ...options, bodyFile: '.soulkiller-local/pr.md' }),
    errorCode('PREFLIGHT_FAILED'));
  // Assert
  assert.deepEqual(f.api.requests, []);
});


test('real confined body reader rejects malformed UTF-8 before scanner or authentication', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t, { stage: false });
  await fixtureWriteFile(path.join(f.root, '.soulkiller-local/pr.md'), Buffer.from([0xc3, 0x28]));
  const service = new ReviewReplyService(f.publisher);
  // Act
  await assert.rejects(service.reply({ ...options, bodyFile: '.soulkiller-local/pr.md' }),
    errorCode('BODY_INVALID'));
  // Assert
  assert.deepEqual(f.api.requests, []);
  assert.equal(f.calls.some((call) => call.file === 'bash'), false);
});


test('a truthy nonboolean execution value cannot accidentally authenticate', async () => {
  // Arrange
  const f = createReviewReplyFixture();
  // Act
  await assert.rejects(f.service.reply({ ...options, execute: 'false' }), errorCode('BAD_ARGUMENT'));
  // Assert
  assert.equal(f.state.minted, 0);
  assertNoReply(f.state);
});
