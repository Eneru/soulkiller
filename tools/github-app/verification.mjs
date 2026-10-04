import { BOT, REPOSITORY, SHA, PLATFORM_COMMITTER } from './constants.mjs';
import { ensure } from './guards.mjs';

export function verifyBotCommit(commit, sha, tree, parent) {
  ensure(commit.sha === sha && commit.author?.login === BOT && commit.committer?.login === PLATFORM_COMMITTER.login
    && commit.commit?.committer?.name === PLATFORM_COMMITTER.name
    && commit.commit.committer.email === PLATFORM_COMMITTER.email
    && commit.commit?.verification?.verified === true
    && commit.commit.verification.reason === 'valid', 'COMMIT_UNVERIFIED',
    SHA.test(sha) ? { commit: sha } : {});
  if (tree) ensure(commit.commit.tree.sha === tree, 'TREE_MISMATCH');
  if (parent) ensure(commit.parents?.length === 1 && commit.parents[0].sha === parent, 'STALE_PARENT');
}

export function verifyPr(pr, branch, commit) {
  ensure(Number.isSafeInteger(pr.number) && pr.number > 0 && pr.user?.login === BOT
    && pr.state === 'open' && pr.draft === false && pr.base?.ref === 'main'
    && pr.base.repo?.full_name === REPOSITORY && pr.head?.ref === branch
    && pr.head.repo?.full_name === REPOSITORY
    && pr.html_url === 'https://github.com/' + REPOSITORY + '/pull/' + pr.number, 'PR_FAILED');
  if (commit) ensure(pr.head.sha === commit, 'PR_FAILED');
}
