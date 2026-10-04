# Limit CI to reviewed PRs and version tags

## Why
The maintainer wants to avoid repeating builds on pushes to main. Product framing now confirms first-person text dialogue with consultable sources.

## What Changes
- Restrict build/test Actions to PRs targeting main and valid SemVer 2.0.0 version tags. Support bare versions and the conventional v prefix, including prerelease/build identifiers.
- Remove main-push and manual workflow triggers; use a cheap exact eligibility guard before Docker build/checks because GitHub tag filters are globs.
- Record the confirmed dialogue presentation and CI policy in project documents. Preserve remaining product decisions as open.

## Capabilities
### New Capabilities
- development-ci: event eligibility and bounded foundation checks.
### Modified Capabilities
None. Product work records a maintainer decision; no application behavior is implemented.

## Impact
Existing quality workflow, small tested dependency-free Node guard, canonical checks and documentation. Refs #7; no repository settings, release tag, application stack, provider or paid experiment.
