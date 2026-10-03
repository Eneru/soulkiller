import { lstatSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const maintainedShellSources = Object.freeze([
  'tools/checks/check.sh',
  'tools/checks/install-hooks.sh',
  '.githooks/pre-commit',
]);

function count(value) {
  if (!(typeof value === 'number' || (typeof value === 'string' && /^\d+$/.test(value)))) {
    throw new Error('Invalid executable line count');
  }
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 0) throw new Error('Invalid executable line count');
  return parsed;
}

export function summarizeCoverage(report, repositoryRoot, minimum = 70) {
  if (!report || !Array.isArray(report.files) || !Number.isFinite(minimum) || minimum < 70 || minimum > 100) {
    throw new Error('Invalid coverage report or threshold');
  }
  return maintainedShellSources.map((file) => {
    const expected = resolve(repositoryRoot, file);
    const matches = report.files.filter((entry) => entry && entry.file === expected);
    if (matches.length !== 1) throw new Error('Missing or duplicate maintained source');
    const entry = matches.at(0);
    const covered = count(entry.covered_lines);
    const total = count(entry.total_lines);
    if (!total || covered > total) throw new Error('Invalid executable line denominator');
    const percentage = covered * 100 / total;
    const declared = Number(entry.percent_covered);
    if (!Number.isFinite(declared) || Math.abs(declared - percentage) > 0.011) {
      throw new Error('Coverage percentage does not match measured counts');
    }
    if (percentage < minimum) throw new Error('Maintained shell source is below the coverage threshold');
    return { file, covered, total, percentage };
  });
}

export function validateCoverageFile(filePath, repositoryRoot) {
  const reportPath = resolve(filePath);
  if (!reportPath.startsWith('/tmp/')) throw new Error('Coverage report must remain container-local');
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- Only a container-local generated report is inspected; no contents are logged.
  const stat = lstatSync(reportPath);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 1024 * 1024) throw new Error('Unsafe coverage report');
  // eslint-disable-next-line security/detect-non-literal-fs-filename -- The preceding check confines this read to the generated container-local report.
  const report = JSON.parse(readFileSync(reportPath, 'utf8'));
  return summarizeCoverage(report, repositoryRoot);
}

export function main(args, output = console) {
  try {
    if (args.length !== 1) throw new Error('Provide one generated coverage report');
    const root = resolve(import.meta.dirname, '../..');
    for (const result of validateCoverageFile(args.at(0), root)) {
      output.log('Shell source line coverage: ' + result.file + ': ' + result.percentage.toFixed(2) + '% (' + result.covered + '/' + result.total + ')');
    }
    return 0;
  } catch {
    output.error('Shell coverage validation failed: report missing, invalid or below 70%.');
    return 1;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = main(process.argv.slice(2));
}
