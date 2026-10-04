import test from 'node:test';
import assert from 'node:assert/strict';
import { code, publication } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

const staleParents = [
  {name: 'remote main has advanced', arrange: async (f) => { f.api.base = 'a'.repeat(40); }, expected: 'STALE_PARENT'},
  {name: 'remote branch differs from the local parent', arrange: async (f) => { f.api.branch = 'b'.repeat(40); }, expected: 'STALE_PARENT'},
  {name: 'repository identity differs', arrange: async (f) => {
    f.api.intercept = ({endpoint}) => endpoint === '/repos/Eneru/soulkiller' ? {full_name: 'Other/repo', default_branch: 'main'} : undefined;
  }, expected: 'REPOSITORY_MISMATCH'},
  {name: 'prior branch commit has an untrusted author', arrange: async (f) => {
    await f.git(['commit', '-m', 'Unverified local commit']);
    const snapshot = await f.workspace.snapshot();
    f.api.branch = snapshot.head;
    f.api.commits.set(snapshot.head, {...f.api.makeCommit(snapshot.head, snapshot.tree, snapshot.base), author: {login: 'Eneru'}});
  }, expected: 'COMMIT_UNVERIFIED'},
];
for (const {name, arrange, expected} of staleParents) {
  test('publication refuses when ' + name, async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    await arrange(f);
    // Act
    const attempt = f.publisher.publish(publication);
    // Assert
    await assert.rejects(attempt, code(expected));
    assert.equal(f.api.requests.some((request) => request.endpoint.endsWith('/git/refs')), false);
  });
}
