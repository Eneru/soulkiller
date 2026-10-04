import test from 'node:test';
import assert from 'node:assert/strict';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

for (const scenario of ['blob', 'tree', 'signature', 'identity']) {
  test("blob/tree mismatch and unverified/wrong-identity commit do not publish a ref: " + scenario, async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    f.api.intercept = async ({ method, endpoint, body }) => {
      if (scenario === 'blob' && endpoint.endsWith('/git/blobs')) return { sha: 'a'.repeat(40) };
      if (scenario === 'tree' && endpoint.endsWith('/git/trees')) return { sha: 'a'.repeat(40) };
      if (scenario === 'signature' && endpoint.endsWith('/git/commits')) {
        return { sha: 'a'.repeat(40), tree: { sha: body.tree }, parents: [{ sha: body.parents[0] }],
          verification: { verified: false, reason: 'unsigned' } };
      }
      if (scenario === 'identity' && method === 'GET' && endpoint.includes('/commits/')
        && !endpoint.endsWith(f.api.base)) {
        const saved = f.api.commits.get(endpoint.split('/commits/')[1]);
        return { ...saved, author: { login: 'Eneru' } };
      }
      return undefined;
    };
    // Act
    const attempt = f.publisher.publish(publication);
    // Assert
    await assert.rejects(attempt, (error) => {
      assert.equal(code(['blob', 'tree'].includes(scenario) ? 'TREE_MISMATCH' : 'COMMIT_UNVERIFIED')(error), true);
      if (['signature', 'identity'].includes(scenario)) assert.match(error.details.commit, /^[a-f0-9]{40}$/u);
      assert.deepEqual(Object.keys(error.details), ['signature', 'identity'].includes(scenario) ? ['commit'] : []);
      return true;
    });
    assert.equal(f.api.branch, null);
    assert.equal(f.api.revoked, 1);
    assert.equal(await f.text(['rev-parse', 'HEAD']), f.api.base);
  });
}
