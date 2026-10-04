import { CONFIG, REPOSITORY } from './constants.mjs';
import { PublicationError } from './errors.mjs';
import { ensure } from './guards.mjs';
import { createJwt } from './crypto.mjs';
import { validateTokenScope } from './validation.mjs';

export class InstallationAuth {
  constructor({ files, client, now }) {
    this.files = files;
    this.client = client;
    this.now = now;
  }

  async withInstallation(permissions, keyFile, operation) {
    const { bytes: pem } = await this.files.readLocal(keyFile || CONFIG.keyFile, 'key');
    let jwt;
    try { jwt = createJwt(pem, this.now()); } finally { pem.fill(0); }
    const app = await this.client.request('GET', '/app', jwt);
    ensure(app.id === CONFIG.appId && app.slug === CONFIG.appSlug, 'APP_MISMATCH');
    const installation = await this.client.request('GET', '/repos/' + REPOSITORY + '/installation', jwt);
    ensure(Number.isSafeInteger(installation.id) && installation.app_id === CONFIG.appId
      && installation.account?.login === 'Eneru', 'APP_MISMATCH');
    const minted = await this.client.request('POST', '/app/installations/' + installation.id + '/access_tokens',
      jwt, { repositories: ['soulkiller'], permissions });
    let token = typeof minted.token === 'string' ? minted.token : '';
    let result;
    let error;
    try {
      validateTokenScope(minted, permissions, this.now());
      delete minted.token;
      result = await operation(token, installation.id);
    } catch (caught) {
      error = caught instanceof PublicationError ? caught : new PublicationError('API_FAILED');
    } finally {
      if (token) {
        try {
          await this.client.request('DELETE', '/installation/token', token);
        } catch {
          if (error) error.details.tokenRevocationFailed = true;
          else error = new PublicationError('TOKEN_REVOCATION_FAILED', result ? {
            branch: result.branch, commit: result.commit, url: result.url,
          } : {});
        }
      }
    }
    if (error) throw error;
    return { ...result, tokenRevoked: true };
  }
}
