import path from 'node:path';
import { REPOSITORY } from './constants.mjs';
import { ensure } from './guards.mjs';

export function hasControl(value) {
  return [...value].some((character) => character.codePointAt(0) < 32 || character.codePointAt(0) === 127);
}

export function permittedBranch(branch) {
  return /^(?:codex|feature|fix|docs)\/[a-z0-9][a-z0-9._/-]{0,99}$/u.test(branch)
    && !branch.includes('..') && !branch.includes('//') && !branch.endsWith('/')
    && !branch.split('/').some((part) => part.endsWith('.lock') || part.startsWith('.'));
}

export function safeTrackedPath(file) {
  const parts = file.split('/');
  return Boolean(file) && !path.posix.isAbsolute(file) && !file.includes('\\')
    && !hasControl(file)
    && !parts.some((part) => part === '..' || part === '.' || !part)
    && !parts.some((part) => /^\.soulkiller-local$/iu.test(part) || /^\.git$/iu.test(part))
    && !parts.some((part) => /^\.env(?:$|\.(?!example$|sample$))/iu.test(part)
      || /\.(?:pem|key|p12|pfx)$/iu.test(part) || /^id_(?:rsa|ed25519)$/u.test(part));
}

export function validateText(value, limit = 200) {
  ensure(typeof value === 'string' && value.trim() && value.length <= limit
    && !hasControl(value), 'BAD_ARGUMENT');
  return value.trim();
}

export function validateTokenScope(response, requested, now = Date.now()) {
  ensure(typeof response.token === 'string' && response.token.length >= 20, 'TOKEN_SCOPE');
  ensure(Array.isArray(response.repositories) && response.repositories.length === 1
    && response.repositories[0].full_name === REPOSITORY, 'TOKEN_SCOPE');
  const expires = Date.parse(response.expires_at);
  ensure(Number.isFinite(expires) && expires > now + 1000 && expires <= now + 3_660_000, 'TOKEN_SCOPE');
  const expected = new Map(Object.entries(requested));
  const actual = new Map(Object.entries(response.permissions || {}));
  ensure([...expected].every(([name, value]) => actual.get(name) === value), 'TOKEN_SCOPE');
  ensure([...actual].every(([name, value]) =>
    (name === 'metadata' && value === 'read') || expected.get(name) === value), 'TOKEN_SCOPE');
}
