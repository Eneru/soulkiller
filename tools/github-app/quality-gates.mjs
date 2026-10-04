import { ensure, fail } from './guards.mjs';
import { withFrozenIndex } from './git-index.mjs';

export class QualityGates {
  constructor({ root, workspace, command }) {
    this.root = root;
    this.workspace = workspace;
    this.command = command;
  }

  async preflight(body, title, message, snapshot) {
    const args = ['tools/checks/check.sh', body ? 'secrets-publication' : 'secrets'];
    if (body) args.push('--body-file', body.file, '--metadata-stdin');
    try {
      ensure(snapshot?.indexBytes, 'INDEX_CHANGED');
      await withFrozenIndex(snapshot.indexBytes, async (env) => {
        await this.command('bash', args, {
          cwd: this.root, env,
          input: body ? title + '\n' + message + '\n' + body.text + '\n' : undefined,
        });
        await this.command('openspec', ['validate', '--all', '--strict', '--no-interactive'], { cwd: this.root });
        await this.workspace.git(['diff', '--check'], { env });
        await this.workspace.git(['diff', '--cached', '--check'], { env });
      });
    } catch {
      fail('PREFLIGHT_FAILED');
    }
  }
}
