import { runCommand } from '../../command.mjs';
import { Publisher } from '../../publisher.mjs';
import { TemporaryRepository } from './temporary-repository.mjs';
import { FakeGitHubServer } from './fake-github-server.mjs';
import { now } from './synthetic-data.mjs';

export async function createPublicationFixture(t, options) {
  const repository = await TemporaryRepository.create(t, options);
  const api = new FakeGitHubServer(repository);
  const calls = [];
  const command = async (file, args, passed) => {
    calls.push({file, args, options: passed});
    if (file !== 'git' || args.includes('fetch')) return Buffer.alloc(0);
    return runCommand(file, args, passed);
  };
  const publisher = new Publisher({root: repository.root, command, client: api, now: () => now});
  return {root: repository.root, repository, publisher, api, command, calls,
    files: publisher.files, workspace: publisher.workspace, gates: publisher.gates,
    git: repository.git, text: repository.text};
}
