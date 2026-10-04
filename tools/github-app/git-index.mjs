import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { SHA } from './constants.mjs';
import { ensure } from './guards.mjs';
import { safeTrackedPath } from './validation.mjs';

export function parseIndex(raw) {
  return raw.toString('utf8').split('\0').filter(Boolean).map((record) => {
    const split = record.indexOf('\t');
    const [mode, sha, stage] = record.slice(0, split).split(' ');
    ensure(split > 0 && SHA.test(sha) && stage === '0'
      && ['100644', '100755'].includes(mode), 'WORKSPACE_DIRTY');
    const file = record.slice(split + 1);
    ensure(safeTrackedPath(file), 'BAD_PATH');
    return { mode, sha, path: file };
  });
}

export async function withFrozenIndex(bytes, operation) {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'soulkiller-publish-index-'));
  const file = path.join(directory, 'index');
  try {
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Fresh process-owned temporary directory stores the captured index only.
    await writeFile(file, bytes, { mode: 0o600 });
    return await operation({ GIT_INDEX_FILE: file });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}
