import { open, realpath } from 'node:fs/promises';
import { constants } from 'node:fs';
import path from 'node:path';
import { ensure, fail } from './guards.mjs';

export async function confinedRead(file, allowed, code, maximum) {
  let handle;
  try {
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Caller validated the ignored path; O_NOFOLLOW rejects a swapped leaf symlink.
    handle = await open(file, constants.O_RDONLY | constants.O_NOFOLLOW);
    const info = await handle.stat();
    ensure(info.isFile() && info.size <= maximum, code);
    // Linux descriptor resolution checks the file actually opened, including ancestor swaps.
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- This is the process-owned opened descriptor, not a caller-controlled path.
    const target = await realpath('/proc/self/fd/' + handle.fd);
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Recheck the confined lexical path against the open descriptor before reading.
    ensure(target.startsWith(allowed + path.sep) && target === await realpath(file), code);
    return await handle.readFile();
  } catch {
    fail(code);
  } finally {
    await handle?.close();
  }
}
