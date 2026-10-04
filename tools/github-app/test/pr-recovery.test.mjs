import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fixtureWriteFile } from './helpers/filesystem.mjs';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('existing verified bot branch advances only with force=false and reuses its PR', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  await fixtureWriteFile(path.join(f.root, 'README.md'), 'Second staged change\n');
  await f.git(['add', 'README.md']);
  // Act
  const second = await f.publisher.publish(publication);
  // Assert
  assert.equal(second.existingPrMetadataPreserved, true);
  assert.ok(f.api.requests.some((request) => request.method === 'PATCH' && request.body.force === false));
  assert.equal(f.api.requests.filter((request) => request.method === 'POST'
    && request.endpoint.endsWith('/pulls')).length, 1);
});


const failPr = ({method, endpoint}) => { if (method === 'POST' && endpoint.endsWith('/pulls')) throw new Error('private failure body'); };
test('failed PR creation reports a preserved published branch without exposing the private response', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  f.api.intercept = failPr;
  // Act
  const attempt = f.publisher.publish(publication);
  // Assert
  await assert.rejects(attempt, (error) => code('PR_FAILED')(error) && error.details.branchPublished === true
    && error.details.commit === f.api.branch && !error.message.includes('private'));
  assert.equal(await f.text(['rev-parse', 'HEAD']), f.api.branch);
});

test('retry after failed PR creation reuses the published commit and creates one PR', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  f.api.intercept = failPr;
  await assert.rejects(f.publisher.publish(publication), code('PR_FAILED'));
  f.api.intercept = undefined;
  // Act
  const resumed = await f.publisher.publish(publication);
  // Assert
  assert.equal(resumed.url, 'https://github.com/Eneru/soulkiller/pull/17');
  assert.equal(f.api.requests.filter((request) => request.endpoint.endsWith('/git/commits')).length, 1);
  assert.equal(f.api.pulls.length, 1);
});

test('a denied review request does not hide an independently valid published PR', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  f.api.intercept = ({method, endpoint}) => { if (method === 'POST' && endpoint.endsWith('/requested_reviewers')) throw new Error('private denied body'); };
  // Act
  const result = await f.publisher.publish(publication);
  // Assert
  assert.equal(result.reviewRequested, false);
  assert.equal(result.mode, 'published');
});

test('an existing PR owned by another identity is refused', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  f.api.pulls[0].user.login = 'Eneru';
  // Act
  const attempt = f.publisher.publish(publication);
  // Assert
  await assert.rejects(attempt, code('PR_FAILED'));
});
