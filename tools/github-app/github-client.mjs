import { API, CONFIG } from './constants.mjs';
import { PublicationError } from './errors.mjs';
import { ensure, fail } from './guards.mjs';

const { AbortSignal } = globalThis;

export class GitHubClient {
  constructor({ fetchImpl = globalThis.fetch, now = Date.now, timeout = 15_000 } = {}) {
    this.fetchImpl = fetchImpl;
    this.now = now;
    this.timeout = timeout;
  }

  async request(method, endpoint, auth, body, { missing = false } = {}) {
    ensure(endpoint.startsWith('/') && !endpoint.startsWith('//')
      && !endpoint.includes('..') && !endpoint.includes('#')
      && ['GET', 'POST', 'PATCH', 'DELETE'].includes(method), 'BAD_ARGUMENT');
    // This internal API transport is deliberately fixed; the CLI exposes no URL override.
    const url = new URL(endpoint, API);
    ensure(url.origin === API, 'BAD_ARGUMENT');
    try {
      const response = await this.fetchImpl(url.href, {
        method, redirect: 'error', signal: AbortSignal.timeout(this.timeout),
        headers: {
          Accept: 'application/vnd.github+json', Authorization: 'Bearer ' + auth,
          'X-GitHub-Api-Version': CONFIG.apiVersion, 'Content-Type': 'application/json',
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
      if (missing && response.status === 404) return null;
      if (!response.ok) fail('API_FAILED', { status: response.status });
      if (response.status === 204) return null;
      const raw = await response.text();
      ensure(Buffer.byteLength(raw) <= 2 * 1024 * 1024, 'API_FAILED');
      return JSON.parse(raw);
    } catch (error) {
      if (error instanceof PublicationError) throw error;
      fail('API_FAILED');
    }
  }
}
