import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import test from 'node:test';
import { CiWorkflowFixture } from './helpers/ci-workflow-fixture.mjs';

const pr = { eventName: 'pull_request', baseRef: 'main', ref: 'refs/pull/42/merge', refType: 'branch', deleted: false };
const tag = { eventName: 'push', ref: 'refs/tags/v1.2.3', refType: 'tag', deleted: false };
const accepted = [
  ['main pull request', pr], ['stable v tag', tag],
  ['bare stable tag', { ...tag, ref: 'refs/tags/1.2.3' }],
  ['prerelease/build tag', { ...tag, ref: 'refs/tags/v1.2.3-rc.1+build.007' }],
];
for (const [name, context] of accepted) {
  test('parsed workflow executes build and canonical checks for ' + name, (t) => {
    // Arrange
    const fixture = new CiWorkflowFixture(t);
    // Act
    const result = fixture.run(context);
    // Assert
    assert.equal(result.eligible, 'true');
    assert.equal(result.calls.length, 2);
    assert.equal(result.calls.at(0), 'build --tag soulkiller-quality .devcontainer');
    assert.match(result.calls.at(1), /^run --rm --init --mount /);
    assert.match(result.calls.at(1), /target=\/workspaces\/soulkiller,readonly/);
    assert.match(result.calls.at(1), /soulkiller-quality bash tools\/checks\/check.sh all$/);
  });
}
const rejected = [
  ['main push', { ...tag, ref: 'refs/heads/main', refType: 'branch' }, 'unsubscribed'],
  ['other PR target', { ...pr, baseRef: 'develop' }, 'unsubscribed'],
  ['manual dispatch', { ...pr, eventName: 'workflow_dispatch' }, 'unsubscribed'],
  ['unshaped tag', { ...tag, ref: 'refs/tags/release-latest' }, 'unsubscribed'],
  ['deleted tag', { ...tag, deleted: true }, 'deleted'],
  ['leading-zero tag', { ...tag, ref: 'refs/tags/v01.2.3' }, 'guarded'],
  ['invalid numeric prerelease', { ...tag, ref: 'refs/tags/v1.2.3-01' }, 'guarded'],
  ['multiple build markers', { ...tag, ref: 'refs/tags/v1.2.3+a+b' }, 'guarded'],
  ['shell-looking tag', { ...tag, ref: 'refs/tags/v1.2.3;false' }, 'guarded'],
];
for (const [name, context, reason] of rejected) {
  test('parsed workflow skips heavy work for ' + name, (t) => {
    // Arrange
    const fixture = new CiWorkflowFixture(t);
    // Act
    const result = fixture.run(context);
    // Assert
    assert.equal(result.reason, reason);
    assert.deepEqual(result.calls, []);
    if (reason === 'guarded') assert.equal(result.eligible, 'false');
  });
}

test('workflow preserves bounded read-only checkout and required foundation job', (t) => {
  // Arrange
  const fixture = new CiWorkflowFixture(t);
  // Act
  const { workflow } = fixture;
  const job = workflow.jobs.foundation;
  const checkout = job.steps.at(0);
  // Assert
  assert.deepEqual(Object.keys(workflow.on).sort(), ['pull_request', 'push']);
  assert.deepEqual(workflow.on.pull_request.branches, ['main']);
  assert.equal(workflow.on.push.branches, undefined);
  assert.deepEqual(workflow.permissions, { contents: 'read' });
  assert.equal(workflow.concurrency['cancel-in-progress'], true);
  assert.equal(job['timeout-minutes'], 15);
  assert.equal(job['runs-on'], 'ubuntu-24.04');
  assert.equal(checkout.uses, 'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1');
  assert.equal(checkout.with['persist-credentials'], false);
  assert.equal(checkout.with['fetch-depth'], 0);
});

test('event command substitution remains inert environment data', (t) => {
  // Arrange
  const fixture = new CiWorkflowFixture(t);
  const marker = resolve(fixture.directory, 'injected');
  const context = { ...tag, ref: 'refs/tags/v1.2.3$(touch ' + marker + ')' };
  // Act
  const result = fixture.run(context);
  // Assert
  assert.equal(result.eligible, 'false');
  assert.deepEqual(result.calls, []);
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Marker is confined to this synthetic fixture's owned container-local temporary directory.
  assert.equal(existsSync(marker), false);
});
