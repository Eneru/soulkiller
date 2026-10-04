import test from 'node:test';
import assert from 'node:assert/strict';
import { permittedBranch, safeTrackedPath, validateText } from '../validation.mjs';
import { code } from './helpers/synthetic-data.mjs';

const rejectedBranches = ['main', 'tags/v1', 'codex/../x', 'codex/x.lock', 'codex/x//y', 'codex/.x', 'codex/x/'];
for (const branch of rejectedBranches) {
  test('branch validation rejects ' + JSON.stringify(branch), () => {
    // Arrange
    const input = branch;
    // Act
    const accepted = permittedBranch(input);
    // Assert
    assert.equal(accepted, false);
  });
}
for (const branch of ['codex/10-publisher', 'feature/first-step', 'fix/a/b', 'docs/readme']) {
  test('branch validation accepts ' + branch, () => {
    // Arrange
    const input = branch;
    // Act
    const accepted = permittedBranch(input);
    // Assert
    assert.equal(accepted, true);
  });
}

const rejectedPaths = ['', '../key', '/abs', 'a\\b', '.soulkiller-local/key', '.git/config', '.env', 'secrets/private.pem', 'id_rsa', 'dir\nname'];
for (const file of rejectedPaths) {
  test('tracked path validation rejects ' + JSON.stringify(file), () => {
    // Arrange
    const input = file;
    // Act
    const accepted = safeTrackedPath(input);
    // Assert
    assert.equal(accepted, false);
  });
}
for (const file of ['README.md', '.env.example', 'docs/guide.md']) {
  test('tracked path validation accepts ' + file, () => {
    // Arrange
    const input = file;
    // Act
    const accepted = safeTrackedPath(input);
    // Assert
    assert.equal(accepted, true);
  });
}

test('text validation trims a supported single-line title', () => {
  // Arrange
  const title = ' title ';
  // Act
  const result = validateText(title);
  // Assert
  assert.equal(result, 'title');
});
for (const [name, input] of [['empty text', ''], ['multiline text', 'x\nsecret'], ['overlong text', 'x'.repeat(201)]]) {
  test('text validation rejects ' + name, () => {
    // Arrange
    const value = input;
    // Act
    const operation = () => validateText(value);
    // Assert
    assert.throws(operation, code('BAD_ARGUMENT'));
  });
}
