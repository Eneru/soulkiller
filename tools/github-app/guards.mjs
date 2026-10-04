import { PublicationError } from './errors.mjs';

export function fail(code, details) {
  throw new PublicationError(code, details);
}

export function ensure(condition, code, details) {
  if (!condition) fail(code, details);
}
