# Local quality checks

This foundation accompanies the GitHub App development tool and delivers part of
[issue #7](https://github.com/Eneru/soulkiller/issues/7). Run every command inside
the rebuilt devcontainer. It installs Gitleaks **8.30.1**, Hadolint **2.15.1**,
kcov **43**, ESLint **10.12.0**, `@eslint/js` **10.0.1** and `eslint-plugin-security` **4.2.0**.
The scanner downloads have explicit SHA-256 values for Linux amd64 and arm64;
npm tools use the [quality lockfile](../.devcontainer/quality/package-lock.json).
Kcov is built from a versioned, SHA-256-verified upstream source archive in a
separate build stage. Compilers, CMake and its build-only Python dependency do
not enter the development image. Bash tracing runs as the non-root user without
additional Docker capabilities or relaxed seccomp.
ARM64 pinning is not evidence that ARM64 runtime checks were executed.

## Canonical commands

From the repository root:

```sh
bash tools/checks/check.sh secrets-staged
bash tools/checks/check.sh secrets
bash tools/checks/check.sh docker
bash tools/checks/check.sh static
bash tools/checks/check.sh audit
bash tools/checks/check.sh selftest
bash tools/checks/check.sh coverage
npm --prefix tools/github-app test
bash tools/checks/check.sh all
```

- `secrets-staged` materializes raw Git index blobs without checkout filters in container-internal
  temporary storage and scans it. It preserves partial staging and rejects
  indexed symlinks/submodules rather than following them. Replacement objects
  are disabled, a supplied frozen index is honored, and an index change fails
  the scan.
- `secrets` also scans the tracked diff against HEAD. Untracked files must be
  staged before committing or publication; ignored local directories are not
  recursively scanned.
- `docker` checks applicable tracked and non-ignored Dockerfiles with Hadolint.
  `static` adds ESLint's recommended and security-oriented rules for tooling.
  Scanner findings and execution errors fail the command.
- `audit` queries the npm advisory service for the locked quality dependencies
  and publisher manifest. Any reported severity fails the gate; it requires
  registry connectivity and uses a bounded request timeout.
- `selftest` creates isolated synthetic repositories inside the container's
  temporary directory. It checks hook setup/preservation, partial staging,
  synthetic secrets, smudge-filter bypass attempts, tool failures, path confinement and Dockerfile rejection.
  It does not install hooks or modify Git configuration in Soulkiller itself.
- `coverage` runs the synthetic checks under kcov PS4 tracing and requires at
  least **70% of instrumented executable lines for each maintained Bash source**:
  `check.sh`, `install-hooks.sh` and `.githooks/pre-commit`. The report must contain
  each exact canonical source path, valid counts and matching percentages.
  Temporary fixture copies do not replace maintained sources or inflate the
  result. The Node report validator has separate positive, threshold-failure,
  missing-source and malformed-report tests with its own **70% line-coverage gate**.
- The publisher's test command measures maintained publisher JavaScript with
  Node's built-in coverage and enforces at least **70% line coverage**. Test
  harnesses (`selftest.sh`, `coverage.sh` and test files), vendor packages and
  declarative configuration are excluded because they provide synthetic test
  execution or configuration rather than the maintained publication/scanning
  behavior. Security-critical scanners, hook setup and the report validator
  remain measured; Markdown and absent application code receive no percentage.
- `all` runs those checks, shell/helper/publisher tests and coverage, strict OpenSpec and both
  unstaged/staged whitespace checks. Set `SOULKILLER_CHECK_BASE` to an existing
  40-character base commit SHA to add a commit-range scan.

Establish and review a full-history baseline explicitly:

```sh
bash tools/checks/check.sh secrets-history
bash tools/checks/check.sh secrets-changes BASE_COMMIT_SHA
```

Replace the placeholder with a real commit SHA. Range scans fail if the base
commit is unavailable; fetch sufficient history inside the container. A clean
scan is heuristic evidence, not proof that no secret exists.

## Publication metadata

The publisher invokes the fixed preflight before GitHub repository mutations.
The canonical command can also inspect an explicitly selected ignored PR body:

```sh
bash tools/checks/check.sh secrets-publication --body-file .soulkiller-local/pr-body.md
```

Its `--metadata-stdin` option also scans supplied title/commit-message text.
The publisher supplies those fields and the immutable captured body bytes
through stdin, so restoring a changed body file cannot substitute different
publication text. Diagnostics are withheld on
failure and the scanner uses redaction; it never copies the local directory,
App key or surrounding ignored files into a scan. Ambient scanner configuration,
ignore files and inline allow comments do not override the pinned default rules plus the explicit modern-installation-token rule.

The supplemental rule covers the `ghs_APPID_JWT` installation-token format
[documented by GitHub](https://docs.github.com/en/rest/apps/apps#create-an-installation-access-token-for-an-app);
synthetic staged/body/title/message cases verify it alongside the pinned defaults.

Git hooks can be bypassed and never run for GitHub API-created commits. Explicit
pre-publication scans and independent CI remain required.

## Explicit repository-local hooks

Installation is opt-in:

```sh
bash tools/checks/install-hooks.sh
git config --local --get core.hooksPath
```

The installer sets the local value to `.githooks` only when no unrelated hooks
or hooks-path setting would be displaced. It refuses to overwrite existing
hooks/configuration and is idempotent for Soulkiller's configured path. Resolve
existing integrations deliberately; do not delete another hook to make setup pass.
No global host configuration or automatic startup installation is used.

The pre-commit hook invokes `secrets-staged`. A missing scanner or synthetic
staged secret prevents a commit; unstaged content is not substituted for the index.

## Editor and CI

Rebuild/reopen to apply `exiasr.hadolint@1.1.2` on the container side. It calls
`/usr/local/bin/hadolint` with the same default rules and strict failure threshold
as the CLI. Verify diagnostics in VS Code separately: CLI success does not
establish that the extension UI has been exercised.

The [quality workflow](../.github/workflows/quality.yml) uses a full-SHA-pinned
checkout, full Git history, no persisted checkout credentials and
`contents: read`. It builds the same image and runs `all` with a read-only
repository mount on PRs and main; PR/main commit ranges avoid repeated baseline
history scans. Its single job has a 15-minute limit and cancels superseded runs.
No App key, token secret, Docker socket mount or privileged PR trigger is used.
Hosted Actions results must be reported after execution, separately from local
verification.

No application stack, coverage for absent application code, web DAST target,
performance benchmark or load-test result is supplied by this foundation.
Continue through the [quality plan](development-quality.md) as components arrive.
