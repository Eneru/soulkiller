import { createHash, createPrivateKey, createSign } from 'node:crypto';
import { CONFIG } from './constants.mjs';
import { ensure, fail } from './guards.mjs';

export function createJwt(pem, now = Date.now()) {
  try {
    const key = createPrivateKey(pem);
    ensure(key.asymmetricKeyType === 'rsa', 'KEY_INVALID');
    const header = Buffer.from(JSON.stringify({ alg: 'RS256', typ: 'JWT' })).toString('base64url');
    const payload = Buffer.from(JSON.stringify({
      iat: Math.floor(now / 1000) - 60,
      exp: Math.floor(now / 1000) + 540,
      iss: String(CONFIG.appId),
    })).toString('base64url');
    const signingInput = header + '.' + payload;
    const signer = createSign('RSA-SHA256');
    signer.update(signingInput);
    return signingInput + '.' + signer.sign(key, 'base64url');
  } catch {
    fail('KEY_INVALID');
  }
}

export function hash(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

export function blobHash(bytes) {
  return createHash('sha1').update('blob ' + bytes.length + '\0').update(bytes).digest('hex');
}
