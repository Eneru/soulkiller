import assert from 'node:assert/strict';
import test from 'node:test';
import { isEligibleEvent } from '../ci-policy.mjs';

const pullRequest = { eventName: 'pull_request', baseRef: 'main', ref: 'refs/pull/42/merge', refType: 'branch', deleted: false };
const tagPush = { eventName: 'push', baseRef: '', ref: 'refs/tags/v1.2.3', refType: 'tag', deleted: false };
const cases = [
  ['main pull request', pullRequest, true],
  ['bare tag', { ...tagPush, ref: 'refs/tags/1.2.3' }, true],
  ['prerelease tag', { ...tagPush, ref: 'refs/tags/v1.2.3-rc.1+build.01' }, true],
  ['other PR base', { ...pullRequest, baseRef: 'develop' }, false],
  ['missing PR base', { ...pullRequest, baseRef: undefined }, false],
  ['wrong PR ref type', { ...pullRequest, refType: 'tag' }, false],
  ['head-only PR ref', { ...pullRequest, ref: 'refs/pull/42/head' }, false],
  ['PR ref trailing newline', { ...pullRequest, ref: 'refs/pull/42/merge\n' }, false],
  ['zero PR number', { ...pullRequest, ref: 'refs/pull/0/merge' }, false],
  ['main branch push', { ...tagPush, ref: 'refs/heads/main', refType: 'branch' }, false],
  ['feature branch push', { ...tagPush, ref: 'refs/heads/feature/1.2.3', refType: 'branch' }, false],
  ['tag-looking branch', { ...tagPush, refType: 'branch' }, false],
  ['missing tag ref type', { ...tagPush, refType: undefined }, false],
  ['tag without ref prefix', { ...tagPush, ref: 'v1.2.3' }, false],
  ['malformed version tag', { ...tagPush, ref: 'refs/tags/v01.2.3' }, false],
  ['deleted tag', { ...tagPush, deleted: true }, false],
  ['missing deletion flag', { ...tagPush, deleted: undefined }, false],
  ['string deletion flag', { ...tagPush, deleted: 'false' }, false],
  ['manual event', { ...pullRequest, eventName: 'workflow_dispatch' }, false],
  ['privileged PR event', { ...pullRequest, eventName: 'pull_request_target' }, false],
  ['missing event', { ...pullRequest, eventName: undefined }, false],
  ['missing ref', { ...pullRequest, ref: undefined }, false],
  ['null context', null, false], ['undefined context', undefined, false],
  ['primitive context', 'pull_request', false],
];

for (const [name, input, expected] of cases) {
  test('event eligibility: ' + name, () => {
    // Arrange
    const context = input;
    // Act
    const eligible = isEligibleEvent(context);
    // Assert
    assert.equal(eligible, expected);
  });
}
