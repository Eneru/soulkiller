## User journey
From an offline devcontainer, run --run-id demo-001 processes the existing
example and prints results. show --run-id demo-001 reads them later without
parsing sources. Repeating run fails without replacing the first result.
Connected run refuses with an actionable offline-launch message before writes.

## Implementation
Use accepted snapshots once with CorpusRunner. Add an optional completion
callback, defaulting to None for existing callers, invoked before scheduling
the next worker. A saved-run writer owns the RunStore and records returned rows
with existing codecs. Persist a version-2 manifest synthesized from accepted
metadata as record manifest; fixture-001..032 hold existing codec bytes; summary
holds version/status/observed bytes. Maximum34 records retains existing budgets.
Validate the synthesized manifest before creating output.

On caught cancellation/cleanup, save only rows not already published and final
status; failures to persist stop work and retain earlier state, never cleanup.
SIGKILL/power loss can leave no summary: inspection says incomplete, unknown
rather than inventing a completed run or zero-byte unfinished observation.
A callback interrupted during publication may leave a poisoned handle; no retry
or successful checkpoint guarantee is claimed.

Read stored metadata with existing strict manifest parsers, bound all JSON,
validate summary types and row order/reasons/aggregate when summary exists.
Missing records with a final summary fail; without it show unavailable rows.
Corrupt records fail rather than silently disappearing.
Source directory must still exist for the existing source-disjoint store check;
source files need not exist or match a current manifest to inspect saved bytes.
Plain display escapes terminal control characters; JSON escapes exact evidence.

## Quality and delivery
Document every new/changed function. Independent tests cover run/show, actual
offline subprocesses, connected refusal, restarts, collision, corruption,
cancellation and persistence failure. Existing editor/checks cover Python; CI triggers remain unchanged. The required
security refresh below rebuilds the image without adding dependencies. Run all canonical gates and offline suite,
strict OpenSpec, documentation links, LICENSE and whitespace checks.

The default demo is experiments/text-pdf/examples/mixed: five frozen invented
TXT/PDF fixtures (including invalid UTF-8), with independent reference facts.
The historical TXT-only corpus is preserved.

## Required security refresh
The first canonical audit on 2026-11-01 found 31 advisory entries across
certifi 2026.7.22, filelock 4.0.12 and pypdf 6.20.0. Verify primary PyPI metadata
and wheel hashes, then pin certifi 2026.10.18, filelock 4.2.1 and pypdf 6.21.4.
Preserve other resolved versions; rebuild and rerun gates. No advisory suppression.
Primary release metadata:
https://pypi.org/pypi/certifi/2026.10.18/json
https://pypi.org/pypi/filelock/4.2.1/json
https://pypi.org/pypi/pypdf/6.21.4/json

The next audit identified GHSA-g3hv-75wg-m249 in ESLint's minimatch 10 tree.
Current ESLint 10.14/config-array0.23.5 metadata still requires minimatch 10;
avoid npm's suggested forced downgrade to ESLint 4. Pin a temporary transitive
override to minimatch 11.0.1, whose Node engine supports the existing Node 24.
Rebuild and exercise actual ESLint + all tooling tests. Remove the override
when upstream natively accepts a patched range.
https://github.com/advisories/GHSA-g3hv-75wg-m249

Declare the two PDF example artifacts binary in Git attributes: their fixed-width
xref entries contain required padding, not source-code trailing whitespace.

## Hosted clean-build repair
Hosted run 41337284256 failed before tests: removed APT pins were hidden by local
cached layers. Current repository metadata requires ca-certificates
20260816ubuntu0.24.04.1, git 1:2.43.0-1ubuntu7.4 and xz/liblzma revision 0.4.
Update the matching family pins, check all pinned package availability and build
with --no-cache before claiming a fresh installation. No CI trigger is changed.

The complete availability check also found removed zlib runtime/dev revision 2.2;
align both pins to the available 2.3 revision before rebuilding.
