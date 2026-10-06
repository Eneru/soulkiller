# Agent instructions

## Scope and environment

- Work only in the Soulkiller folder. Do not modify other host folders, global
  host configuration or GitHub repository settings.
- Run development commands, Git, installations and validation inside the
  devcontainer. Only commands needed to build and launch it may run on the host.
- Mount only Soulkiller; do not mount the Docker socket or host credential
  directories. Writes internal to the image and container are expected.
- Read any more specific AGENTS.md files before editing within their scope.
- Preserve existing changes and history. Do not force-push, perform destructive
  cleanup or overwrite work without explicit instructions.
- Never modify LICENSE.

## Working method and language

- English is the project's working language. Write specifications, documentation,
  agent instructions, code comments, issue and PR content, and new commit messages
  in English. Preserve tool-defined identifiers and validation keywords,
  including SHALL and WHEN/THEN in OpenSpec specifications.
- Read README.md, CONTRIBUTING.md and the relevant specifications.
- Use OpenSpec through its CLI and openspec/config.yaml; do not install global
  configuration or skills on the host.
- For behavior or architecture changes, prepare the proposal, specifications,
  design and tasks before implementation. Ask the maintainer to validate product
  decisions or scope changes; an explicit request approving a plan is authorization.
- A documentation fix with no behavioral effect may reference an existing
  specification; explain in the PR if none applies.
- Do not invent Soulkiller's stages. Python, .NET, Angular and OmniRoute are
  candidates, not adopted technologies.
- Keep changes small and documented. Prefer rg for searches.
- Use Conventional Commits 1.0.0 for new authored commit messages, in English,
  with a lowercase type and optional scope (for example feat(evaluation): ...).
  Follow CONTRIBUTING.md; preserve existing history and generated merge commits.
- Keep tooling modules cohesive: one class per file, explicit collaborators and
  separate shared helpers/constants. Follow CONTRIBUTING.md for independent
  Arrange/Act/Assert tests and reusable synthetic fixtures.

## Quality and secrets

- Test changed behavior, errors and boundaries. For future features, include
  appropriate unit, integration and end-to-end tests. Routine tests must run
  without credentials or paid LLM calls.
- Integrate DevOps/DevSecOps checks with each language/component from its first
  implementation; follow docs/development-quality.md and issue #7.
- Maintain at least 70% test coverage for executable code; define the metric and
  justified exclusions in the implementation change. Do not fabricate coverage
  for Markdown or unimplemented code.
- Add applicable pinned local/CI checks: Gitleaks, Hadolint, Bandit for Python,
  equivalent analysis for other languages, and ZAP for runnable web targets.
- Evolve the devcontainer runtime, native editor extensions/settings and validation
  guidance alongside each added language/component; command tasks alone do not
  provide native editor integration.
- Specify each check's execution points: container CLI, repository-local hooks,
  container-side editor integration and CI. Run Gitleaks before committing and
  Hadolint in the editor using the binary installed in the image, once implemented.
- Plan reproducible benchmarks and bounded load tests with approved profiles,
  synthetic inputs and explicit thresholds; do not claim unexecuted results.
- Keep secrets, applicable static checks and coverage in the fast PR lane.
  CI builds/checks run only for PRs targeting main or valid SemVer version tags;
  reserve expensive CI checks for reviewed version tags with bounded resources.
  Do not add main/other branch pushes or manual Actions dispatch without a new decision.
- Follow docs/documentation-site-plan.md for issue #8; Pages uses Actions by
  maintainer report. Do not publish private/local data or change Pages settings.
- Do not report a check as passing unless it was executed. Report blockers and
  distinguish foundation checks from application tests.
- Run openspec validate --all --strict --no-interactive and git diff --check
  before delivery; follow docs/validation.md for devcontainer changes.
- Do not commit secrets, real personal data or sensitive logs. Use synthetic
  examples and ignored local files.
- No OmniRoute service or LLM provider must start automatically.
- Update documentation and CHANGELOG.md to match delivered behavior.

## GitHub and review

- Follow GitHub Flow: a short-lived branch from main, validation, a PR ready for
  maintainer review and manual merge.
- Open a non-draft PR when the completed change needs maintainer validation.
  Use a draft only for unfinished work with a useful portion available for early
  reading, for example before a context/quota limit; make the remaining work clear.
  Early reading is not approval. Mark it ready when completion and checks permit.
- Publish only the authorized working branch. Do not merge, enable auto-merge
  or change repository protections.
- Link issue work through GitHub's native Development mechanism when available;
  a branch name alone is not a native link. Use Closes #N in the PR description
  only when its merge completes that issue; use Refs #N for partial work.
- Report any native branch-link capability limitation rather than claiming success.
- Keep completed issues as closed history. Automatic branch deletion is a
  maintainer-managed repository setting; do not change settings or enable auto-merge.
- Publish agent changes through tools/github-app/cli.mjs in the devcontainer;
  read docs/github-app-publication.md. The existing connector may authenticate as
  Eneru: do not fall back to it for agent publication or human review.
- Keep App keys inside ignored .soulkiller-local/github-app/, never in CI/image/logs.
  Require verified bot commits, exact staged trees and non-force branch updates.
- The PR must identify the OpenSpec change, checks performed and their limitations.
- Proposed issues in docs/roadmap.md require maintainer review before being
  created on GitHub.
- Do not mark review or merge as complete before confirmation.
