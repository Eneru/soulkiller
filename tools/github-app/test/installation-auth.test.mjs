import test from 'node:test';
import assert from 'node:assert/strict';
import { CONFIG } from '../constants.mjs';
import { code, scope } from './helpers/synthetic-data.mjs';
import { createPublicationFixture } from './helpers/publication-fixture.mjs';

test('authenticated check verifies fixed installation and repository then revokes its read token', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  // Act
  const result = await f.publisher.check({ execute: true });
  // Assert
  assert.equal(result.remoteChecks, 'passed');
  assert.equal(result.installationId, 123);
  assert.equal(result.tokenRevoked, true);
  assert.equal(f.api.revoked, 1);
  const mint = f.api.requests.find((request) => request.endpoint.endsWith('/access_tokens'));
  assert.deepEqual(mint.body, { repositories: ['soulkiller'],
    permissions: { contents: 'read', pull_requests: 'read' } });
  assert.equal(f.api.requests.some((request) => request.endpoint.endsWith('/git/commits')), false);
});


for (const [name, response] of [
  ['wrong App identity', ({endpoint}) => endpoint === '/app' ? {id: 1, slug: 'other'} : undefined],
  ['wrong installation owner', ({endpoint}) => endpoint.endsWith('/installation') ? {id: 123, app_id: CONFIG.appId, account: {login: 'Other'}} : undefined],
]) {
  test('installation authentication rejects ' + name + ' before minting a token', async (t) => {
    // Arrange
    const f = await createPublicationFixture(t);
    f.api.intercept = response;
    // Act
    const attempt = f.publisher.check({execute: true});
    // Assert
    await assert.rejects(attempt, code('APP_MISMATCH'));
    assert.equal(f.api.requests.some((request) => request.endpoint.endsWith('/access_tokens')), false);
  });
}

test('invalid installation token scope is revoked before rejection', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  f.api.intercept = ({endpoint, body}) => endpoint.endsWith('/access_tokens')
    ? {...scope(body.permissions), permissions: {...body.permissions, administration: 'write'}} : undefined;
  // Act
  const attempt = f.publisher.check({execute: true});
  // Assert
  await assert.rejects(attempt, code('TOKEN_SCOPE'));
  assert.equal(f.api.revoked, 1);
});

test('a token-revocation failure remains an explicit safe error', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  f.api.intercept = ({method}) => { if (method === 'DELETE') throw new Error('revocation secret response'); };
  // Act
  const attempt = f.publisher.check({execute: true});
  // Assert
  await assert.rejects(attempt, (error) => code('TOKEN_REVOCATION_FAILED')(error)
    && !JSON.stringify(error).includes('revocation secret response'));
});

test('invalid scope and failed revocation preserve the original scope error with a safe flag', async (t) => {
  // Arrange
  const f = await createPublicationFixture(t);
  f.api.intercept = ({method, endpoint, body}) => {
    if (method === 'DELETE') throw new Error('revocation secret');
    if (endpoint.endsWith('/access_tokens')) return {...scope(body.permissions), repositories: []};
    return undefined;
  };
  // Act
  const attempt = f.publisher.check({execute: true});
  // Assert
  await assert.rejects(attempt, (error) => code('TOKEN_SCOPE')(error)
    && error.details.tokenRevocationFailed === true && !JSON.stringify(error).includes('revocation secret'));
});
