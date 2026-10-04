import test from 'node:test';
import assert from 'node:assert/strict';
import { parseArgs } from '../cli.mjs';
import { code } from './helpers/synthetic-data.mjs';

const body = '.soulkiller-local/pr.md';
const acceptedArguments = [
  {name: 'empty invocation help', args: [], expected: {help: true}},
  {name: 'explicit help', args: ['--help'], expected: {help: true}},
  {name: 'offline check', args: ['check'], expected: {command: 'check', options: {}}},
  {name: 'explicit authenticated verification', args: ['verify', '--number', '17', '--execute'], expected: {command: 'verify', options: {number: 17, execute: true}}},
  {name: 'offline publication with optional message and key', args: ['publish', '--title', 'Synthetic title', '--body-file', body, '--message', 'Synthetic message', '--key-file', '.soulkiller-local/github-app/private-key.pem'], expected: {command: 'publish', options: {title: 'Synthetic title', bodyFile: body, message: 'Synthetic message', keyFile: '.soulkiller-local/github-app/private-key.pem'}}},
  {name: 'explicit PR metadata update', args: ['publish', '--title', 'Title', '--body-file', body, '--update-pr'], expected: {command: 'publish', options: {title: 'Title', bodyFile: body, updatePr: true}}},
  {name: 'offline review reply', args: ['reply', '--number', '17', '--comment', '4176900402', '--body-file', body], expected: {command: 'reply', options: {number: 17, comment: 4176900402, bodyFile: body}}},
  {name: 'explicit authenticated review reply', args: ['reply', '--number', '17', '--comment', '4176900402', '--body-file', body, '--execute'], expected: {command: 'reply', options: {number: 17, comment: 4176900402, bodyFile: body, execute: true}}},
];
for (const {name, args, expected} of acceptedArguments) {
  test('CLI parses ' + name, () => {
    // Arrange
    const input = [...args];
    // Act
    const result = parseArgs(input);
    // Assert
    assert.deepEqual(result, expected);
  });
}

const rejectedArguments = [
  {name: 'merge command', args: ['merge']},
  {name: 'custom API endpoint', args: ['check', '--api', 'https://evil.invalid']},
  {name: 'duplicate execution flag', args: ['check', '--execute', '--execute']},
  {name: 'missing key path', args: ['check', '--key-file']},
  {name: 'flag used as key path', args: ['check', '--key-file', '--execute']},
  {name: 'title on check', args: ['check', '--title', 'x']},
  {name: 'duplicate key flag', args: ['check', '--key-file', 'a', '--key-file', 'b']},
  {name: 'missing publish fields', args: ['publish']},
  {name: 'zero PR number', args: ['verify', '--number', '0']},
  {name: 'non-numeric PR number', args: ['verify', '--number', 'x']},
  {name: 'unsafe PR integer', args: ['verify', '--number', '99999999999999999999']},
  {name: 'metadata update on check', args: ['check', '--update-pr']},
  {name: 'metadata update on verify', args: ['verify', '--number', '17', '--update-pr']},
  {name: 'duplicate metadata update', args: ['publish', '--title', 'T', '--body-file', body, '--update-pr', '--update-pr']},
  {name: 'reply missing comment', args: ['reply', '--number', '17', '--body-file', body]},
  {name: 'reply missing body', args: ['reply', '--number', '17', '--comment', '1']},
  {name: 'reply missing PR number', args: ['reply', '--comment', '1', '--body-file', body]},
  {name: 'reply duplicate comment', args: ['reply', '--number', '17', '--comment', '1', '--comment', '2', '--body-file', body]},
  {name: 'reply zero comment', args: ['reply', '--number', '17', '--comment', '0', '--body-file', body]},
  {name: 'reply negative comment', args: ['reply', '--number', '17', '--comment', '-1', '--body-file', body]},
  {name: 'reply non-numeric comment', args: ['reply', '--number', '17', '--comment', 'x', '--body-file', body]},
  {name: 'reply unsafe comment integer', args: ['reply', '--number', '17', '--comment', '99999999999999999999', '--body-file', body]},
  {name: 'reply unsafe PR integer', args: ['reply', '--number', '99999999999999999999', '--comment', '1', '--body-file', body]},
  {name: 'reply metadata update', args: ['reply', '--number', '17', '--comment', '1', '--body-file', body, '--update-pr']},
  {name: 'reply publication title', args: ['reply', '--number', '17', '--comment', '1', '--body-file', body, '--title', 'x']},
];
for (const {name, args} of rejectedArguments) {
  test('CLI rejects ' + name, () => {
    // Arrange
    const input = [...args];
    // Act
    const operation = () => parseArgs(input);
    // Assert
    assert.throws(operation, code('BAD_ARGUMENT'));
  });
}
