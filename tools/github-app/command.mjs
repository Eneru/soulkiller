import { execFile } from 'node:child_process';
import { PublicationError } from './errors.mjs';

export function runCommand(file, args, { cwd, input, env = {} } = {}) {
  return new Promise((resolve, reject) => {
    const childEnv = { ...process.env };
    for (const key of Object.keys(childEnv)) {
      if (/^(?:GIT_|GH_TOKEN$|GITHUB_TOKEN$)/u.test(key)) Reflect.deleteProperty(childEnv, key);
    }
    Object.assign(childEnv, {
      GIT_TERMINAL_PROMPT: '0', GIT_ASKPASS: '/bin/false',
      GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_NOSYSTEM: '1',
      GIT_NO_REPLACE_OBJECTS: '1', GIT_OPTIONAL_LOCKS: '0',
      OPENSPEC_TELEMETRY: '0', OPENSPEC_NO_UPDATE_CHECK: '1',
    }, env);
    const child = execFile(file, args, {
      cwd, env: childEnv, encoding: 'buffer', timeout: 60_000, maxBuffer: 64 * 1024 * 1024,
    }, (error, stdout) => {
      if (error) reject(new PublicationError('COMMAND_FAILED'));
      else resolve(stdout);
    });
    child.stdin?.on('error', () => {});
    child.stdin?.end(input);
  });
}
