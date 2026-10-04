import { readFileSync } from 'node:fs';

// eslint-disable-next-line security/detect-non-literal-fs-filename -- Fixed module-relative public configuration; no caller-selected path.
export const CONFIG = Object.freeze(JSON.parse(readFileSync(new URL('./config.json', import.meta.url), 'utf8')));
export const REPOSITORY = 'Eneru/soulkiller';
export const BOT = 'eneru-soulkiller-agent[bot]';
export const API = 'https://api.github.com';
export const SHA = /^[a-f0-9]{40}$/u;
export const MAX_BLOB = 16 * 1024 * 1024;

export const ERROR_MESSAGES = Object.freeze({
  BAD_ARGUMENT: 'Unsupported or invalid command argument.',
  BAD_BRANCH: 'Use a permitted short-lived development branch.',
  BAD_PATH: 'A local or staged path is not permitted.',
  KEY_INVALID: 'The ignored local RSA key is missing or invalid.',
  BODY_INVALID: 'The ignored UTF-8 PR body is missing or invalid.',
  WORKSPACE_DIRTY: 'Stage all intended files and resolve other workspace changes first.',
  LICENSE_CHANGED: 'LICENSE differs from the starting main revision.',
  COMMAND_FAILED: 'A required local command failed; its output is withheld.',
  PREFLIGHT_FAILED: 'A required validation or secret scan failed; its output is withheld.',
  API_FAILED: 'A GitHub API request failed; its response is withheld.',
  APP_MISMATCH: 'The authenticated App or installation does not match public configuration.',
  TOKEN_SCOPE: 'The installation token is not restricted to the required repository and permissions.',
  REPOSITORY_MISMATCH: 'The repository, default branch or origin does not match Soulkiller.',
  STALE_PARENT: 'The local or remote parent changed or is not an eligible verified bot revision.',
  INDEX_CHANGED: 'The branch, files, index or PR body changed during publication.',
  TREE_MISMATCH: 'GitHub did not return the exact staged Git object.',
  COMMIT_UNVERIFIED: 'The commit is not verified as the configured App bot.',
  REF_RACE: 'The remote development ref changed during publication.',
  NOTHING_STAGED: 'There are no staged changes or verified published branch to resume.',
  PR_FAILED: 'The branch is published but the ready PR could not be created or verified.',
  REVIEW_COMMENT_INVALID: 'The selected comment is not a top-level maintainer review comment on this PR.',
  REPLY_FAILED: 'The review reply could not be safely created or verified.',
  TOKEN_REVOCATION_FAILED: 'Token revocation could not be confirmed; the token remains time-limited.',
});

export const DEFAULT_ROOT = '/workspaces/soulkiller';
export const MAX_KEY = 16_384;
export const MAX_BODY = 65_536;
export const MAX_INDEX = 16 * 1024 * 1024;
export const PLATFORM_COMMITTER = Object.freeze({ login: 'web-flow', name: 'GitHub', email: 'noreply@github.com' });
