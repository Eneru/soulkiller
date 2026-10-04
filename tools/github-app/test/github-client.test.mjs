import test from 'node:test';
import assert from 'node:assert/strict';
import { GitHubClient } from '../github-client.mjs';
import { code, token } from './helpers/synthetic-data.mjs';

test('GitHub transport fixes the API host, version, authentication and bounded redirect policy', async () => {
  // Arrange
  let requested;
  const client = new GitHubClient({timeout: 250, fetchImpl: async (url, options) => {
    requested = {url, options};
    return new Response('{"id":5174172}', {status: 200});
  }});
  // Act
  const result = await client.request('GET', '/app', token);
  // Assert
  assert.deepEqual(result, {id: 5174172});
  assert.equal(requested.url, 'https://api.github.com/app');
  assert.equal(requested.options.redirect, 'error');
  assert.ok(requested.options.signal instanceof AbortSignal);
  assert.equal(requested.options.headers['X-GitHub-Api-Version'], '2026-03-10');
  assert.equal(requested.options.headers.Authorization, 'Bearer ' + token);
});

for (const endpoint of ['https://evil.invalid', '//evil.invalid/a', '/x/../a', '/a#b']) {
  test('GitHub transport rejects endpoint ' + endpoint + ' before fetching', async () => {
    // Arrange
    let calls = 0;
    const client = new GitHubClient({fetchImpl: async () => { calls += 1; return new Response('{}'); }});
    // Act
    const attempt = client.request('GET', endpoint, token);
    // Assert
    await assert.rejects(attempt, code('BAD_ARGUMENT'));
    assert.equal(calls, 0);
  });
}

test('GitHub transport rejects an unsupported HTTP method before fetching', async () => {
  // Arrange
  let calls = 0;
  const client = new GitHubClient({fetchImpl: async () => { calls += 1; return new Response('{}'); }});
  // Act
  const attempt = client.request('PUT', '/app', token);
  // Assert
  await assert.rejects(attempt, code('BAD_ARGUMENT'));
  assert.equal(calls, 0);
});

const invalidResponses = [
  {name: 'forbidden response', response: () => new Response('private secret response', {status: 403})},
  {name: 'malformed JSON response', response: () => new Response('not-json')},
  {name: 'oversized response', response: () => new Response('x'.repeat(2 * 1024 * 1024 + 1))},
];
for (const {name, response} of invalidResponses) {
  test('GitHub transport redacts ' + name, async () => {
    // Arrange
    const client = new GitHubClient({fetchImpl: async () => response()});
    // Act
    const attempt = client.request('POST', '/app', token, {safe: true});
    // Assert
    await assert.rejects(attempt, (error) => code('API_FAILED')(error)
      && !JSON.stringify(error).includes('private secret'));
  });
}

test('GitHub transport accepts an empty token-revocation response', async () => {
  // Arrange
  const client = new GitHubClient({fetchImpl: async () => new Response(null, {status: 204})});
  // Act
  const result = await client.request('DELETE', '/installation/token', token);
  // Assert
  assert.equal(result, null);
});

test('GitHub transport permits a missing response only when explicitly requested', async () => {
  // Arrange
  const client = new GitHubClient({fetchImpl: async () => new Response(null, {status: 404})});
  // Act
  const result = await client.request('GET', '/missing', token, undefined, {missing: true});
  // Assert
  assert.equal(result, null);
});

test('GitHub transport redacts network exceptions containing a token', async () => {
  // Arrange
  const client = new GitHubClient({fetchImpl: async () => { throw new Error(token); }});
  // Act
  const attempt = client.request('GET', '/app', token);
  // Assert
  await assert.rejects(attempt, (error) => code('API_FAILED')(error) && !JSON.stringify(error).includes(token));
});
