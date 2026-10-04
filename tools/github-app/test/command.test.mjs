import test from 'node:test';
import assert from 'node:assert/strict';
import { runCommand } from '../command.mjs';
import { code } from './helpers/synthetic-data.mjs';

test('command execution preserves binary stdin and stdout', async () => {
  // Arrange
  const bytes = Buffer.from([0, 255, 1]);
  // Act
  const output = await runCommand(process.execPath, ['-e', 'process.stdin.pipe(process.stdout)'], {input: bytes});
  // Assert
  assert.deepEqual(output, bytes);
});

test('command failures with sensitive stderr produce redacted errors', async () => {
  // Arrange
  const args = ['-e', 'console.error("synthetic secret");process.exit(1)'];
  // Act
  const attempt = runCommand(process.execPath, args);
  // Assert
  await assert.rejects(attempt, (error) => code('COMMAND_FAILED')(error) && !error.message.includes('synthetic secret'));
});
