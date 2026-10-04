import path from 'node:path';
import { REPOSITORY, SHA, MAX_INDEX } from './constants.mjs';
import { ensure } from './guards.mjs';
import { permittedBranch, safeTrackedPath } from './validation.mjs';
import { hash } from './crypto.mjs';
import { confinedRead } from './confined-read.mjs';
import { parseIndex, withFrozenIndex } from './git-index.mjs';

export class GitWorkspace {
  constructor({ root, command }) {
    this.root = path.resolve(root);
    this.command = command;
  }

  async git(args, options = {}) {
    return this.command('git', ['-c', 'safe.directory=' + this.root, ...args], { cwd: this.root, ...options });
  }

  async gitText(args, options = {}) {
    return (await this.git(args, options)).toString('utf8').trim();
  }

  async snapshot() {
    ensure(await this.gitText(['rev-parse', '--show-toplevel']) === this.root, 'REPOSITORY_MISMATCH');
    ensure(await this.gitText(['rev-parse', '--show-object-format']) === 'sha1', 'REPOSITORY_MISMATCH');
    const origin = await this.gitText(['remote', 'get-url', 'origin']);
    ensure(origin === 'https://github.com/' + REPOSITORY + '.git', 'REPOSITORY_MISMATCH');
    const branch = await this.gitText(['branch', '--show-current']);
    ensure(permittedBranch(branch), 'BAD_BRANCH');
    await this.git(['check-ref-format', '--branch', branch]);
    const head = await this.gitText(['rev-parse', 'HEAD']);
    const base = await this.gitText(['rev-parse', 'refs/remotes/origin/main']);
    ensure(SHA.test(head) && SHA.test(base), 'STALE_PARENT');
    ensure((await this.git(['diff', '--name-only', '-z'])).length === 0
      && (await this.git(['ls-files', '--others', '--exclude-standard', '-z'])).length === 0
      && (await this.git(['ls-files', '-u'])).length === 0, 'WORKSPACE_DIRTY');
    const indexFile = path.resolve(this.root, await this.gitText(['rev-parse', '--git-path', 'index']));
    ensure(indexFile.startsWith(this.root + path.sep), 'BAD_PATH');
    const indexBytes = await confinedRead(indexFile, this.root, 'BAD_PATH', MAX_INDEX);
    const indexHash = hash(indexBytes);
    const { entries, changes, tree } = await withFrozenIndex(indexBytes, async (env) => {
      const options = { env };
      const entries = parseIndex(await this.git(['ls-files', '--stage', '-z'], options));
      const againstBase = (await this.git(['diff', '--cached', '--no-renames', '--name-only', '-z', base], options))
        .toString('utf8').split('\0').filter(Boolean);
      ensure(!againstBase.some((file) => file.toLowerCase() === 'license'), 'LICENSE_CHANGED');
      const changes = (await this.git(['diff', '--cached', '--no-renames', '--name-only', '-z', head], options))
        .toString('utf8').split('\0').filter(Boolean);
      ensure(changes.every(safeTrackedPath), 'BAD_PATH');
      const tree = await this.gitText(['write-tree'], options);
      ensure(SHA.test(tree), 'TREE_MISMATCH');
      return { entries, changes, tree };
    });
    ensure(hash(await confinedRead(indexFile, this.root, 'BAD_PATH', MAX_INDEX)) === indexHash
      && await this.gitText(['rev-parse', 'HEAD']) === head
      && await this.gitText(['branch', '--show-current']) === branch, 'INDEX_CHANGED');
    return { branch, head, base, tree, entries, changes, indexFile, indexHash, indexBytes };
  }

  async assertSnapshot(snapshot) {
    const latest = await this.snapshot();
    ensure(latest.branch === snapshot.branch && latest.head === snapshot.head && latest.base === snapshot.base
      && latest.tree === snapshot.tree && latest.indexHash === snapshot.indexHash, 'INDEX_CHANGED');
  }

  async assertPublishedSnapshot(snapshot, commit) {
    const latest = await this.snapshot();
    ensure(latest.branch === snapshot.branch && latest.head === commit
      && latest.base === snapshot.base && latest.tree === snapshot.tree
      && latest.indexHash === snapshot.indexHash, 'INDEX_CHANGED');
  }

  async fetchPublished(token, snapshot, commit) {
    const basic = Buffer.from('x-access-token:' + token).toString('base64');
    await this.git(['-c', 'credential.helper=', '-c', 'http.followRedirects=false',
      'fetch', '--no-tags', '--no-write-fetch-head', '--no-recurse-submodules',
      'https://github.com/' + REPOSITORY + '.git', 'refs/heads/' + snapshot.branch], {
      env: { GIT_CONFIG_COUNT: '2', GIT_CONFIG_KEY_0: 'http.https://github.com/.extraheader',
        GIT_CONFIG_VALUE_0: '', GIT_CONFIG_KEY_1: 'http.https://github.com/.extraheader',
        GIT_CONFIG_VALUE_1: 'AUTHORIZATION: basic ' + basic },
    });
    ensure(await this.gitText(['show', '--format=%T', '--no-patch', commit]) === snapshot.tree, 'TREE_MISMATCH');
    ensure(await this.gitText(['show', '--format=%P', '--no-patch', commit]) === snapshot.head, 'STALE_PARENT');
    await this.git(['merge-base', '--is-ancestor', snapshot.head, commit]);
    await this.assertSnapshot(snapshot);
    await this.git(['update-ref', 'refs/heads/' + snapshot.branch, commit, snapshot.head]);
    // update-ref leaves the staged index and working files intact; their tree is now HEAD's tree.
    ensure(await this.gitText(['rev-parse', 'HEAD']) === commit
      && await this.gitText(['write-tree']) === snapshot.tree, 'INDEX_CHANGED');
  }
}
