import test from 'node:test';
import assert from 'node:assert/strict';
import { validateTokenScope } from '../validation.mjs';
import { code, now, scope } from './helpers/synthetic-data.mjs';

const wanted = Object.freeze({contents: 'read', pull_requests: 'read'});
test('installation token has exactly one repository, approved permissions and bounded lifetime', () => {
  // Arrange
  const token = scope(wanted);
  // Act
  const operation = () => validateTokenScope(token, wanted, now);
  // Assert
  assert.doesNotThrow(operation);
});
const invalidScopes = [
  {name: 'empty token', mutation: {token: ''}},
  {name: 'no repository', mutation: {repositories: []}},
  {name: 'another repository', mutation: {repositories: [{full_name: 'Other/repo'}]}},
  {name: 'multiple repositories', mutation: {repositories: [{full_name: 'Eneru/soulkiller'}, {full_name: 'Other/repo'}]}},
  {name: 'excess contents permission', mutation: {permissions: {contents: 'write', pull_requests: 'read'}}},
  {name: 'unrequested permission', mutation: {permissions: {...wanted, issues: 'write'}}},
  {name: 'expired token', mutation: {expires_at: new Date(now - 1).toISOString()}},
  {name: 'excessive lifetime', mutation: {expires_at: new Date(now + 9_000_000).toISOString()}},
];
for (const {name, mutation} of invalidScopes) {
  test('installation token rejects ' + name, () => {
    // Arrange
    const token = {...scope(wanted), ...mutation};
    // Act
    const operation = () => validateTokenScope(token, wanted, now);
    // Assert
    assert.throws(operation, code('TOKEN_SCOPE'));
  });
}
