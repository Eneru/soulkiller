import test from 'node:test';
import assert from 'node:assert/strict';
import { main } from '../cli.mjs';
import { captureCliOutput } from './helpers/cli-output.mjs';

for (const execute of [false, true]) {
  test('CLI review reply dispatches only the reply service with execute=' + execute, async () => {
    // Arrange
    const captured = captureCliOutput();
    const calls = [];
    const publisher = {publish: async () => { throw new Error('Publication must not run'); }};
    const replyService = {reply: async (options) => { calls.push(options); return {mode: execute ? 'replied' : 'dry-run'}; }};
    const args = ['reply', '--number', '17', '--comment', '4176900402', '--body-file', '.soulkiller-local/reply.md'];
    if (execute) args.push('--execute');
    // Act
    const status = await main(args, {...captured.io, publisher, replyService});
    // Assert
    assert.equal(status, 0);
    assert.deepEqual(calls, [{number: 17, comment: 4176900402, bodyFile: '.soulkiller-local/reply.md', ...(execute ? {execute: true} : {})}]);
    assert.deepEqual(JSON.parse(captured.outputs.at(0)), {mode: execute ? 'replied' : 'dry-run'});
    assert.equal(captured.errors.length, 0);
  });
}

test('CLI review reply redacts unexpected service errors', async () => {
  // Arrange
  const captured = captureCliOutput();
  const replyService = {reply: async () => { throw new Error('synthetic reply credential'); }};
  // Act
  const status = await main(['reply', '--number', '17', '--comment', '1', '--body-file', '.soulkiller-local/reply.md'], {...captured.io, replyService});
  // Assert
  assert.equal(status, 1);
  assert.equal(JSON.parse(captured.errors.at(0)).error, 'COMMAND_FAILED');
  assert.equal(captured.errors.some((line) => line.includes('synthetic reply credential')), false);
});
