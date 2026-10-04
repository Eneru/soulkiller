import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Publisher } from './publisher.mjs';
import { PublicationError } from './errors.mjs';
import { ReviewReplyService } from './review-replies.mjs';

export const HELP = [
  'Soulkiller GitHub App publication (run inside its devcontainer).',
  'check [--execute] [--key-file ignored-path]',
  'publish --body-file ignored-path --title text [--message text] [--update-pr] [--execute] [--key-file ignored-path]',
  'verify --number PR-number [--execute] [--key-file ignored-path]',
  'reply --number PR-number --comment comment-ID --body-file ignored-path [--execute] [--key-file ignored-path]',
  'Without --execute all commands are offline dry runs. No merge/settings operations exist.',
].join('\n');

export function parseArgs(args) {
  if (args.length === 0 || (args.length === 1 && ['--help', '-h'].includes(args[0]))) return { help: true };
  const [command, ...rest] = args;
  if (!['check', 'publish', 'verify', 'reply'].includes(command)) throw new PublicationError('BAD_ARGUMENT');
  const options = {};
  const names = new Map(Object.entries({ '--key-file': 'keyFile', '--body-file': 'bodyFile', '--title': 'title',
    '--message': 'message', '--number': 'number', '--comment': 'comment' }));
  for (let index = 0; index < rest.length; index += 1) {
    const flag = rest.at(index);
    if (flag === '--execute') {
      if (options.execute) throw new PublicationError('BAD_ARGUMENT');
      options.execute = true;
      continue;
    }
    if (flag === '--update-pr') {
      if (options.updatePr) throw new PublicationError('BAD_ARGUMENT');
      options.updatePr = true;
      continue;
    }
    const name = names.get(flag);
    if (!name || Object.hasOwn(options, name) || !rest.at(index + 1) || rest.at(index + 1).startsWith('--')) {
      throw new PublicationError('BAD_ARGUMENT');
    }
    // eslint-disable-next-line security/detect-object-injection -- name comes only from the fixed flag allowlist; prototype keys cannot enter it.
    options[name] = rest.at(++index);
  }
  const allowed = command === 'publish' ? ['execute', 'updatePr', 'keyFile', 'bodyFile', 'title', 'message']
    : command === 'reply' ? ['execute', 'keyFile', 'bodyFile', 'number', 'comment']
      : command === 'verify' ? ['execute', 'keyFile', 'number'] : ['execute', 'keyFile'];
  if (Object.keys(options).some((name) => !allowed.includes(name))) throw new PublicationError('BAD_ARGUMENT');
  if (command === 'publish' && (!options.bodyFile || !options.title)) throw new PublicationError('BAD_ARGUMENT');
  if (command === 'reply' && !options.bodyFile) throw new PublicationError('BAD_ARGUMENT');
  if (command === 'reply') {
    if (!/^[1-9]\d*$/u.test(options.comment || '')) throw new PublicationError('BAD_ARGUMENT');
    options.comment = Number(options.comment);
    if (!Number.isSafeInteger(options.comment)) throw new PublicationError('BAD_ARGUMENT');
  }
  if (command === 'verify' || command === 'reply') {
    if (!/^[1-9]\d*$/u.test(options.number || '')) throw new PublicationError('BAD_ARGUMENT');
    options.number = Number(options.number);
    if (!Number.isSafeInteger(options.number)) throw new PublicationError('BAD_ARGUMENT');
  }
  return { command, options };
}

export async function main(args, {
  publisher = new Publisher(), replyService = new ReviewReplyService(publisher),
  output = console.log, errorOutput = console.error,
} = {}) {
  try {
    const parsed = parseArgs(args);
    if (parsed.help) {
      output(HELP);
      return 0;
    }
    const result = parsed.command === 'reply'
      ? await replyService.reply(parsed.options)
      : await publisher[parsed.command](parsed.options);
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
