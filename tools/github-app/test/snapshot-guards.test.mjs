import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fixtureWriteFile } from './helpers/filesystem.mjs';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('snapshot guard detects changed captured body bytes', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  const snapshot = await f.workspace.snapshot();
  const body = await f.files.readBody(publication.bodyFile);
  await fixtureWriteFile(body.file, 'Edited ignored body');
  // Act
  const attempt = f.publisher.assertSnapshot(snapshot, body);
  // Assert
  await assert.rejects(attempt, code('INDEX_CHANGED'));
});

test('snapshot guard detects a newly staged tracked change', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  const snapshot = await f.workspace.snapshot();
  await fixtureWriteFile(path.join(f.root, 'README.md'), 'new staged document');
  await f.git(['add', 'README.md']);
  // Act
  const attempt = f.workspace.assertSnapshot(snapshot);
  // Assert
  await assert.rejects(attempt, code('INDEX_CHANGED'));
});

test('snapshot guard detects a different current branch', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  const snapshot = await f.workspace.snapshot();
  await f.git(['switch', '-c', 'codex/replacement']);
  // Act
  const attempt = f.workspace.assertSnapshot(snapshot);
  // Assert
  await assert.rejects(attempt, code('INDEX_CHANGED'));
});
