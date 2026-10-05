# GitHub App publication

Agent changes are published through the repository-local Node.js tool in the
devcontainer. The public configuration identifies App `eneru-soulkiller-agent`
(ID `5174172`), repository `Eneru/soulkiller`, and GitHub REST API version
`2026-03-10`. The expected author is
`eneru-soulkiller-agent[bot]`. GitHub signs the API-created commit and records
its platform committer: login `web-flow`, name `GitHub`, email
`noreply@github.com`. These fields were observed for this installation on
GitHub.com and are enforced by the tool; unexpected responses are refused.

The existing connector can authenticate as the maintainer, `Eneru`. It is not
a fallback for agent publication or human review. This tool creates ready PRs
for maintainer review; it cannot approve, merge, enable auto-merge, delete a
branch, publish a tag or change repository settings.

The maintainer reports, on 2026-10-04, that owner review, at least one approval
and signed commits are required. This is maintainer-reported configuration, not
a settings audit by this tool. Publication keeps those controls intact.

## Local preparation

Run every command below inside the Soulkiller devcontainer, with
`/workspaces/soulkiller` as the current directory. Only Soulkiller is mounted;
the Docker socket and host credential folders are not mounted.

The maintainer registers and installs the App on Soulkiller. The repository
permissions needed for publication are **Contents: read and write** and
**Pull requests: read and write**. Publishing staged changes under
`.github/workflows/` additionally requires **Workflows: read and write**.
Read-only authenticated checks request only Contents and Pull requests read
permissions. Metadata read is implicit. The tool requests no Issues,
Administration or organization permissions.

Keep the downloaded RSA private key in ignored
`.soulkiller-local/github-app/`. The default filename is
`.soulkiller-local/github-app/private-key.pem`; `--key-file` accepts another
ignored regular file inside that same directory. The current installation uses
`eneru-soulkiller-agent.2026-10-03.private-key.pem`; pass its relative path with
`--key-file` unless you deliberately use the documented default filename.
Do not copy the key into the
image, CI, a tracked file, a PR, a command argument containing key contents, or
logs. Permissions such as `0600` are useful inside Linux; Windows mount
permissions alone are not a confidentiality guarantee.

The App private key signs the short-lived authentication JWT. It is **not a Git
commit signing key**. The tool requests a short-lived installation token
explicitly restricted to Soulkiller and the command's necessary permissions,
validates the returned repository/permission/expiry scope, keeps it in memory,
and attempts revocation in a `finally` block. Revocation failures are reported;
the token also expires. JavaScript and cryptographic runtime memory cannot
provide a complete secret-zeroization guarantee.

