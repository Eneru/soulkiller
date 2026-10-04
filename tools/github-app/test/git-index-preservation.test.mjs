import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fixtureReadFile, fixtureWriteFile } from './helpers/filesystem.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';
import { publication, token } from './helpers/synthetic-data.mjs';

test('fetching a verified tree preserves raw staged index bytes when live write-tree would refresh the cache', async (t) => {
  // Arrange: use real Git objects/ref updates; only the credential-free fetch transport is stubbed.
  const f = await createPublicationFixture(t);
  const index = path.join(f.root, '.git/index');
  await f.git(['write-tree']);
  await fixtureWriteFile(path.join(f.root, 'README.md'), 'New synthetic bytes invalidate the cached tree\n');
  await f.git(['add', 'README.md']);
  const originalIndex = await fixtureReadFile(index);
  await f.git(['write-tree']);
  assert.notDeepEqual(await fixtureReadFile(index), originalIndex);
  await fixtureWriteFile(index, originalIndex);
  const snapshot = await f.workspace.snapshot();
  const commit = await f.text(['commit-tree', snapshot.tree, '-p', snapshot.head], {
    input: 'Synthetic accepted remote commit',
  });

  // Act
  await f.workspace.fetchPublished(token, snapshot, commit);

  // Assert
  assert.deepEqual(await fixtureReadFile(index), originalIndex);
  assert.equal(await f.text(['rev-parse', 'HEAD']), commit);
  await f.workspace.assertPublishedSnapshot(snapshot, commit);
  assert.equal(f.api.requests.length, 0);
});

test('staged publication can refresh its existing PR immediately without a cache-populating retry', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.publisher.publish(publication);
  await f.git(['write-tree']);
  await fixtureWriteFile(path.join(f.root, 'README.md'), 'Second synthetic staged commit\n');
  await f.git(['add', 'README.md']);
  const originalIndex = await fixtureReadFile(path.join(f.root, '.git/index'));
  const title = 'Refresh the PR after a staged commit';
  const body = 'Synthetic metadata captured before the second publication';
  await fixtureWriteFile(path.join(f.root, '.soulkiller-local/pr.md'), body);

  // Act
  const result = await f.publisher.publish({...publication, title, updatePr: true});

  // Assert
  assert.equal(result.mode, 'published');
  assert.equal(result.changedFiles, 1);
  assert.equal(result.existingPrMetadataPreserved, false);
  assert.deepEqual(await fixtureReadFile(path.join(f.root, '.git/index')), originalIndex);
  assert.equal(await f.text(['rev-parse', 'HEAD']), result.commit);
  const updates = f.api.requests.filter((request) => request.method === 'PATCH'
    && request.endpoint.endsWith('/pulls/17'));
  assert.equal(updates.length, 1);
  assert.deepEqual(updates[0].body, {title, body});
  assert.equal(f.api.pulls[0].title, title);
  assert.equal(f.api.pulls[0].body, body);
});
