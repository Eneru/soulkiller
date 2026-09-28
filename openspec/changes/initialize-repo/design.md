# Design

## Context

The local folder was empty. The public Eneru/soulkiller repository on main
contains LICENSE, a short README and a Python gitignore. Docker WSL integration
is needed to comply with the requirement to execute commands inside a container.

## Goals / Non-Goals

Provide a minimal rebuildable environment and a contribution process with
specifications, validation and human review. Do not choose stages, application
architecture or LLM providers during initialization.

## Decisions

- Use Ubuntu 24.04 pinned by digest and its non-root ubuntu user. Mount only
  the Soulkiller workspace; no privileged mode or Docker socket.
- Install Node.js 24.21.0 from the official archive with a SHA-256 checksum for
  amd64 or arm64. Lock OpenSpec 1.13.2 and its dependencies in
  .devcontainer/tools/package-lock.json without creating an application npm project.
- Pin direct Ubuntu packages. Transitive APT dependencies still come from the
  mirrors, so bit-for-bit reproducibility is not guaranteed.
- Use openspec init --tools none and AGENTS.md as the agent entry point.
  Specifications describe the development environment's behavior.
- Use English as the working language for specifications, documentation, agent
  instructions, code comments, issue and PR content, and new commit messages.
  Record this policy in the README, contribution guide, AGENTS.md, OpenSpec
  configuration and requirements. Preserve historical commits and LICENSE.
- Provide a Markdown validation procedure without adding scripts or CI.
- Describe OmniRoute and future issues in the roadmap; activation and publication
  require a separate review.
- Keep the OpenSpec change active until acceptance. Later archiving will update
  the reference specifications through a PR.

## Risks / Trade-offs

- Mirrors may remove pinned APT versions: update affected versions in a PR
  instead of silently replacing them.
- Windows mounts may behave differently from native Linux permissions. Verify
  writes as the non-root user; Dev Containers clients may adapt its UID to the host.
- Initialization does not enable GitHub protections enforcing review:
  the requirement is documented and followed in the workflow.
- Foundation checks are not an application test suite. Build that suite alongside
  the features.

## Migration Plan

Clone the existing repository without changing LICENSE, work on
feature/initialize-repo, validate locally and open a draft PR against main.
No data migration or GitHub settings changes are needed.
Before merge, abandoning the PR leaves main unchanged.

## Open Questions

Stages, architecture and OmniRoute adoption are intentionally left to the roadmap
proposals. They do not block this foundation.
