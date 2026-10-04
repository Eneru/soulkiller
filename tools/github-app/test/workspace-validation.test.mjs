import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fixtureWriteFile, fixtureSymlink } from './helpers/filesystem.mjs';
import { code } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

const invalidWorkspaces = [
  {name: 'untracked source', expected: 'WORKSPACE_DIRTY', arrange: async (f) => {
    await fixtureWriteFile(path.join(f.root, 'untracked.txt'), 'untracked');
  }},
  {name: 'unstaged tracked change', expected: 'WORKSPACE_DIRTY', arrange: async (f) => {
    await fixtureWriteFile(path.join(f.root, 'README.md'), 'unstaged');
  }},
  {name: 'LICENSE modification', expected: 'LICENSE_CHANGED', arrange: async (f) => {
    await fixtureWriteFile(path.join(f.root, 'LICENSE'), 'Changed');
    await f.git(['add', 'LICENSE']);
  }},
  {name: 'secret file in the index', expected: 'BAD_PATH', arrange: async (f) => {
    await fixtureWriteFile(path.join(f.root, '.env'), 'synthetic local env');
    await f.git(['add', '.env']);
  }},
  {name: 'indexed symlink', expected: 'WORKSPACE_DIRTY', arrange: async (f) => {
    await fixtureSymlink('README.md', path.join(f.root, 'link.md'));
    await f.git(['add', 'link.md']);
  }},
  {name: 'protected main branch', expected: 'BAD_BRANCH', stage: false, arrange: async (f) => {
    await f.git(['switch', 'main']);
  }},
  {name: 'incorrect origin', expected: 'REPOSITORY_MISMATCH', arrange: async (f) => {
    await f.git(['remote', 'set-url', 'origin', 'https://github.com/Other/repo.git']);
  }},
];
for (const {name, expected, arrange, stage = true} of invalidWorkspaces) {
  test('snapshot rejects ' + name + ' without authentication', async (t) => {
    // Arrange
    const f = await createPublicationFixture(t, {stage});
    await arrange(f);
    // Act
    const attempt = f.workspace.snapshot();
    // Assert
    await assert.rejects(attempt, code(expected));
    assert.equal(f.api.requests.length, 0);
  });
}
