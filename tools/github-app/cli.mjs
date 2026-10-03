import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Publisher, PublicationError } from './publisher.mjs';

export const HELP = [
  'Soulkiller GitHub App publication (run inside its devcontainer).',
  'check [--execute] [--key-file ignored-path]',
  'publish --body-file ignored-path --title text [--message text] [--execute] [--key-file ignored-path]',
  'verify --number PR-number [--execute] [--key-file ignored-path]',
  'Without --execute all commands are offline dry runs. No merge/settings operations exist.',
].join('\n');

export function parseArgs(args) {
  if (args.length === 0 || (args.length === 1 && ['--help', '-h'].includes(args[0]))) return { help: true };
  const [command, ...rest] = args;
  if (!['check', 'publish', 'verify'].includes(command)) throw new PublicationError('BAD_ARGUMENT');
  const options = {};
  const names = new Map(Object.entries({ '--key-file': 'keyFile', '--body-file': 'bodyFile', '--title': 'title',
    '--message': 'message', '--number': 'number' }));
  for (let index = 0; index < rest.length; index += 1) {
    const flag = rest.at(index);
    if (flag === '--execute') {
      if (options.execute) throw new PublicationError('BAD_ARGUMENT');
      options.execute = true;
      continue;
    }
    const name = names.get(flag);
    if (!name || Object.hasOwn(options, name) || !rest.at(index + 1) || rest.at(index + 1).startsWith('--')) {
      throw new PublicationError('BAD_ARGUMENT');
    }
    // eslint-disable-next-line security/detect-object-injection -- name comes only from the fixed flag allowlist; prototype keys cannot enter it.
    options[name] = rest.at(++index);
  }
  const allowed = command === 'publish' ? ['execute', 'keyFile', 'bodyFile', 'title', 'message']
    : command === 'verify' ? ['execute', 'keyFile', 'number'] : ['execute', 'keyFile'];
  if (Object.keys(options).some((name) => !allowed.includes(name))) throw new PublicationError('BAD_ARGUMENT');
  if (command === 'publish' && (!options.bodyFile || !options.title)) throw new PublicationError('BAD_ARGUMENT');
  if (command === 'verify') {
    if (!/^[1-9]\d*$/u.test(options.number || '')) throw new PublicationError('BAD_ARGUMENT');
    options.number = Number(options.number);
    if (!Number.isSafeInteger(options.number)) throw new PublicationError('BAD_ARGUMENT');
  }
  return { command, options };
}

export async function main(args, { publisher = new Publisher(), output = console.log, errorOutput = console.error } = {}) {
  try {
    const parsed = parseArgs(args);
    if (parsed.help) {
      output(HELP);
      return 0;
    }
    const result = await publisher[parsed.command](parsed.options);
    output(JSON.stringify(result, null, 2));
    return 0;
  } catch (error) {
    const safe = error instanceof PublicationError ? error : new PublicationError('COMMAND_FAILED');
    errorOutput(JSON.stringify({ error: safe.code, message: safe.message, ...safe.details }, null, 2));
    return 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  process.exitCode = await main(process.argv.slice(2));
}
