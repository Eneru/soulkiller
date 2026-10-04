import test from 'node:test';
import assert from 'node:assert/strict';
import { fixtureWriteFile } from './helpers/filesystem.mjs';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('the immutable captured PR body reaches secret scanning even if its file is swapped temporarily', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  const body = await f.files.readBody(publication.bodyFile);
  const snapshot = await f.workspace.snapshot();
  let scanned = false;
  f.publisher.command = async (file, args, options) => {
    if (file === 'bash') {
      await fixtureWriteFile(body.file, 'Different mutable synthetic body');
      assert.ok(options.input.includes(body.text));
      scanned = true;
      await fixtureWriteFile(body.file, body.bytes);
    }
    return f.command(file, args, options);
  };
  // Act
  await f.gates.preflight(body, publication.title, publication.title, snapshot);
  await f.publisher.assertSnapshot(snapshot, body);
  // Assert
  assert.equal(scanned, true);
});

test('preflight failure blocks authentication and does not echo scanner output', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  f.publisher.command = async (file, args, options) => {
    if (file === 'bash') throw new Error('secret scanner output');
    return f.command(file, args, options);
  };
  // Act
  const attempt = f.publisher.publish(publication);
  // Assert
  await assert.rejects(attempt, (error) =>
    code('PREFLIGHT_FAILED')(error) && !error.message.includes('secret scanner output'));
  assert.equal(f.api.requests.length, 0);
});
