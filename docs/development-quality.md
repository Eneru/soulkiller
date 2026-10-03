# Development quality, DevOps and DevSecOps

**Maintainer direction:** 2026-10-03.
Tracking: [issue #7](https://github.com/Eneru/soulkiller/issues/7).
This plan accompanies each implemented component. No scanners, coverage gate or
GitHub Actions workflow are configured yet; the current change records the work.

## Requirements and rollout

Add applicable local checks and Actions automation in the same reviewed change
that introduces a language or component. Do not deliver application code first
and postpone its security/test gates to a separate cleanup milestone.

- Minimum test coverage: **70%** for maintained executable code.
- Secret detection with Gitleaks; Dockerfile checks with Hadolint.
- Python security analysis with Bandit when Python is introduced; appropriate
  analysis for every other adopted language.
- OWASP ZAP for runnable web targets, with declared scan scope.
- Deterministic tests, dependency/configuration checks, meaningful failure results
  and documented commands reproducible in the devcontainer.
- Automatic GitHub Actions execution, with a small fast lane and bounded deeper
  checks on tags or trusted manual runs. No mandatory paid account or service.

First deliver reviewed foundation commands and a small Gitleaks/Hadolint/validation
workflow. Extend it with each language's tests, coverage and analysis when that
language enters the project. Web DAST and native Windows packaging need suitable
targets and reviewed test lanes. This is not permission to install every candidate
tool, adopt an application stack or enable a broad matrix immediately.

## Coverage contract to finalize in the implementation proposal

The proposed interpretation is at least **70% line coverage per maintained
executable component**, so one language/component cannot hide another's low
coverage. The threshold is a minimum, not evidence that the behavior is correct.
Tests must still cover success, errors, boundaries and meaningful regressions.

Include unexecuted source files in measurement. Document justified exclusions
such as generated/vendor code; do not broadly omit difficult code or lower the
threshold to obtain a pass. Report branch coverage where supported, without
inventing a separate numeric floor the maintainer has not requested.

Pure Markdown and non-executable configuration have no application coverage
denominator: report not applicable, not a fabricated 70% result. Hand-written
site components/build tooling need the applicable tests and coverage policy.
Verify the gate with synthetic failing and passing cases at implementation time.
Keep reports local or in bounded CI artifacts; no external coverage account is
required. Python candidates include coverage.py/pytest-cov:
[coverage reporting](https://coverage.readthedocs.io/en/latest/commands/cmd_report.html),
[pytest-cov configuration](https://pytest-cov.readthedocs.io/en/latest/config.html).

## Applicable checks

| Scope | First applicable gate | Later or deeper checks |
| --- | --- | --- |
| Repository | OpenSpec/docs/config checks and Gitleaks on reviewed changes with sufficient Git history | Full-history scan on baseline establishment and tag/manual runs |
| Dockerfiles | Hadolint, including the devcontainer Dockerfile when this baseline is introduced | Rebuild/boot and an approved image/dependency scan |
| Python, if adopted | Tests/coverage, Bandit, lint/type checks and dependency vulnerability checks | Broader integration/end-to-end/resource evaluations |
| .NET or TypeScript, if adopted | Tests/coverage and selected native lint/type/security/dependency analysis | Packaging, browser/runtime and broader OS checks |
| Runnable web | Bounded ZAP baseline against an ephemeral synthetic instance when applicable | Active/full ZAP and deeper end-to-end checks on tags/manual runs |
| Documentation site | Production build, links/routes, dependency checks and applicable custom-code tests | Broader accessibility/browser checks and approved publication |

Bandit analyzes Python syntax trees for common issues; it does not prove absence
of vulnerabilities. Hadolint checks Dockerfile rules and shell instructions.
[Bandit](https://bandit.readthedocs.io/en/latest/),
[Hadolint](https://github.com/hadolint/hadolint).

Prefer the pinned Gitleaks CLI as the reproducible local/CI tool. Its Git mode
can scan commit ranges; use redacted output and enough history for the declared
scope. The separate Gitleaks Action has its own license/account conditions,
including an organization-key requirement; it is not necessary for CLI use.
Review current releases/maintenance before pinning an implementation.
[Gitleaks CLI](https://github.com/gitleaks/gitleaks),
[Gitleaks Action](https://github.com/gitleaks/gitleaks-action).

ZAP baseline performs crawling/passive analysis; full scan also performs active
attacks. Run either only against the declared ephemeral project-owned test
instance, with synthetic data and time limits. A static documentation site and
a future application web/API surface need different applicable scan policies.
[ZAP baseline](https://www.zaproxy.org/docs/docker/baseline-scan/),
[ZAP full scan](https://www.zaproxy.org/docs/docker/full-scan/).

Define rule/severity thresholds in the implementation change. Fail selected
gates on findings or scanner execution errors; report explicit not-applicable
checks. Suppressions need narrow scope, rationale and review. Do not use blanket
allowlists or continue-on-error to turn a failure into success.

## Actions lanes and budget

| Lane | Proposed contents | Trigger boundary |
| --- | --- | --- |
| Fast validation | Secrets, applicable Docker/language analysis, deterministic tests and 70% coverage, OpenSpec/docs checks | PRs and reviewed main changes |
| Deeper validation | Repeat baseline; full scans, broader supported-OS/packaging/end-to-end work | Selected tags or trusted manual runs |
| Pages | Unprivileged PR build checks; separate static artifact deployment | Reviewed main or trusted manual run; no PR deployment |

Basic coverage, secret detection and applicable static analysis stay before merge.
Tags reduce the frequency of expensive work; they do not replace these early
gates. Verify a tag's reviewed revision before privileged/release work: a tag
name alone does not prove membership in main or authorize publication.

Use standard hosted runners, explicit timeouts, a bounded matrix, cancellation
of obsolete PR runs and short artifact/cache retention. Plan no schedule initially.
If a check later becomes required, avoid workflow-level path skipping that leaves
it pending; return a reliable aggregate result while skipping irrelevant jobs.
Linux CI should reuse devcontainer commands. Native Windows runs require a
separately reviewed lane; Linux results are not native Windows evidence.

Standard hosted-runner compute is free for public repositories under current
GitHub terms; larger runners and storage/cache allowances are separate. Recheck
eligibility and estimates before implementation rather than promising unlimited
free use. No repository billing or protection settings are changed here.
[Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions),
[workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency).

## Workflow trust and reproducibility

Pin scanner versions and action commit SHAs; verify
downloaded artifacts and maintain the dependency/notice inventory. Local commands
stay inside the devcontainer under [AGENTS.md](../AGENTS.md).

Use pull_request for untrusted contribution checks, contents:read by default,
and permissions only where required. Do not execute PR-controlled code through
privileged pull_request_target or a privileged workflow consuming untrusted
artifacts. Keep PR fields out of shell-code interpolation.
[GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use),
[PR trust boundaries](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).

Use synthetic fixtures and model doubles. No real personal corpus, provider
credentials or paid LLM calls in routine CI. Redact scanner reports and logs
before retention; a detected credential needs revocation/rotation, not merely
a suppressed finding. Actual security checks and their limits must be visible
in each implementation PR. Reports do not replace human review.
