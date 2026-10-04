import test from 'node:test';
import assert from 'node:assert/strict';
import { bot, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('completed publication creates a ready independent PR and requests the maintainer review', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  const before = await f.workspace.snapshot();
  // Act
  const result = await f.publisher.publish(publication);
  // Assert
  assert.equal(result.mode, 'published');
  assert.equal(result.verified, true);
  const inspected = f.api.commits.get(result.commit);
  assert.equal(inspected.author.login, bot);
  assert.equal(inspected.committer.login, 'web-flow');
  assert.deepEqual(inspected.commit.committer, { name: 'GitHub', email: 'noreply@github.com' });
  assert.equal(result.reviewRequested, true);
  assert.equal(result.url, 'https://github.com/Eneru/soulkiller/pull/17');
  assert.equal(f.api.revoked, 1);
  const pr = f.api.requests.find((request) => request.method === 'POST' && request.endpoint.endsWith('/pulls')).body;
  assert.equal(pr.draft, false);
  assert.equal(pr.base, 'main');
  assert.equal(pr.head, before.branch);

});

test('authenticated verification confirms the published bot PR and revokes its read token', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  // Act
  const checked = await f.publisher.verify({execute: true, number: 17});
  // Assert
  assert.equal(checked.verified, true);
  assert.equal(checked.tokenRevoked, true);
});
