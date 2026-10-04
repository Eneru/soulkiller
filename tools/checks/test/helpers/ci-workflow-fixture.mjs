/* eslint-disable security/detect-non-literal-fs-filename -- Paths are owned container-local temporary fixtures or the fixed repository workflow. */
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { isSelected, isSubscribed, workflowEnvironment } from './ci-workflow-inputs.mjs';

const require = createRequire('/opt/openspec/package.json');
const { parse } = require('yaml');

export class CiWorkflowFixture {
  constructor(cleanup) {
    this.root = resolve(import.meta.dirname, '../../../..');
    this.workflow = parse(readFileSync(resolve(this.root, '.github/workflows/quality.yml'), 'utf8'));
    this.directory = mkdtempSync('/tmp/soulkiller-ci-policy-');
    this.output = resolve(this.directory, 'outputs');
    this.log = resolve(this.directory, 'docker-calls');
    cleanup.after(() => rmSync(this.directory, { recursive: true, force: true }));
    writeFileSync(this.output, '');
    writeFileSync(this.log, '');
    writeFileSync(resolve(this.directory, 'docker'), '#!/usr/bin/env bash\nset -euo pipefail\nprintf \'%s\\n\' "$*" >> "$CI_TEST_DOCKER_LOG"\n', { mode: 0o755 });
  }

  run(context) {
    const job = this.workflow.jobs.foundation;
    if (!isSubscribed(this.workflow, context)) return { reason: 'unsubscribed', calls: [] };
    if (job.if !== "github.event_name != 'push' || !github.event.deleted") throw new Error('Job deletion guard changed');
    if (context.eventName === 'push' && context.deleted) return { reason: 'deleted', calls: [] };
    const gate = job.steps.find((step) => step.id === 'eligibility');
    const environment = {
      ...process.env,
      PATH: this.directory + ':' + process.env.PATH,
      GITHUB_WORKSPACE: this.root,
      GITHUB_OUTPUT: this.output,
      CI_TEST_DOCKER_LOG: this.log,
    };
    this.runStep(gate, environment, context);
    const output = readFileSync(this.output, 'utf8');
    if (!/^eligible=(true|false)\n$/.test(output)) throw new Error('Unexpected gate output');
    const eligible = output.trim().split('=').at(1);
    for (const step of job.steps.filter((candidate) => candidate.run && candidate.id !== 'eligibility')) {
      if (isSelected(step.if, eligible)) this.runStep(step, environment, context);
    }
    return { reason: 'guarded', eligible, calls: readFileSync(this.log, 'utf8').trim().split('\n').filter(Boolean) };
  }

  runStep(step, environment, context) {
    if (step.run.includes('${{')) throw new Error('Event expressions must not appear in shell scripts');
    const result = spawnSync('bash', ['-e', '-c', step.run], {
      cwd: this.root,
      env: { ...environment, ...workflowEnvironment(step.env, context) },
      encoding: 'utf8', timeout: 10000,
    });
    if (result.status !== 0) throw new Error('Synthetic workflow step failed: ' + result.stderr);
  }
}
