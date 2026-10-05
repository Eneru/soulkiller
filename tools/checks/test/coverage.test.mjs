import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import test from 'node:test';
import { main, maintainedShellSources, summarizeCoverage, validateCoverageFile } from '../coverage.mjs';

const root = resolve(import.meta.dirname, '../../..');
const report = (covered = 80) => ({files: maintainedShellSources.map((file) => ({
  file: resolve(root, file), covered_lines: String(covered), total_lines: '100', percent_covered: covered.toFixed(2),
}))});

test('each maintained source passes at or above the floor independently', () => {
  assert.equal(summarizeCoverage(report(), root).length, 4);
  assert.equal(summarizeCoverage(report(70), root).at(0).percentage, 70);
  assert.throws(() => summarizeCoverage(report(69), root), /below/);
  const mixed = report(); mixed.files.at(1).covered_lines = '69'; mixed.files.at(1).percent_covered = '69.00';
  assert.throws(() => summarizeCoverage(mixed, root), /below/);
  assert.throws(() => summarizeCoverage(report(), root, 90), /below/);
});

test('missing, duplicate or foreign paths cannot substitute for maintained sources', () => {
  const missing = report(); missing.files.pop();
  assert.throws(() => summarizeCoverage(missing, root), /Missing/);
  const duplicate = report(); duplicate.files.push({...duplicate.files.at(0)});
  assert.throws(() => summarizeCoverage(duplicate, root), /duplicate/);
  const foreign = report(); foreign.files.at(0).file = '/tmp/copied/tools/checks/check.sh';
  assert.throws(() => summarizeCoverage(foreign, root), /Missing/);
  const extra = report(); extra.files.push({file:'/tmp/copied/check.sh',covered_lines:'0',total_lines:'100',percent_covered:'0'});
  assert.equal(summarizeCoverage(extra, root).length, 4);
});

test('invalid denominators, percentages and weakened thresholds fail closed', () => {
  for (const value of ['', -1, 0.1, '1.5', null, Number.MAX_SAFE_INTEGER + 1]) {
    const invalid = report(); invalid.files.at(0).covered_lines = value;
    assert.throws(() => summarizeCoverage(invalid, root), /Invalid/);
  }
  for (const total of ['0', '79']) {
    const invalid = report(); invalid.files.at(0).total_lines = total;
    assert.throws(() => summarizeCoverage(invalid, root), /denominator/);
  }
  for (const percent of ['81', 'not a number']) {
    const invalid = report(); invalid.files.at(0).percent_covered = percent;
    assert.throws(() => summarizeCoverage(invalid, root), /percentage/);
  }
  for (const threshold of [0, 69, 101, NaN]) assert.throws(() => summarizeCoverage(report(), root, threshold), /Invalid/);
  for (const invalid of [null, {}, {files:null}]) assert.throws(() => summarizeCoverage(invalid, root), /Invalid/);
});

test('generated report files and CLI assertions handle success and unsafe inputs without leaking contents', () => {
  const directory = mkdtempSync(resolve(tmpdir(), 'soulkiller-coverage-test-'));
  const file = resolve(directory, 'coverage.json');
  const link = resolve(directory, 'report-link.json');
  const lines = [];
  const output = {log: (line) => lines.push(line), error: (line) => lines.push(line)};
  try {
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Test writes only within its owned container-local temporary fixture.
    writeFileSync(file, JSON.stringify(report()));
    assert.equal(validateCoverageFile(file, root).length, 4);
    assert.equal(main([file], output), 0);
    assert.equal(lines.length, 4);
    assert.equal(main([], output), 1);
    assert.throws(() => validateCoverageFile('/workspaces/forbidden.json', root), /container-local/);
    assert.throws(() => validateCoverageFile(resolve(directory, 'missing.json'), root));
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Both paths are generated inside the owned temporary fixture.
    symlinkSync(file, link);
    assert.throws(() => validateCoverageFile(link, root), /Unsafe/);
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Oversized synthetic input remains inside the owned temporary fixture.
    writeFileSync(file, 'x'.repeat(1024 * 1024 + 1));
    assert.throws(() => validateCoverageFile(file, root), /Unsafe/);
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- Malformed input is synthetic and confined to this owned temporary fixture.
    writeFileSync(file, 'PRIVATE_SYNTHETIC_REPORT_CONTENT');
    assert.equal(main([file], output), 1);
    assert.ok(lines.every((line) => !line.includes('PRIVATE_SYNTHETIC_REPORT_CONTENT')));
  } finally {
    rmSync(directory, {recursive:true, force:true});
  }
});
