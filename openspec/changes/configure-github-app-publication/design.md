# Design

## Context and authorization

The maintainer installed the private GitHub App and generated its key, then
requested this implementation and PR. Public App ID/name are configuration;
the PEM is a private runtime input in an ignored Soulkiller subdirectory.
The project language remains English. Commands run in the existing devcontainer.

## Decisions

Use Node.js 24 built-ins for RSA JWT signing, HTTPS fetch, files and Git plumbing.
This is development tooling, not selection of the application language. Pin the
GitHub REST API version, time out requests, disallow redirects and redact errors.
Use fixed GitHub/repository/App identities; discover and validate the installation
rather than accepting a broad token or maintainer-authentication fallback.
Mint a token constrained to Soulkiller and necessary permissions, retain it only
in memory, and attempt revocation in a finally block.

Freeze the Git index in container-local temporary storage, scan raw blob bytes
without checkout/smudge filters and bind metadata checks to captured input bytes.
Use no-follow file handles and descriptor/path checks to prevent key/body path
substitution during validation. Use blobs (base64 for binary files) and trees preserving
modes/deletions. Require a clean unstaged workspace, a permitted current branch,
unchanged LICENSE, safe paths and known remote parent. Reject stale main/branch
state rather than force updating. Run explicit secret scans including the PR body,
OpenSpec validation and whitespace checks before publication. Git hooks alone
cannot guard API-created commits.

Create a commit through the Git Database API without custom author, committer or
signature fields. Check the returned tree/parent and GitHub's Verified result and
App bot author before exposing a branch ref. Live GitHub.com inspection showed
a valid signature with author `eneru-soulkiller-agent[bot]` and platform committer
`web-flow`, raw name `GitHub`, email `noreply@github.com`. Require this exact
committer contract as well; it is the observed integration behavior, not a claim
that every GitHub deployment or endpoint uses these fields. Never update main, tags, settings or
merge endpoints. Ref updates use force=false. The selected REST ref endpoint lacks an expected-SHA compare-and-swap
parameter: read again before update and verify afterward, report a concurrent
change rather than claiming atomicity. Do not discard divergent local history.

Fetch the accepted remote commit and move only the local working ref from its
expected old SHA after verifying the staged tree, leaving files/index unchanged.
Create or reuse one ready PR against main; report a branch published without a PR
if that later step fails. Request Eneru's review. Never approve/merge as Eneru.
CODEOWNERS is a file-level review request; only a maintainer can enforce rules.

## Quality and execution

Install pinned scanner binaries/checksums in the image; run native commands without
a Docker socket. Add ESLint with security-oriented rules and a dependency audit.
Measure all maintained publisher and coverage-validator JavaScript with Node's
built-in test coverage, at least 70% lines; report branches and functions. Shell
integration tests exercise hook installation, partial staging, synthetic secrets
and missing tools. kcov 43 measures each maintained shell helper with a separate
70% executable-line gate. Its Bash tracing runs without additional Docker
privileges. Build kcov from a checked source archive in a separate image stage;
compiler tools and Python used by that build do not enter the runtime image.
Exclude test harnesses, configuration and third-party tooling from source coverage;
require canonical source entries and fail on absent or inconsistent reports.
Use a bounded unprivileged pull_request/main Actions lane without App keys,
credential persistence or privileged PR execution. Local hooks are explicit and
preserve existing hooks/configuration. Hadolint editor integration uses the same
binary/configuration; CLI checks do not prove editor UI behavior.

## Risks, recovery and exclusions

A compromised App key can use the permissions granted by GitHub; this CLI is not
a replacement for repository protection. Keep key backups private, rotate/revoke
through the maintainer's App settings, and never put it into Actions for routine
checks. Runtime network/signature/permission failure blocks delivery. Tests use
generated ephemeral keys and fake APIs, never real credentials.
The CLI cannot make multi-step API publication transactional; unreachable Git
objects or a branch without a PR can remain after failure. Recovery inspects
remote objects and resumes safely, with no cleanup or force push.
No paid model calls, application features, web DAST target, site deployment,
benchmark claim or settings change belongs to this implementation.
