# Contributing to Soulkiller

## Environment

Read the [README](README.md) and start the devcontainer before running commands.
Run installations and Git commands in its terminal. Do not modify other host
folders or [LICENSE](LICENSE).

Human Git identity and authentication remain personal. When needed, configure identity
at repository level using `git config --local` and use an approved authentication
mechanism, without tokens in tracked files or remote URLs. Do not copy credentials
into the image.

## Working language

Use **English** for project work: specifications, documentation, agent instructions,
code comments, issues, pull requests and new commit messages. Keep tool-defined
identifiers and validation keywords unchanged. Historical commits are preserved;
the language policy does not require rewriting history.

## GitHub Flow

We follow [GitHub Flow](https://blog.stephane-robert.info/docs/developper/version/git/workflows-git/#4-github-flow):

1. Start from an up-to-date `main` and a clean workspace. Preserve local work.
2. Create a short-lived branch, such as `feature/name`, `fix/name` or `docs/name`.
3. Prepare the [OpenSpec](docs/openspec.md) artifacts, then implement the authorized
   change with its checks and documentation.
4. Make focused commits with clear messages. Open a **ready-for-review** PR when
   the completed change needs maintainer validation.
5. Describe the problem solved, the OpenSpec reference, tests actually run and
   limitations. Use a draft only for unfinished work with a useful portion for
   early reading, such as before a context/quota limit. State what remains and
   mark it ready after completion and checks; early reading is not approval.
6. Wait for approval; merging into `main` remains manual. No auto-merge.

Example to run inside the container from a clean workspace:

```sh
git switch main
git pull --ff-only origin main
git switch -c feature/change-name
```

If Git refuses an update, inspect the divergence instead of forcing it.
This setup does not configure GitHub branch protection; review remains a
contribution rule. Historical OpenSpec delivery records may mention drafts;
this policy supersedes them for new work.

Commit author metadata does not change the authenticated GitHub account that
opens a PR. Separating agent development from maintainer approval requires a
separately authenticated machine user or GitHub App and maintainer-configured
review rules. Never approve or merge agent work using the maintainer's identity.
The [publication tool](docs/github-app-publication.md) authenticates as the installed
App; never use the maintainer-authenticated connector as a fallback for agent
publication. The PEM remains an ignored local input. CODEOWNERS requests Eneru's
review, while enforcing review/signature rules remains a maintainer setting.

## Issue linkage and completed work

When working on an approved issue, create or link its branch through GitHub's
**Development** section when that interface is available. A branch created there
connects the eventual PR to the issue. See
[GitHub's branch workflow](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-a-branch-for-an-issue).
Including the issue number in a branch name aids navigation but does not create
that native connection; report a tooling limitation if the native link cannot be made.

Use `Closes #N` in the PR description when merging into the default branch
completes the issue. Use `Refs #N` for partial or related work: it does not close
the issue. Check the issue's criteria before choosing a closing keyword.
See [GitHub's issue linking rules](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
Close completed issues rather than deleting their history.

Automatic deletion after merge is a repository setting, not a PR option:
**Settings → General → Pull Requests → Automatically delete head branches**.
The maintainer controls it; agents keep repository settings unchanged and must
not claim it is enabled without verification. Branch protections/rules can prevent
deletion. See
[GitHub's branch deletion documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches).
This setting does not authorize automatic merging.

## Validation and documentation

- Follow [docs/validation.md](docs/validation.md) and validate OpenSpec.
- Add meaningful tests for each future application behavior: success, invalid
  input, dependency failures and regressions.
- Apply the [development quality plan](docs/development-quality.md) with each
  implemented language/component: at least 70% coverage, applicable security/static
  checks and reproducible local/Actions commands. Metrics and exclusions need review.
- Specify where checks run: container CLI, repository-local pre-commit hooks,
  container-side editor diagnostics and CI. Editor/hooks complement CI, not replace it.
- Include reproducible benchmarks and bounded load tests as components become
  measurable, with synthetic data, approved resource profiles and thresholds.
- Use deterministic LLM test doubles for routine tests. Reserve external trials
  for explicit runs with an agreed budget and local secrets.
- Update the README, guides and [CHANGELOG](CHANGELOG.md) as appropriate.
- Check off a task only after verifying its outcome.

A small [quality workflow](.github/workflows/quality.yml) checks this tooling and
the foundation. [Quality commands](docs/quality-checks.md) are shared with the
container CLI. [Issue #7](https://github.com/Eneru/soulkiller/issues/7) remains open
for future component gates; implement those alongside their development.
Run CI builds/checks only on PRs targeting main and valid SemVer version tags;
reserve expensive CI work for reviewed version tags. Main/other branch pushes
and manual Actions dispatch do not repeat those checks. Local container commands
remain available. See [the event policy](docs/quality-checks.md#editor-and-ci).
[Issue #8](https://github.com/Eneru/soulkiller/issues/8) tracks the Actions-based
[documentation site](docs/documentation-site-plan.md). Include actual local/CI
results and limitations in each PR; do not claim planned automation is running.

## Maintainable tooling and tests

Keep modules focused on a clear responsibility. In the Node.js tooling, put
each class in its own file, separate shared constants and pure helpers from
publication orchestration, and use explicit imports and composition. Prefer
named operations over compact expressions that hide validation or cleanup.

Organize tests by capability. Keep reusable synthetic repositories and fake API
fixtures in dedicated helper files. Each named test follows Arrange, Act, Assert
(or Given, When, Then), using one independent scenario and a fresh fixture.
Parameterized cases still have a descriptive name and those phases; avoid
adding a second scenario after the first scenario's assertions. Assert behavior
and failures rather than implementation layout.

When splitting source modules, update meaningful tests and coverage inclusion
for all maintained executable modules; an include filter alone does not execute
an unimported module. See [the publication guide](docs/github-app-publication.md)
for the tooling layout.

## Issues and security

Use the bug and feature templates for ordinary requests.
The [roadmap](docs/roadmap.md) contains proposals that have not been published yet.
Follow [SECURITY.md](SECURITY.md) for vulnerabilities.