Official background:
[installation authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation),
[installation token creation](https://docs.github.com/en/rest/apps/apps#create-an-installation-access-token),
and [bot commit verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification#signature-verification-for-bots).

## Prepare a reviewed change

Start from the current `origin/main` revision on a short-lived branch using
`codex/`, `feature/`, `fix/` or `docs/`. Preserve existing work and history.
Prepare the applicable OpenSpec proposal, specifications, design and tasks
before implementation. This tooling change is
`configure-github-app-publication`.

Stage exactly the completed change, including its documentation and changelog.
There must be no unstaged changes, unresolved index entries or non-ignored
untracked files. Do not create a separate local human-authored commit for the
publisher: the eligible parent is either the starting main revision or the
previous remote, verified App-bot commit on this same branch.

Write an English PR body in an ignored file, for example
`.soulkiller-local/publication-pr.md`. Include the OpenSpec change, checks
actually executed, limitations, scope and issue references. Use `Refs #N` for
partial work and `Closes #N` only when merging completes the issue. A reference
in the body is not a native GitHub Development branch association; the current
publisher does not create that association.

## Commands

Show the supported arguments:

```sh
node tools/github-app/cli.mjs --help
```

All commands default to an **offline dry run**, with no key read, token request
or network call:

```sh
node tools/github-app/cli.mjs check
node tools/github-app/cli.mjs publish \
  --title "chore(repository): apply the reviewed change" \
  --body-file .soulkiller-local/publication-pr.md
node tools/github-app/cli.mjs verify --number 10
```

The dry run validates local state and runs the relevant fixed gates. It does
not establish App installation access, remote branch state, commit
verification or actual PR creation. `verify` in offline mode checks local
state only.

Inspect read-only remote authentication and parent metadata:

```sh
node tools/github-app/cli.mjs check --execute \
  --key-file .soulkiller-local/github-app/private-key.pem
```

This authenticated check reads App, installation, repository and ref metadata.
Minting and revoking its read token are the only authentication mutations; it
does not publish repository content.

Publish the staged change and create or reuse its ready PR:

```sh
node tools/github-app/cli.mjs publish --execute \
  --key-file .soulkiller-local/github-app/private-key.pem \
  --title "chore(repository): apply the reviewed change" \
  --message "chore(repository): apply the reviewed change" \
  --body-file .soulkiller-local/publication-pr.md
```

`--message` is optional and defaults to the title; for new commits, pass an explicit
[Conventional Commit](../CONTRIBUTING.md#commit-messages) message. Titles and messages must be
nonempty single-line text. The tool requests a review from `Eneru`; a denied
review request is reported as `reviewRequested: false` without hiding an
otherwise valid PR. Repository review requirements and CODEOWNERS remain
separate maintainer-managed controls.

To explicitly refresh the same bot PR title and body after review corrections,
add `--update-pr` to `publish`. The inputs are captured and scanned; the tool
checks the expected bot PR/head before updating and verifies the saved metadata.
Without that flag, existing PR metadata is preserved.

Verify the resulting PR and its exact local tree:

```sh
node tools/github-app/cli.mjs verify --execute --number 10 \
  --key-file .soulkiller-local/github-app/private-key.pem
```

Successful output contains public repository/App identifiers, branch, object
SHAs, verification state and the PR URL. Errors expose fixed explanations and
safe public identifiers or HTTP status, never API response bodies, scanner
output, PEM contents or token values.

## Reply to maintainer review comments

After publishing and verifying the current branch, write the requested English
reply in an ignored file. No unpublished staged or unstaged changes may remain.
Use the numeric ID of the top-level inline maintainer comment, not a thread node
ID or a reply ID. For example:

```sh
node tools/github-app/cli.mjs reply \
  --number 10 --comment 4176900402 \
  --body-file .soulkiller-local/review-reply.md
node tools/github-app/cli.mjs reply --execute \
  --number 10 --comment 4176900402 \
  --body-file .soulkiller-local/review-reply.md \
  --key-file .soulkiller-local/github-app/private-key.pem
```

The first command is offline. Execution requests only Contents read and Pull
requests write, verifies the bot PR and exact current commit/tree, confirms that
the selected top-level comment belongs to Eneru on that PR, and posts the
captured/scanned body as the App. The persisted reply identity and parent are
verified and token revocation is attempted. It never resolves a thread, submits
a review, approves or merges; thread acceptance remains the maintainer's action.

Replies are explicit and serial. Bounded pagination checks up to 1,000 existing
review comments and returns an identical bot reply instead of posting it again.
Ambiguous duplicates, repeated pages or exhausted bounds fail. REST posting has
no atomic idempotency key: a timeout can occur after GitHub accepts a reply, so
inspect/retry through this command rather than blindly posting again or running
concurrent reply commands.

Official endpoint: [reply to a review comment](https://docs.github.com/en/rest/pulls/comments#create-a-reply-for-a-review-comment).

## Publication safeguards

The publisher accepts only the fixed HTTPS origin and repository, a permitted
development branch and SHA-1 Git repositories. It compares remote main and
branch parents with the captured local state. `LICENSE` must match the
starting main revision. Tracked local secret directories, common key/secret
paths, symlinks, submodules and unresolved index entries are refused.

The staged index is captured into a process-owned temporary copy. Entries,
changes, the expected tree and validation all derive from those same bytes.
The live index, branch, HEAD and body are rechecked before publication. Local
key and body reads use an opened regular-file descriptor with no-follow and
resolved-path confinement checks; replaced leaf or ancestor symlinks are
rejected. Git replacement objects are disabled.

Fixed preflight commands are:

```sh
bash tools/checks/check.sh secrets-publication \
  --body-file .soulkiller-local/publication-pr.md --metadata-stdin
openspec validate --all --strict --no-interactive
git diff --check
git diff --cached --check
```

The publisher supplies the captured title, commit message and PR body to the
scanner's standard input. The scanner also checks the ignored body file and
raw staged Git blobs through the frozen index. Do not run the stdin variant
manually without providing the metadata. `check` uses the fixed `secrets`
gate instead. Applicable static analysis and coverage must also pass before
delivery; publication preflight is not the entire quality suite.

Raw blobs are transmitted as base64, including binary files. Blob hashes and
the complete remote tree must equal the captured staged Git objects. Regular
file modes, executable mode and deletions are preserved. Individual blobs are
limited to 16 MiB; the ignored UTF-8 body is limited to 64 KiB.

Commit creation omits custom `author`, `committer` and `signature` fields.
Both the commit API response and the repository commit inspection must show
valid GitHub verification. Repository inspection must identify the configured
App bot as author and the exact GitHub platform committer: login `web-flow`,
name `GitHub`, email `noreply@github.com`. The publisher stops before publishing a
ref if these conditions fail. Offline tests simulate this metadata and do not
prove that a particular live GitHub endpoint will provide it; an actual
successful publication is the required evidence.

Only after verification does the tool create the working branch ref or update
that same ref with `force: false`. It fetches only that branch with ephemeral
authentication, verifies the fetched object, and advances the local branch
using an expected old SHA. The index and working files are preserved; the
staged tree becomes the published commit's tree.

## Failures and retry limits

GitHub publication is a sequence of API calls, not an atomic transaction.
Repeated remote checks and non-force updates reject stale parents, but REST
ref updates have no expected-SHA compare-and-swap argument. Other GitHub APIs
have different capabilities; this limitation is specific to the REST path
used here. Stop concurrent editing/publication while executing the command.

If PR creation fails after the verified branch is published, the error
identifies that branch and commit. When the local branch was advanced
successfully, retrying the same command can create the missing PR without an
extra commit. An existing single ready bot PR is reused and its existing title
and body are preserved unless `--update-pr` is explicit. Multiple matching PRs, external authors or an
unexpected PR state are refused.

If a request times out after a remote mutation, the response may not reveal
whether GitHub accepted it. If local fetch or verification fails, the remote
branch may already exist while local HEAD remains unchanged. Inspect the
reported state and use an approved recovery procedure; do not force-push,
reset, change authentication or fall back to the maintainer connector.

## Code and test organization

Start with the command parsing in `cli.mjs`, then the workflow in
`publisher.mjs`. Publisher coordinates explicit collaborators; each class lives
in its own module. Shared helpers and constants are separate.

| Module | Responsibility |
| --- | --- |
| `constants.mjs`, `errors.mjs`, `guards.mjs` | Fixed public identity, limits and redacted errors |
| `validation.mjs`, `crypto.mjs`, `verification.mjs` | Input/token rules, JWT signing and expected GitHub metadata |
| `command.mjs` | Bounded command execution with safe errors |
| `local-files.mjs`, `confined-read.mjs` | Ignored key/body confinement and descriptor reads |
| `git-workspace.mjs`, `git-index.mjs` | Git plumbing, immutable index snapshots and local state checks |
| `quality-gates.mjs` | Fixed scans, strict OpenSpec and whitespace gates |
| `github-client.mjs` | Fixed GitHub API transport and request bounds |
| `installation-auth.mjs` | Scoped installation authentication and token revocation |
| `github-repository.mjs` | Repository/ref/PR state and permitted PR operations |
| `commit-publisher.mjs` | Exact blobs/trees, verified commits and non-force refs |
| `publisher.mjs` | Publication/check/verification workflow coordination |
| `review-replies.mjs`, `review-validation.mjs` | Explicit replies to verified maintainer comments |

Tests are grouped by capability under `test/`. Reusable temporary repositories,
a fake GitHub server and publication fixtures live under `test/helpers/`; they
contain no real credentials. Each named case follows Arrange, Act, Assert,
with independent state. Parameterized cases have their own descriptive name
and fixture instead of sharing mutations between scenarios.

## Offline validation and coverage

The implementation uses Node.js 24 built-ins and no SDK or npm dependencies.
Run:

```sh
npm --prefix tools/github-app test
bash tools/checks/check.sh static
```

The test suite uses temporary container-internal Git repositories, synthetic
RSA keys, synthetic text/binary data and a fake GitHub transport. It performs
no real authentication or paid call. The fake server reconstructs trees from
the submitted base tree and entries to test exact publication content.

The coverage metric is executable **line coverage** across all maintained
source modules listed above, including CLI execution and review replies.
The test command enforces at least 70% overall line coverage and explicitly
includes maintained source modules, which the suite exercises. Include
filters do not discover unimported modules; adding a new executable source
requires adding meaningful test execution and coverage inclusion.
The separate Bash and coverage-validator gates are described in
[quality checks](quality-checks.md). Tests and the public JSON configuration are excluded from the executable
source denominator; Markdown has no claimed test coverage.

Tests cover scope and identity failures, missing and unsafe paths, leaf and
ancestor replacement, frozen-index ABA swaps, captured body scanning, binary
bytes, modes/deletions, tree/hash/verification mismatches, stale refs, token
revocation and PR retry behavior. Live GitHub signing, installation access,
actual reviewer requests and Git network behavior remain integration checks
performed separately with the ignored local key.
