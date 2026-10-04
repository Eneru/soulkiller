import test from 'node:test';
import assert from 'node:assert/strict';
import { generateKeyPairSync, verify as verifySignature } from 'node:crypto';
import { CONFIG } from '../constants.mjs';
import { createJwt } from '../crypto.mjs';
import { code, now, privateKey, publicKey } from './helpers/synthetic-data.mjs';

test('RSA JWT carries the fixed App identity and bounded validity with a valid signature', () => {
  // Arrange
  const key = privateKey;
  // Act
  const jwt = createJwt(key, now);
  const [header, encodedPayload, signature] = jwt.split('.');
  const payload = JSON.parse(Buffer.from(encodedPayload, 'base64url'));
  // Assert
  assert.deepEqual(JSON.parse(Buffer.from(header, 'base64url')), {alg: 'RS256', typ: 'JWT'});
  assert.equal(payload.iss, String(CONFIG.appId));
  assert.equal(payload.iat, now / 1000 - 60);
  assert.equal(payload.exp, now / 1000 + 540);
  assert.equal(verifySignature('RSA-SHA256', Buffer.from(header + '.' + encodedPayload), publicKey,
    Buffer.from(signature, 'base64url')), true);
});

test('JWT signing rejects malformed private-key content', () => {
  // Arrange
  const key = 'invalid secret key content';
  // Act
  const operation = () => createJwt(key, now);
  // Assert
  assert.throws(operation, code('KEY_INVALID'));
});

test('JWT signing rejects a generated non-RSA key', () => {
  // Arrange
  const key = generateKeyPairSync('ed25519').privateKey.export({format: 'pem', type: 'pkcs8'});
  // Act
  const operation = () => createJwt(key, now);
  // Assert
  assert.throws(operation, code('KEY_INVALID'));
});
