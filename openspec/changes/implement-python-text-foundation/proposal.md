# Python evaluation foundation

## Why

PR #13 was approved and merged. The maintainer authorizes implementation, with
short reviewable PRs. Start with the pinned runtime, quality gates and pure TXT
decoding/evidence seam before adding filesystem access or PDF dependencies.

## What Changes

- Install isolated CPython 3.13.16 and hash-locked development tools in the Ubuntu devcontainer.
- Decode supplied bytes strictly as UTF-8, retaining source SHA-256 and exact text.
- Produce inspectable code-point evidence slices, rejecting invalid ranges/outcomes.
- Run independent tests, all-source >=70% line coverage, Ruff, mypy, Bandit and dependency audit through the existing CLI/hooks/editor/CI policy.
- Provide pinned container-side VS Code Python, Ruff and mypy integration, source navigation and native pytest discovery using the image interpreter/tools and experiment configuration.
- Document small follow-up tranches and actual verification.

## Capabilities

### New Capabilities

- `text-evidence-foundation`: byte decoding and evidence for the evaluation only.

### Modified Capabilities

None. This is partial implementation of `evaluate-text-pdf-extraction`, not a completed comparison.

## Impact

Development image, an isolated experiments/text-pdf package, tests and quality
commands. Python is an evaluation tool, not an adopted production stack. No PDF
parser, file reader, manifest, worker, report, benchmark, model, provider, web
service, paid call, Windows lane or GitHub settings change is included.
Refs #7; no issue is completed or new issue created by this delivery.
