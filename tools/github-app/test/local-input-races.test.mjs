import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { CONFIG } from '../constants.mjs';
import { fixtureSymlink, fixtureRename, fixtureRm } from './helpers/filesystem.mjs';
import { code } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

for (const category of ['body', 'key']) {
  test("descriptor reads reject leaf replacement during ignored-path Git checks: " + category, async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    const relative = category === 'body' ? '.soulkiller-local/pr.md' : CONFIG.keyFile;
    let swapped = false;
    f.publisher.command = async (file, args, options) => {
      const result = await f.command(file, args, options);
      if (!swapped && file === 'git' && args.includes('ls-files') && args.includes(relative)) {
        swapped = true;
        await fixtureRm(path.join(f.root, relative));
        await fixtureSymlink(path.join(f.root, 'README.md'), path.join(f.root, relative));
      }
      return result;
    };
    // Act
    const attempt = f.files.readLocal(relative, category);
    // Assert
    await assert.rejects(attempt,
      code(category === 'body' ? 'BODY_INVALID' : 'KEY_INVALID'));
    assert.equal(swapped, true);
    assert.equal(f.api.requests.length, 0);
  });
}

for (const category of ['body', 'key']) {
  test("descriptor reads reject ancestor replacement after path validation: " + category, async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    const relative = category === 'body' ? '.soulkiller-local/pr.md' : CONFIG.keyFile;
    const directory = path.join(f.root, category === 'body' ? '.soulkiller-local' : '.soulkiller-local/github-app');
    const archive = path.join(f.root, category === 'body' ? 'local-archive' : '.soulkiller-local/key-archive');
    let swapped = false;
    f.publisher.command = async (file, args, options) => {
      const result = await f.command(file, args, options);
      if (!swapped && file === 'git' && args.includes('ls-files') && args.includes(relative)) {
        swapped = true;
        await fixtureRename(directory, archive);
        await fixtureSymlink(archive, directory);
      }
      return result;
    };
    // Act
    const attempt = f.files.readLocal(relative, category);
    // Assert
    await assert.rejects(attempt,
      code(category === 'body' ? 'BODY_INVALID' : 'KEY_INVALID'));
    assert.equal(swapped, true);
    assert.equal(f.api.requests.length, 0);
  });
}
