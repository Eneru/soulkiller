# Design

## Authorized scope
The maintainer requested PR-to-main/SemVer-only Actions and selected first-person text dialogue with sources. App publication/review and signed-commit protections remain unchanged.

## Event policy
Use native pull_request branches: [main] and push.tags version-shaped globs; omit branch pushes and workflow_dispatch. Keep the existing foundation job, read-only token, pinned checkout, readonly container mount, concurrency cancellation and 15-minute bound. Reject tag deletion at job level.

After credential-free checkout, a small Node guard validates the full SemVer syntax, optional lowercase v prefix and allowed event/base/ref. Its boolean output controls Docker build and canonical checks. Nonversion tags excluded by native globs do not start a workflow; malformed version-shaped tags may perform lightweight checkout/eligibility only. No build/test runs for them. Never insert event text directly into shell code.

## Testing
Keep source parsing separate from CLI output; independent named AAA cases cover stable/prerelease/build tags, invalid numeric prerelease identifiers, leading zeros, malformed separators, whitespace, other events/bases, branch pushes and deleted tags. Measure maintained guard code at 70% minimum through canonical checks, with no dependencies. Test workflow-selected step execution from synthetic events without creating tags.

## Product record and exclusions
Record Q4 as first-person text dialogue with consultable sources; citation presentation details, conflict policy, rights, budgets and architecture remain open. No Windows application or real-model quality claim. Network diagnostics, public IP and private device details must never enter repository artifacts.

## References
- [SemVer 2.0.0](https://semver.org/) defines numeric/prerelease/build identifiers.
- [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) defines native PR/tag glob filters and conditional steps.
