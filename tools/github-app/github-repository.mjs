import { REPOSITORY, SHA } from './constants.mjs';
import { ensure, fail } from './guards.mjs';
import { verifyBotCommit, verifyPr } from './verification.mjs';

export class GitHubRepository {
  constructor({ client, workspace }) {
    this.client = client;
    this.workspace = workspace;
  }

  async remoteRef(token, branch) {
    const value = await this.client.request('GET',
      '/repos/' + REPOSITORY + '/git/ref/heads/' + encodeURIComponent(branch), token, undefined, { missing: true });
    if (!value) return null;
    ensure(value.ref === 'refs/heads/' + branch && SHA.test(value.object?.sha)
      && value.object.type === 'commit', 'REF_RACE');
    return value.object.sha;
  }

  async remoteState(token, snapshot) {
    const repo = await this.client.request('GET', '/repos/' + REPOSITORY, token);
    ensure(repo.full_name === REPOSITORY && repo.default_branch === 'main', 'REPOSITORY_MISMATCH');
    const main = await this.remoteRef(token, 'main');
    ensure(main === snapshot.base, 'STALE_PARENT');
    const branch = await this.remoteRef(token, snapshot.branch);
    ensure(branch === null ? snapshot.head === main : branch === snapshot.head, 'STALE_PARENT');
    const parent = await this.client.request('GET', '/repos/' + REPOSITORY + '/commits/' + snapshot.head, token);
    ensure(parent.sha === snapshot.head && SHA.test(parent.commit?.tree?.sha), 'STALE_PARENT');
    if (snapshot.head !== main) verifyBotCommit(parent, snapshot.head);
    await this.workspace.git(['merge-base', '--is-ancestor', snapshot.base, snapshot.head]);
    return { main, branch, parentTree: parent.commit.tree.sha };
  }

  async recheckRemote(token, snapshot, expectedBranch) {
    ensure(await this.remoteRef(token, 'main') === snapshot.base
      && await this.remoteRef(token, snapshot.branch) === expectedBranch, 'REF_RACE');
  }

  async existingPr(token, branch) {
    const pulls = await this.client.request('GET', '/repos/' + REPOSITORY
      + '/pulls?state=open&base=main&head=' + encodeURIComponent('Eneru:' + branch), token);
    ensure(Array.isArray(pulls) && pulls.length <= 1, 'PR_FAILED');
    if (!pulls.length) return null;
    verifyPr(pulls[0], branch);
    return pulls[0];
  }

  verifyPr(pr, branch, commit) { return verifyPr(pr, branch, commit); }

  async publishRef(token, snapshot, previous, commit) {
    if (previous === null) {
      await this.client.request('POST', '/repos/' + REPOSITORY + '/git/refs', token,
        { ref: 'refs/heads/' + snapshot.branch, sha: commit });
    } else {
      await this.client.request('PATCH', '/repos/' + REPOSITORY + '/git/refs/heads/'
        + encodeURIComponent(snapshot.branch), token, { sha: commit, force: false });
    }
    ensure(await this.remoteRef(token, snapshot.branch) === commit, 'REF_RACE', {
      branch: snapshot.branch, commit, branchPublished: true,
    });
  }

  async readyPr(token, { pr, snapshot, commit, title, body, updatePr = false, beforeUpdate }) {
    const reusedPr = Boolean(pr);
    try {
      if (!pr) {
        pr = await this.client.request('POST', '/repos/' + REPOSITORY + '/pulls', token,
          { title, body: body.text, head: snapshot.branch, base: 'main', draft: false });
      }
      pr = await this.client.request('GET', '/repos/' + REPOSITORY + '/pulls/' + pr.number, token);
      verifyPr(pr, snapshot.branch, commit);
      if (reusedPr && updatePr) {
        ensure(typeof beforeUpdate === 'function', 'PR_FAILED');
        await beforeUpdate();
        await this.client.request('PATCH', '/repos/' + REPOSITORY + '/pulls/' + pr.number, token,
          { title, body: body.text });
        pr = await this.client.request('GET', '/repos/' + REPOSITORY + '/pulls/' + pr.number, token);
        verifyPr(pr, snapshot.branch, commit);
        ensure(pr.title === title && pr.body === body.text, 'PR_FAILED');
      }
      return pr;
    } catch {
      fail('PR_FAILED', { branch: snapshot.branch, commit, tree: snapshot.tree, branchPublished: true });
    }
  }

  async requestReview(token, number) {
    try {
      await this.client.request('POST', '/repos/' + REPOSITORY + '/pulls/' + number + '/requested_reviewers',
        token, { reviewers: ['Eneru'] });
      return true;
    } catch {
      // A valid PR remains available; report the review-request limitation explicitly.
      return false;
    }
  }
}
