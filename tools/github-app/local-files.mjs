import { realpath, stat } from 'node:fs/promises';
import { TextDecoder } from 'node:util';
import path from 'node:path';
import { MAX_KEY, MAX_BODY } from './constants.mjs';
import { ensure, fail } from './guards.mjs';
import { hasControl } from './validation.mjs';
import { hash } from './crypto.mjs';
import { confinedRead } from './confined-read.mjs';

export class LocalFiles {
  constructor({ root, workspace }) {
    this.root = path.resolve(root);
    this.workspace = workspace;
  }

  async localPath(value, category) {
    const relative = path.relative(this.root, path.resolve(this.root, value));
    const prefix = category === 'key' ? '.soulkiller-local/github-app/' : '.soulkiller-local/';
    const code = category === 'key' ? 'KEY_INVALID' : 'BODY_INVALID';
    try {
      ensure(relative.startsWith(prefix) && !hasControl(relative)
        && !relative.split('/').some((part) => part === '..' || part === '.' || !part), code);
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Lexically confined ignored input; resolved containment is checked next.
      const full = await realpath(path.join(this.root, relative));
      const allowed = path.join(this.root, category === 'key' ? '.soulkiller-local/github-app' : '.soulkiller-local');
      // Compare to the lexical directory: escaping ancestor symlinks are rejected too.
      ensure(full.startsWith(allowed + path.sep), code);
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Contained resolved path; descriptor read later rechecks identity.
      ensure((await stat(full)).isFile(), code);
      await this.workspace.git(['check-ignore', '--quiet', '--', relative]);
      const tracked = await this.workspace.git(['ls-files', '-z', '--', relative, path.relative(this.root, full)]);
      ensure(tracked.length === 0, code);
      return full;
    } catch {
      fail(code);
    }
  }

  async readLocal(value, category) {
    const file = await this.localPath(value, category);
    const allowed = path.join(this.root, category === 'key' ? '.soulkiller-local/github-app' : '.soulkiller-local');
    const bytes = await confinedRead(file, allowed, category === 'key' ? 'KEY_INVALID' : 'BODY_INVALID',
      category === 'key' ? MAX_KEY : MAX_BODY);
    return { file, bytes };
  }

  async readBody(value) {
    const { file, bytes } = await this.readLocal(value, 'body');
    ensure(bytes.length > 0 && bytes.length <= MAX_BODY, 'BODY_INVALID');
    try {
      return { file, bytes, text: new TextDecoder('utf-8', { fatal: true }).decode(bytes), hash: hash(bytes) };
    } catch {
      fail('BODY_INVALID');
    }
  }

  async assertBody(body) {
    ensure(hash((await this.readLocal(body.file, 'body')).bytes) === body.hash, 'INDEX_CHANGED');
  }
}
