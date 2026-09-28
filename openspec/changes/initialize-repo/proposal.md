# Proposal

## Why

Soulkiller only has an initial README, a license and Git exclusions.
A shared foundation is needed before defining stages and developing the
application so that work is reproducible and reviewable.

## What Changes

- Add a minimal Ubuntu devcontainer with a non-root user, Git, Node.js and OpenSpec.
- Initialize the specification process and contribution instructions.
- Document startup, security, validation and changes.
- Provide PR and issue templates and a roadmap for review.
- Connect the workspace to the repository and deliver through a branch and draft PR.
- Establish English as the working language for specifications, documentation,
  agent instructions, code comments, contribution content and new commit messages.

Out of scope: application code, stage definitions, Python/.NET/Angular SDKs,
Docker-in-Docker, active OmniRoute integration, CI and LICENSE changes.

## Capabilities

### New Capabilities

- `development-foundation`: containerized environment, foundation validation,
  English-language project artifacts and OpenSpec-guided contribution.

### Modified Capabilities

No existing reference specifications.

## Impact

The repository receives documentation and configuration files. Building requires
access to Ubuntu, Node.js and npm registries. No application API, data migration
or LLM provider usage is introduced.
