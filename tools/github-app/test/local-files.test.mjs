import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { CONFIG } from '../constants.mjs';
import { fixtureWriteFile, fixtureSymlink } from './helpers/filesystem.mjs';
import { code } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('ignored App key resolves inside its allowed local directory', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  // Act
  const file = await f.files.localPath(CONFIG.keyFile, 'key');
  // Assert
  assert.equal(file, path.join(f.root, CONFIG.keyFile));
});

for (const [name, file] of [
  ['tracked repository file', 'LICENSE'], ['parent traversal', '../outside.pem'],
  ['body directory used as key', '.soulkiller-local/pr.md'], ['missing key', '.soulkiller-local/github-app/missing.pem'],
]) {
  test('App key confinement rejects ' + name, async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    // Act
    const attempt = f.files.localPath(file, 'key');
    // Assert
    await assert.rejects(attempt, code('KEY_INVALID'));
  });
}

test('App key confinement rejects a symlink pointing at a tracked file', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await fixtureSymlink(path.join(f.root, 'LICENSE'), path.join(f.root, '.soulkiller-local/github-app/escape.pem'));
  // Act
  const attempt = f.files.localPath('.soulkiller-local/github-app/escape.pem', 'key');
  // Assert
  await assert.rejects(attempt, code('KEY_INVALID'));
});

test('App key confinement rejects a forcibly tracked ignored key', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await f.git(['add', '-f', CONFIG.keyFile]);
  // Act
  const attempt = f.files.localPath(CONFIG.keyFile, 'key');
  // Assert
  await assert.rejects(attempt, code('KEY_INVALID'));
});

for (const [name, bytes] of [['malformed UTF-8', Buffer.from([255, 254])], ['empty body', Buffer.alloc(0)]]) {
  test('body reader rejects ' + name, async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    await fixtureWriteFile(path.join(f.root, '.soulkiller-local/bad.md'), bytes);
    // Act
    const attempt = f.files.readBody('.soulkiller-local/bad.md');
    // Assert
    await assert.rejects(attempt, code('BODY_INVALID'));
  });
}
