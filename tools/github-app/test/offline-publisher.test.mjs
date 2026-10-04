import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import os from 'node:os';
import { CONFIG } from '../constants.mjs';
import { fixtureRm } from './helpers/filesystem.mjs';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('dry run performs fixed local gates without key reads or any API request', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  await fixtureRm(path.join(f.root, '.soulkiller-local/github-app/private-key.pem'));
  // Act
  const result = await f.publisher.publish({ ...publication, execute: false });
  // Assert
  assert.equal(result.mode, 'dry-run');
  assert.equal(result.changedFiles, 4);
  assert.equal(f.api.requests.length, 0);
  const scan = f.calls.find((call) => call.file === 'bash');
  assert.deepEqual(scan.args, ['tools/checks/check.sh', 'secrets-publication', '--body-file',
    path.join(f.root, '.soulkiller-local/pr.md'), '--metadata-stdin']);
  assert.equal(scan.options.input, publication.title + '\n' + publication.title + '\n'
    + 'Synthetic review body\n\nRefs #7\n\n');
  assert.ok(scan.options.env.GIT_INDEX_FILE.startsWith(path.join(os.tmpdir(), 'soulkiller-publish-index-')));
  assert.ok(f.calls.some((call) => call.file === 'openspec'
    && call.args.join(' ') === 'validate --all --strict --no-interactive'));
  assert.ok(f.calls.some((call) => call.args.join(' ').endsWith('diff --cached --check')));
});


for (const command of ['check', 'verify']) {
  test(command + ' defaults to an offline dry run without a private key', async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    await fixtureRm(path.join(f.root, CONFIG.keyFile));
    // Act
    const result = command === 'check' ? await f.publisher.check() : await f.publisher.verify({number: 17});
    // Assert
    assert.equal(result.mode, 'dry-run');
    assert.equal(f.api.requests.length, 0);
  });
}

test('publication at the main base rejects an empty staged change', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t, {stage: false});
  // Act
  const attempt = f.publisher.publish(publication);
  // Assert
  await assert.rejects(attempt, code('NOTHING_STAGED'));
});

test('PR verification rejects an invalid number before authentication', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  // Act
  const attempt = f.publisher.verify({number: 0});
  // Assert
  await assert.rejects(attempt, code('BAD_ARGUMENT'));
  assert.equal(f.api.requests.length, 0);
});
