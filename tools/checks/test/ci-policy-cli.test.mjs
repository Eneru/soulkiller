import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { main } from '../ci-policy-cli.mjs';
import { capturedOutput, eventEnvironment } from './helpers/ci-policy-fixture.mjs';

const tag = { eventName: 'push', ref: 'refs/tags/v1.2.3', refType: 'tag', deleted: false };
for (const [name, environment, expected] of [
  ['eligible tag', eventEnvironment(tag), true],
  ['missing environment', {}, false],
  ['malformed tag', eventEnvironment({ ...tag, ref: 'refs/tags/v01.2.3' }), false],
  ['true deletion', eventEnvironment({ ...tag, deleted: true }), false],
  ['ambiguous deletion', { ...eventEnvironment(tag), SOULKILLER_CI_DELETED: 'FALSE' }, false],
]) {
  test('CLI output: ' + name, () => {
    // Arrange
    const capture = capturedOutput();
    // Act
    const status = main([], environment, capture.output);
    // Assert
    assert.equal(status, 0);
    assert.deepEqual(capture.lines, ['eligible=' + expected]);
    assert.deepEqual(capture.errors, []);
  });
}

test('CLI rejects command arguments without reflecting their contents', () => {
  // Arrange
  const capture = capturedOutput();
  // Act
  const status = main(['SYNTHETIC_UNTRUSTED_VALUE'], {}, capture.output);
  // Assert
  assert.equal(status, 1);
  assert.deepEqual(capture.lines, []);
  assert.deepEqual(capture.errors, ['CI eligibility accepts environment inputs only.']);
});

test('executable CLI returns only the eligible output for a valid tag', () => {
  // Arrange
  const environment = { ...process.env, ...eventEnvironment(tag) };
  // Act
  const result = spawnSync(process.execPath, ['tools/checks/ci-policy-cli.mjs'], { cwd: new URL('../../../', import.meta.url), env: environment, encoding: 'utf8', timeout: 10000 });
  // Assert
  assert.equal(result.status, 0);
  assert.equal(result.stdout, 'eligible=true\n');
  assert.equal(result.stderr, '');
});
