import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fixtureWriteFile, fixtureReadFile, fixtureMkdir } from './helpers/filesystem.mjs';
import { publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('publication uploads exact staged blobs, modes, deletion and parent without custom commit identities', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  const before = await f.workspace.snapshot();
  // Act
  await f.publisher.publish(publication);
  // Assert
  assert.deepEqual(await fixtureReadFile(path.join(f.root, 'binary.bin')), Buffer.from([0, 255, 128, 13, 10, 0, 65]));
  const blobs = f.api.requests.filter((request) => request.endpoint.endsWith('/git/blobs'));
  assert.ok(blobs.some((request) => Buffer.from(request.body.content, 'base64')
    .equals(Buffer.from([0, 255, 128, 13, 10, 0, 65]))));
  assert.ok(blobs.every((request) => request.body.encoding === 'base64'));
  const tree = f.api.requests.find((request) => request.endpoint.endsWith('/git/trees')).body;
  assert.equal(tree.base_tree, f.api.baseTree);
  assert.ok(tree.tree.some((entry) => entry.path === 'executable.sh' && entry.mode === '100755'));
  assert.ok(tree.tree.some((entry) => entry.path === 'remove.txt' && entry.sha === null));
  const commit = f.api.requests.find((request) => request.endpoint.endsWith('/git/commits')).body;
  assert.deepEqual(Object.keys(commit).sort(), ['message', 'parents', 'tree']);
  assert.deepEqual(commit.parents, [before.head]);

});

test('workflow write permission is requested only when staged workflow changes need it', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await fixtureMkdir(path.join(f.root, '.github/workflows'), { recursive: true });
  await fixtureWriteFile(path.join(f.root, '.github/workflows/check.yml'), 'name: synthetic\n');
  await f.git(['add', '.github/workflows/check.yml']);
  // Act
  await f.publisher.publish(publication);
  const mint = f.api.requests.find((request) => request.endpoint.endsWith('/access_tokens'));
  // Assert
  assert.deepEqual(mint.body.permissions, { contents: 'write', pull_requests: 'write', workflows: 'write' });
});
