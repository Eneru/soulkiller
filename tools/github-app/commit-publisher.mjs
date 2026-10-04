import { REPOSITORY, SHA, MAX_BLOB } from './constants.mjs';
import { ensure } from './guards.mjs';
import { blobHash } from './crypto.mjs';
import { verifyBotCommit } from './verification.mjs';

export class CommitPublisher {
  constructor({ client, workspace }) {
    this.client = client;
    this.workspace = workspace;
  }

  async createVerifiedCommit(token, snapshot, parentTree, message) {
    const entries = new Map(snapshot.entries.map((entry) => [entry.path, entry]));
    const treeEntries = [];
    for (const file of snapshot.changes) {
      const entry = entries.get(file);
      if (!entry) {
        treeEntries.push({ path: file, mode: '100644', type: 'blob', sha: null });
        continue;
      }
      const bytes = await this.workspace.git(['cat-file', 'blob', entry.sha]);
      ensure(bytes.length <= MAX_BLOB, 'BAD_PATH');
      const localBlob = blobHash(bytes);
      ensure(localBlob === entry.sha, 'TREE_MISMATCH');
      const blob = await this.client.request('POST', '/repos/' + REPOSITORY + '/git/blobs', token,
        { content: bytes.toString('base64'), encoding: 'base64' });
      ensure(blob.sha === entry.sha, 'TREE_MISMATCH');
      treeEntries.push({ path: file, mode: entry.mode, type: 'blob', sha: blob.sha });
    }
    const tree = await this.client.request('POST', '/repos/' + REPOSITORY + '/git/trees', token,
      { base_tree: parentTree, tree: treeEntries });
    ensure(tree.sha === snapshot.tree, 'TREE_MISMATCH');
    const created = await this.client.request('POST', '/repos/' + REPOSITORY + '/git/commits', token,
      { message, tree: tree.sha, parents: [snapshot.head] });
    ensure(SHA.test(created.sha), 'COMMIT_UNVERIFIED');
    ensure(created.tree?.sha === snapshot.tree && created.parents?.length === 1
      && created.parents[0].sha === snapshot.head, 'TREE_MISMATCH');
    ensure(created.verification?.verified === true && created.verification.reason === 'valid',
      'COMMIT_UNVERIFIED', { commit: created.sha });
    const commit = created.sha;
    const inspected = await this.client.request('GET', '/repos/' + REPOSITORY + '/commits/' + commit, token);
    verifyBotCommit(inspected, commit, snapshot.tree, snapshot.head);
    return commit;
  }
}
