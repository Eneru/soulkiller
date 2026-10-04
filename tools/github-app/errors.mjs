import { ERROR_MESSAGES } from './constants.mjs';

const messages = new Map(Object.entries(ERROR_MESSAGES));

export class PublicationError extends Error {
  constructor(code, details = {}) {
    super(messages.get(code) || 'Publication stopped.');
    this.name = 'PublicationError';
    this.code = code;
    // Only callers construct these public identifiers; never attach raw causes or API bodies.
    this.details = details;
  }
}
