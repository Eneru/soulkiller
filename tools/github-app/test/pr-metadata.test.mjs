import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fixtureWriteFile } from './helpers/filesystem.mjs';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('default PR reuse preserves maintainer metadata without sending a metadata PATCH', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  f.api.pulls[0].title = 'Maintainer title';
  f.api.pulls[0].body = 'Maintainer body';
  await fixtureWriteFile(path.join(f.root, '.soulkiller-local/pr.md'), 'New requested body');
  // Act
  const result = await f.publisher.publish({...publication, title: 'New requested title'});
  // Assert
  assert.equal(result.existingPrMetadataPreserved, true);
  assert.equal(f.api.pulls[0].title, 'Maintainer title');
  assert.equal(f.api.pulls[0].body, 'Maintainer body');
  assert.equal(f.api.requests.some((request) => request.method === 'PATCH' && request.endpoint.endsWith('/pulls/17')), false);
});

test('explicit PR metadata update sends only captured scanned title and body on the verified current head', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  const title = 'Explicit updated title';
  const text = 'Explicit updated body';
  await fixtureWriteFile(path.join(f.root, '.soulkiller-local/pr.md'), text);
  // Act
  const result = await f.publisher.publish({...publication, title, updatePr: true});
  // Assert
  assert.equal(result.existingPrMetadataPreserved, false);
  const updates = f.api.requests.filter((request) => request.method === 'PATCH' && request.endpoint.endsWith('/pulls/17'));
  assert.equal(updates.length, 1);
  assert.deepEqual(updates.at(0).body, {title, body: text});
  assert.equal(f.api.pulls[0].title, title);
  assert.equal(f.api.pulls[0].body, text);
  assert.equal(f.api.branch, result.commit);
  const scan = f.calls.findLast((call) => call.file === 'bash');
  assert.ok(scan.options.input.includes(title + '\n'));
  assert.ok(scan.options.input.includes(text));
});

test('explicit metadata update cannot alter a PR owned by another identity', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  f.api.pulls[0].user.login = 'Eneru';
  // Act
  const attempt = f.publisher.publish({...publication, updatePr: true});
  // Assert
  await assert.rejects(attempt, code('PR_FAILED'));
  assert.equal(f.api.requests.some((request) => request.method === 'PATCH' && request.endpoint.endsWith('/pulls/17')), false);
});

test('metadata update refuses a stale PR head before any metadata PATCH', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  f.api.intercept = ({method, endpoint}) => method === 'GET' && endpoint.endsWith('/pulls/17')
    ? {...f.api.pulls[0], head: {...f.api.pulls[0].head, sha: 'a'.repeat(40)}} : undefined;
  // Act
  const attempt = f.publisher.publish({...publication, updatePr: true});
  // Assert
  await assert.rejects(attempt, code('PR_FAILED'));
  assert.equal(f.api.requests.some((request) => request.method === 'PATCH' && request.endpoint.endsWith('/pulls/17')), false);
});

test('metadata update rejects body replacement after scanning and before PATCH', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  f.api.intercept = async ({method, endpoint}) => {
    if (method === 'GET' && endpoint.endsWith('/pulls/17')) await fixtureWriteFile(path.join(f.root, '.soulkiller-local/pr.md'), 'Unscanned replacement body');
    return undefined;
  };
  // Act
  const attempt = f.publisher.publish({...publication, updatePr: true});
  // Assert
  await assert.rejects(attempt, code('PR_FAILED'));
  assert.equal(f.api.requests.some((request) => request.method === 'PATCH' && request.endpoint.endsWith('/pulls/17')), false);
});

test('metadata update reports a remote title/body mismatch after PATCH verification', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  f.api.intercept = ({method, endpoint}) => method === 'PATCH' && endpoint.endsWith('/pulls/17') ? {} : undefined;
  // Act
  const attempt = f.publisher.publish({...publication, title: 'Remote mismatch title', updatePr: true});
  // Assert
  await assert.rejects(attempt, code('PR_FAILED'));
  assert.equal(f.api.requests.filter((request) => request.method === 'PATCH' && request.endpoint.endsWith('/pulls/17')).length, 1);
});
