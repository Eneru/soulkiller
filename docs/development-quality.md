# Development quality, DevOps and DevSecOps

**Maintainer direction:** 2026-10-03; CI event policy updated 2026-10-04.
Tracking: [issue #7](https://github.com/Eneru/soulkiller/issues/7).
This plan accompanies each implemented component. The first tooling tranche,
`configure-github-app-publication`, implements Gitleaks/Hadolint/ESLint, explicit
local secret hooks, publisher tests with the 70% line-coverage gate and a bounded
Actions workflow. See [runnable quality commands](quality-checks.md). The first extraction seam adds isolated Python tools, strict UTF-8/evidence
tests and the Python gates documented in [its guide](../experiments/text-pdf/README.md).
The broader language/web/performance rollout below remains planned.

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
  checks on valid SemVer version tags. No main-push or manual Actions builds/checks. No mandatory paid account or service.

First deliver reviewed foundation commands and a small Gitleaks/Hadolint/validation
workflow, repository-local secret hooks and container-side Hadolint editor feedback.
Extend it with each language's tests, coverage and analysis when that
language enters the project. Web DAST and native Windows packaging need suitable
targets and reviewed test lanes. This is not permission to install every candidate
tool, adopt an application stack or enable a broad matrix immediately.

## Execution points and developer feedback

| Check | While editing / before committing | Container CLI and PR-to-main/version-tag CI | Deeper execution |
| --- | --- | --- | --- |
| Secrets | Repository-local Gitleaks pre-commit hook scans staged content, with redacted diagnostics | Explicit scan before publishing, including API-created commits; CI scans the declared commit range with sufficient history | Full-history scan at baseline establishment and on approved version-tag runs |
| Dockerfiles | Container-side VS Code Hadolint extension calls the image-installed binary; a lightweight hook may reuse it | Same Hadolint binary/configuration checks all applicable Dockerfiles | Approved rebuild/boot and image/dependency scans |
| Adopted languages | Container-side lint/type/security diagnostics where a maintained extension exists; fast hooks where justified | Canonical tests/coverage/static/dependency commands, including Bandit if Python | Broader integration, packaging and end-to-end tests |
| Runnable web | Explicit local test-instance setup; no background scan against external sites | Bounded ZAP baseline against an ephemeral synthetic target | Active/full ZAP only in the approved version-tag lane |
| Performance | Explicit benchmark/load commands for measurable components | Small deterministic performance regression checks only where the runner supports reliable gates | Representative benchmarks and bounded load/stress/soak profiles on approved hardware and version-tag runs |

Install pinned Gitleaks/Hadolint binaries in the devcontainer image when issue #7's
foundation tranche is implemented. Version the hook configuration and provide
an explicit repository-local setup/verification command from the container.
Gitleaks must reject synthetic staged secrets and tool failures before a commit
is created. Inspect existing hooks/core.hooksPath and preserve them; never use
global host configuration or blindly overwrite another hook.

pre-commit is a candidate hook runner; using it introduces a tooling dependency
to review, not adoption of Python for the application. Native binaries/hooks
avoid a Docker socket or nested Docker requirement. Verify pinning, checksums,
staged-content handling, partial staging, clean inputs and missing-tool failures.
[Gitleaks hooks](https://github.com/gitleaks/gitleaks#pre-commit),
[pre-commit setup](https://pre-commit.com/#install).

Add reviewed VS Code extensions through devcontainer customizations, installed
on the container side. For Hadolint, the extension supplies diagnostics and the
image supplies the executable: verify its path and shared configuration after a
rebuild. Terminal users must have the same checks without relying on editor UI.
Select equivalent language integrations only when that language is introduced.
[Hadolint integration](https://github.com/hadolint/hadolint/blob/master/docs/INTEGRATION.md),
[Hadolint VS Code extension](https://github.com/michaellzc/vscode-hadolint).

Hooks are local feedback, not a security boundary: GitHub API-created commits
and other paths can bypass them. Agent publication must therefore invoke the
canonical secret check explicitly before publishing, even when no git commit
hook runs. CI repeats the check independently. Test hook installation/persistence,
editor diagnostics and CLI/CI parity separately. The planning PR did not install
these tools; the later publication-tooling tranche installs the CLI checks and
configures the editor integration. Report editor UI verification separately.

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
| Repository | OpenSpec/docs/config checks and Gitleaks on reviewed changes with sufficient Git history | Full-history scan on baseline establishment and version-tag runs |
| Dockerfiles | Hadolint, including the devcontainer Dockerfile when this baseline is introduced | Rebuild/boot and an approved image/dependency scan |
| Python, if adopted | Tests/coverage, Bandit, lint/type checks and dependency vulnerability checks | Broader integration/end-to-end/resource evaluations |
| .NET or TypeScript, if adopted | Tests/coverage and selected native lint/type/security/dependency analysis | Packaging, browser/runtime and broader OS checks |
| Runnable web | Bounded ZAP baseline against an ephemeral synthetic instance when applicable | Active/full ZAP and deeper end-to-end checks on version-tag runs |
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

## Benchmarks and load tests

Plan performance checks with the first measurable components. A benchmark
compares reproducible extraction, indexing, retrieval or conversation workloads;
a load test measures behavior under declared arrival rates/concurrency. Bounded
stress and soak profiles explore saturation and sustained operation once those
targets exist. Multi-client load is a test profile, not adoption of multi-user
product behavior.

Use the [evaluation proposal](research/soulkiller-evaluation-plan.md) for corpus,
candidate and hardware controls. Keep TXT/PDF text and French/English first;
the roughly 1,000-page planning corpus is not a validated capacity limit.

- Record source/config/model revisions, machine profile, CPU/RAM/storage, corpus
  size, cold/warm conditions, repetitions and background load.
- Measure p50/p95 latency, throughput, peak memory/disk, error/timeout rates and
  queue/backpressure behavior. Keep functional correctness and provenance checks
  active under load; speed does not compensate for leakage or lost data.
- Exercise bounded ingestion bursts and overlapping supported operations;
  cancellation, restart/recovery, dependency delays and resource exhaustion
  must leave inspectable state. Define supported concurrency before implementing.
- Agree thresholds and comparison baselines before treating a measurement as a
  gate. Hosted-runner variability is not Windows household-PC performance proof:
  separate informational results from stable, reproducible regression checks.
- Use synthetic inputs and deterministic model doubles for routine runs. Real
  model/provider benchmarks need separately approved assets, data boundary and
  budget; never trigger paid/network trials through a tag alone.
- Set explicit maximum duration, concurrency, corpus size, memory/disk and report
  retention. Put larger benchmark/load/stress/soak runs in selected version-tag
  lanes; do not replace fast behavioral tests or the 70% coverage gate.

No benchmark harness, load generator, numeric performance threshold or result
is delivered here. Tool selection and runnable commands belong to issue #7 and
the relevant component's reviewed implementation change.

## Actions lanes and budget

| Lane | Proposed contents | Trigger boundary |
| --- | --- | --- |
| Fast validation | Secrets, applicable Docker/language analysis, deterministic tests and 70% coverage, OpenSpec/docs checks | PRs targeting main and valid SemVer version tags |
| Deeper validation | Repeat baseline; full scans, representative benchmarks/load tests and broader supported-OS/packaging/end-to-end work | Selected reviewed SemVer version tags |
| Pages | Unprivileged PR build checks; separate static artifact deployment | Reviewed version tags with provenance checks; no PR deployment |

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
