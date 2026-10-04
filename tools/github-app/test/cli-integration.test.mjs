import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { CONFIG } from '../constants.mjs';
import { fixtureRm } from './helpers/filesystem.mjs';
import { publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

import { main } from '../cli.mjs';
import { captureCliOutput } from './helpers/cli-output.mjs';

for (const [command, args] of [
  ['check', ['check']],
  ['publish', ['publish', '--title', publication.title, '--body-file', publication.bodyFile]],
  ['verify', ['verify', '--number', '17']],
]) {
  test('CLI ' + command + ' uses shared isolated fixtures for offline execution without a key', async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    const captured = captureCliOutput();
    await fixtureRm(path.join(f.root, CONFIG.keyFile));
    // Act
    const status = await main(args, {...captured.io, publisher: f.publisher});
    // Assert
    assert.equal(status, 0);
    assert.equal(JSON.parse(captured.outputs.at(0)).mode, 'dry-run');
    assert.equal(f.api.requests.length, 0);
    assert.equal(captured.errors.length, 0);
  });
}
