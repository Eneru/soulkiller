# Proposal

## Why

Development currently uses the maintainer's GitHub identity, preventing independent
approval of the agent's PRs. The maintainer installed `eneru-soulkiller-agent`
(App ID 5174172) and explicitly authorized its configuration, a devcontainer
publication tool, documentation and a reviewed PR on 2026-10-03.

## What Changes

- Add a fixed-repository Node.js CLI using GitHub App installation authentication,
  exact staged Git objects and GitHub-created verified bot commits.
- Add offline tests, a minimum 70% executable line-coverage gate, static analysis,
  pinned Gitleaks/Hadolint, explicit local hooks and a bounded Actions check.
- Document ignored private-key setup, independent human review, verification,
  recovery and the distinction between this tool and the existing connector.
- Provide an original cyberpunk avatar designed for a circular GitHub crop.
- Add CODEOWNERS requesting Eneru's review; enforcement remains maintainer-owned.

## Capabilities

### New Capabilities

- `github-app-publication`: Safe staged publication as the installed App, verified
  identity/signature, secrets checks, ready PR and local history preservation.

### Modified Capabilities

None. The historical initialization scope remains a historical delivery record.

## Impact

Development tooling and a small CI lane; no application stack, provider, Pages
deployment, product behavior or repository-setting changes. Private keys remain
ignored inside Soulkiller and never enter the image, logs, PR or CI. This delivers
part of issue #7; broader component gates remain open.

## Review follow-up

PR #10 review authorizes modular source files, shared fixtures, separate readable
Arrange/Act/Assert test cases, the revised artwork, and App-authenticated replies
to review comments. The maintainer retains thread resolution and final approval.
