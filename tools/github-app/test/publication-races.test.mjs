import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fixtureWriteFile } from './helpers/filesystem.mjs';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

for (const scenario of ['index', 'body', 'branch']) {
  test("changing index/body or advancing remote head before ref publication refuses without overwrite: " + scenario, async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    f.api.intercept = async ({ method, endpoint }) => {
      if (method === 'GET' && endpoint.includes('/commits/') && !endpoint.endsWith(f.api.base)) {
        if (scenario === 'index') {
          await fixtureWriteFile(path.join(f.root, 'README.md'), 'concurrently staged change');
          await f.git(['add', 'README.md']);
        } else if (scenario === 'body') {
          await fixtureWriteFile(path.join(f.root, '.soulkiller-local/pr.md'), 'concurrent body');
        } else {
          f.api.branch = 'a'.repeat(40);
        }
      }
      return undefined;
    };
    // Act
    const attempt = f.publisher.publish(publication);
    // Assert
    await assert.rejects(attempt, code(scenario === 'branch' ? 'REF_RACE' : 'INDEX_CHANGED'));
    assert.equal(f.api.requests.some((request) => request.method === 'POST'
      && request.endpoint.endsWith('/git/refs')), false);
    assert.equal(await f.text(['rev-parse', 'HEAD']), f.api.base);
  });
}
