import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fixtureReadFile } from './helpers/filesystem.mjs';
import { token, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('publication advances local HEAD while preserving the staged tree and clearing only its committed diff', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  const before = await f.workspace.snapshot();
  // Act
  const result = await f.publisher.publish(publication);
  // Assert
  assert.equal(await f.text(['rev-parse', 'HEAD']), result.commit);
  assert.equal(await f.text(['write-tree']), before.tree);
  assert.equal(await f.text(['diff', '--cached', '--name-only']), '');
  assert.deepEqual(await fixtureReadFile(path.join(f.root, 'binary.bin')), Buffer.from([0, 255, 128, 13, 10, 0, 65]));
});

test('publication fetch authenticates through environment headers without credentials in arguments', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  // Act
  await f.publisher.publish(publication);
  // Assert
  const fetchCall = f.calls.find((call) => call.file === 'git' && call.args.includes('fetch'));
  assert.equal(fetchCall.options.env.GIT_CONFIG_VALUE_0, '');
  assert.ok(fetchCall.options.env.GIT_CONFIG_VALUE_1.startsWith('AUTHORIZATION: basic '));
  assert.equal(fetchCall.args.some((arg) => arg.includes(token)), false);

});
