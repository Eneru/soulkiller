import { generateKeyPairSync } from 'node:crypto';
import { PublicationError } from '../../errors.mjs';

export const { privateKey, publicKey } = generateKeyPairSync('rsa', {
  modulusLength: 2048,
  privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
  publicKeyEncoding: { type: 'spki', format: 'pem' },
});

export const now = Date.UTC(2026, 9, 3, 12);
export const token = 'synthetic-installation-token-for-offline-tests';
export const bot = 'eneru-soulkiller-agent[bot]';
export const code = (expected) => (error) => error instanceof PublicationError && error.code === expected;

export function scope(permissions = { contents: 'read', pull_requests: 'read' }) {
  return {
    token, repositories: [{ full_name: 'Eneru/soulkiller' }],
    permissions: { ...permissions, metadata: 'read' }, expires_at: new Date(now + 3_600_000).toISOString(),
  };
}

export const publication = Object.freeze({ execute: true, title: 'Publish the synthetic change', bodyFile: '.soulkiller-local/pr.md' });
