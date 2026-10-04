import test from 'node:test';
import assert from 'node:assert/strict';
import { main, HELP } from '../cli.mjs';
import { PublicationError } from '../errors.mjs';
import { runCommand } from '../command.mjs';
import { captureCliOutput } from './helpers/cli-output.mjs';

test('CLI help prints the documented text without invoking a publisher command', async () => {
  // Arrange
  const captured = captureCliOutput();
  // Act
  const status = await main(['--help'], captured.io);
  // Assert
  assert.equal(status, 0);
  assert.deepEqual(captured.outputs, [HELP]);
});

for (const [command, args, expected] of [
  ['check', ['check', '--execute'], {execute: true}],
  ['publish', ['publish', '--body-file', '.soulkiller-local/pr.md', '--title', 'Title'], {bodyFile: '.soulkiller-local/pr.md', title: 'Title'}],
  ['verify', ['verify', '--number', '17'], {number: 17}],
]) {
  test('CLI dispatches ' + command + ' with parsed options and a public result', async () => {
    // Arrange
    const captured = captureCliOutput();
    let received;
    const action = async (options) => { received = options; return {mode: 'synthetic-safe-result'}; };
    const publisher = {check: action, publish: action, verify: action};
    // Act
    const status = await main(args, {...captured.io, publisher});
    // Assert
    assert.equal(status, 0);
    assert.deepEqual(received, expected);
    assert.deepEqual(JSON.parse(captured.outputs.at(0)), {mode: 'synthetic-safe-result'});
  });
}

test('CLI rejects an unsupported command with a safe argument error', async () => {
  // Arrange
  const captured = captureCliOutput();
  // Act
  const status = await main(['unknown'], captured.io);
  // Assert
  assert.equal(status, 1);
  assert.equal(JSON.parse(captured.errors.at(0)).error, 'BAD_ARGUMENT');
});

test('CLI redacts unexpected publisher exceptions', async () => {
  // Arrange
  const captured = captureCliOutput();
  const publisher = {check: async () => { throw new Error('synthetic credential leak'); }};
  // Act
  const status = await main(['check'], {...captured.io, publisher});
  // Assert
  assert.equal(status, 1);
  assert.equal(JSON.parse(captured.errors.at(0)).error, 'COMMAND_FAILED');
  assert.equal(captured.errors.some((line) => line.includes('synthetic credential')), false);
});

test('CLI reports safe publication-recovery details from a typed error', async () => {
  // Arrange
  const captured = captureCliOutput();
  const publisher = {check: async () => { throw new PublicationError('PR_FAILED', {branchPublished: true, commit: 'a'.repeat(40)}); }};
  // Act
  const status = await main(['check'], {...captured.io, publisher});
  // Assert
  assert.equal(status, 1);
  const reported = JSON.parse(captured.errors.at(0));
  assert.equal(reported.branchPublished, true);
  assert.equal(reported.commit, 'a'.repeat(40));
});

test('standalone CLI help executes without credentials or a repository', async () => {
  // Arrange
  const args = [new URL('../cli.mjs', import.meta.url).pathname, '--help'];
  // Act
  const output = await runCommand(process.execPath, args);
  // Assert
  assert.ok(output.toString().includes('offline dry runs'));
});
