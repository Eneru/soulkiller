import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fixtureWriteFile, fixtureReadFile } from './helpers/filesystem.mjs';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('snapshot and uploads derive entries from frozen bytes despite a live-index ABA swap', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  const index = path.join(f.root, '.git/index');
  const original = await fixtureReadFile(index);
  const originalReadme = await fixtureReadFile(path.join(f.root, 'README.md'));
  await fixtureWriteFile(path.join(f.root, 'README.md'), 'UNSCANNED SYNTHETIC INDEX B');
  await f.git(['add', 'README.md']);
  const substituted = await fixtureReadFile(index);
  await fixtureWriteFile(path.join(f.root, 'README.md'), originalReadme);
  await fixtureWriteFile(index, original);
  let swapped = false;
  f.publisher.command = async (file, args, options) => {
    if (!swapped && file === 'git' && args.includes('--stage') && options.env?.GIT_INDEX_FILE) {
      swapped = true;
      await fixtureWriteFile(index, substituted);
      const result = await f.command(file, args, options);
      await fixtureWriteFile(index, original);
      return result;
    }
    return f.command(file, args, options);
  };
  // Act
  const result = await f.publisher.publish(publication);
  // Assert
  assert.equal(result.verified, true);
  assert.equal(swapped, true);
  const uploads = f.api.requests.filter((request) => request.endpoint.endsWith('/git/blobs'));
  assert.ok(uploads.some((request) => Buffer.from(request.body.content, 'base64').equals(originalReadme)));
  assert.equal(uploads.some((request) => Buffer.from(request.body.content, 'base64')
    .includes(Buffer.from('UNSCANNED SYNTHETIC INDEX B'))), false);
});

test('snapshot rejects a live index edit before any authentication or upload', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  let edited = false;
  f.publisher.command = async (file, args, options) => {
    const result = await f.command(file, args, options);
    if (!edited && file === 'git' && args.includes('--stage') && options.env?.GIT_INDEX_FILE) {
      edited = true;
      await fixtureWriteFile(path.join(f.root, 'README.md'), 'Concurrent synthetic index edit');
      await f.git(['add', 'README.md']);
    }
    return result;
  };
  // Act
  const attempt = f.publisher.publish(publication);
  // Assert
  await assert.rejects(attempt, code('INDEX_CHANGED'));
  assert.equal(f.api.requests.length, 0);
});
