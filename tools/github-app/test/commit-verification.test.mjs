import test from 'node:test';
import assert from 'node:assert/strict';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

for (const scenario of ['login', 'name', 'email', 'missing', 'signature']) {
  test("verified App-author commits require the exact GitHub platform committer before any ref is published: " + scenario, async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    f.api.intercept = ({ method, endpoint }) => {
      if (method !== 'GET' || !endpoint.includes('/commits/') || endpoint.endsWith(f.api.base)) return undefined;
      const saved = f.api.commits.get(endpoint.split('/commits/')[1]);
      if (scenario === 'login') return { ...saved, committer: { login: 'Eneru' } };
      if (scenario === 'name') return { ...saved, commit: { ...saved.commit,
        committer: { ...saved.commit.committer, name: 'Unexpected signer' } } };
      if (scenario === 'email') return { ...saved, commit: { ...saved.commit,
        committer: { ...saved.commit.committer, email: 'other@example.invalid' } } };
      if (scenario === 'missing') return { ...saved, commit: { ...saved.commit, committer: undefined } };
      return { ...saved, commit: { ...saved.commit, verification: { verified: false, reason: 'unsigned' } } };
    };
    // Act
    const attempt = f.publisher.publish(publication);
    // Assert
    await assert.rejects(attempt, code('COMMIT_UNVERIFIED'));
    assert.equal(f.api.branch, null);
    assert.equal(f.api.requests.some((request) => request.method === 'POST'
      && request.endpoint.endsWith('/git/refs')), false);
    assert.equal(f.api.requests.some((request) => request.method === 'PATCH'
      && request.endpoint.includes('/git/refs/heads/')), false);
    assert.equal(await f.text(['rev-parse', 'HEAD']), f.api.base);
    assert.equal(f.api.revoked, 1);
  });
}
