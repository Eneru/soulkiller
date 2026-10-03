import test from 'node:test';
import assert from 'node:assert/strict';
import { main, parseArgs, HELP } from '../cli.mjs';
import { PublicationError, runCommand } from '../publisher.mjs';

test('CLI parsing defaults offline and accepts only fixed supported command options', () => {
  assert.deepEqual(parseArgs([]), { help: true });
  assert.deepEqual(parseArgs(['--help']), { help: true });
  assert.deepEqual(parseArgs(['check']), { command: 'check', options: {} });
  assert.deepEqual(parseArgs(['verify', '--number', '17', '--execute']), {
    command: 'verify', options: { number: 17, execute: true },
  });
  assert.deepEqual(parseArgs(['publish', '--title', 'Synthetic title', '--body-file', '.soulkiller-local/pr.md',
    '--message', 'Synthetic message', '--key-file', '.soulkiller-local/github-app/private-key.pem']), {
    command: 'publish', options: { title: 'Synthetic title', bodyFile: '.soulkiller-local/pr.md',
      message: 'Synthetic message', keyFile: '.soulkiller-local/github-app/private-key.pem' },
  });
  for (const args of [
    ['merge'], ['check', '--api', 'https://evil.invalid'], ['check', '--execute', '--execute'],
    ['check', '--key-file'], ['check', '--key-file', '--execute'], ['check', '--title', 'x'],
    ['check', '--key-file', 'a', '--key-file', 'b'], ['publish'], ['verify', '--number', '0'],
    ['verify', '--number', 'x'], ['verify', '--number', '99999999999999999999'],
  ]) assert.throws(() => parseArgs(args), PublicationError);
});

test('CLI reports public result only, handles commands and redacts unknown exceptions', async () => {
  const outputs = [];
  const errors = [];
  const io = { output: (value) => outputs.push(value), errorOutput: (value) => errors.push(value) };
  assert.equal(await main(['--help'], io), 0);
  assert.equal(outputs[0], HELP);
  const publisher = {
    check: async (options) => ({ mode: options.execute ? 'authenticated-check' : 'dry-run' }),
    publish: async () => ({ mode: 'dry-run' }),
    verify: async () => ({ mode: 'verified' }),
  };
  assert.equal(await main(['check', '--execute'], { ...io, publisher }), 0);
  assert.equal(await main(['publish', '--body-file', '.soulkiller-local/pr.md', '--title', 'Title'],
    { ...io, publisher }), 0);
  assert.equal(await main(['verify', '--number', '17'], { ...io, publisher }), 0);
  assert.equal(await main(['unknown'], io), 1);
  publisher.check = async () => { throw new Error('synthetic credential leak'); };
  assert.equal(await main(['check'], { ...io, publisher }), 1);
  assert.equal(errors.some((value) => value.includes('synthetic credential')), false);
  publisher.check = async () => { throw new PublicationError('PR_FAILED', { branchPublished: true, commit: 'a'.repeat(40) }); };
  assert.equal(await main(['check'], { ...io, publisher }), 1);
  assert.equal(JSON.parse(errors.at(-1)).branchPublished, true);
});

test('standalone CLI help executes without credentials or a repository', async () => {
  const output = await runCommand(process.execPath,
    [new URL('../cli.mjs', import.meta.url).pathname, '--help']);
  assert.ok(output.toString().includes('offline dry runs'));
});
