import { mkdtemp } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { runCommand } from '../../command.mjs';
import { privateKey } from './synthetic-data.mjs';
import { fixtureWriteFile, fixtureMkdir, fixtureRm } from './filesystem.mjs';

export class TemporaryRepository {
  constructor(root) {
    this.root = root;
    this.git = (args, options = {}) => runCommand('git', [
      '-c', 'user.name=Offline Test', '-c', 'user.email=offline@example.invalid', ...args,
    ], {cwd: root, ...options});
    this.text = async (args, options = {}) => (await this.git(args, options)).toString().trim();
  }

  static async create(t, {stage = true} = {}) {
    const root = await mkdtemp(path.join(os.tmpdir(), 'soulkiller-app-test-'));
    t.after(() => fixtureRm(root, {recursive: true, force: true}));
    const repository = new TemporaryRepository(root);
    await repository.initialize();
    if (stage) await repository.stageChange();
    return repository;
  }

  async initialize() {
    await this.git(['init', '--initial-branch=main']);
    await fixtureWriteFile(path.join(this.root, '.gitignore'), '.soulkiller-local/\n');
    await fixtureWriteFile(path.join(this.root, 'LICENSE'), 'Synthetic unchanged license\n');
    await fixtureWriteFile(path.join(this.root, 'README.md'), 'Initial synthetic document\n');
    await fixtureWriteFile(path.join(this.root, 'remove.txt'), 'Remove this synthetic file\n');
    await this.git(['add', '.']);
    await this.git(['commit', '-m', 'Synthetic baseline']);
    this.base = await this.text(['rev-parse', 'HEAD']);
    this.baseTree = await this.text(['show', '--format=%T', '--no-patch', 'HEAD']);
    await this.git(['remote', 'add', 'origin', 'https://github.com/Eneru/soulkiller.git']);
    await this.git(['update-ref', 'refs/remotes/origin/main', this.base]);
    await this.git(['switch', '-c', 'codex/test-publication']);
    await fixtureMkdir(path.join(this.root, '.soulkiller-local/github-app'), {recursive: true});
    await fixtureWriteFile(path.join(this.root, '.soulkiller-local/github-app/private-key.pem'), privateKey, {mode: 0o600});
    await fixtureWriteFile(path.join(this.root, '.soulkiller-local/pr.md'), 'Synthetic review body\n\nRefs #7\n');
  }

  async stageChange() {
    await fixtureWriteFile(path.join(this.root, 'README.md'), 'A staged synthetic document\n');
    await fixtureWriteFile(path.join(this.root, 'binary.bin'), Buffer.from([0, 255, 128, 13, 10, 0, 65]));
    await fixtureWriteFile(path.join(this.root, 'executable.sh'), '#!/bin/sh\nexit 0\n', {mode: 0o755});
    await fixtureRm(path.join(this.root, 'remove.txt'));
    await this.git(['add', '.']);
    await this.git(['update-index', '--chmod=+x', 'executable.sh']);
  }
}
