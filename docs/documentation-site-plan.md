# Documentation site plan

**Maintainer request:** 2026-10-03.
Tracking: [issue #8](https://github.com/Eneru/soulkiller/issues/8).
The maintainer reports that Pages uses **GitHub Actions** already. This plan
does not inspect/change that setting, add a workflow, build a site or publish it.

## Outcome and visual direction

Make the English repository documentation easy to browse, with a distinct
Soulkiller identity, clear reading order and usable navigation.
Proposed direction: a restrained dark theme with cyan/violet accents, readable
body text, accessible contrast and responsive layouts. Review a concrete visual
proposal before implementation; neither a theme nor a generator is adopted here.

Initial navigation should cover getting started, contribution/security,
OpenSpec, accepted research/decisions and the roadmap. Show proposal/review status
explicitly so a reader does not mistake candidates for implemented features.
The site documents Soulkiller; it does not host private corpora, personas,
conversation memory or inference services.

## Generator comparison

| Candidate | Fit | Tradeoff / proposed decision |
| --- | --- | --- |
| Docusaurus | Custom React/MDX pages, documentation navigation, theming, versioning and i18n options | Leading candidate for the visual brief; more frontend surface and existing Markdown/MDX compatibility to test |
| Stable VitePress | Markdown-first docs, custom Vue theme and browser-local search | Simpler comparator; use stable documentation/release rather than assuming the live alpha docs describe the selected version |
| Material for MkDocs | Markdown navigation/theme/search, Python/YAML build tooling | Additional Python tooling; upstream reports final maintenance and a move toward Zensical, so re-evaluate lifecycle before any new adoption |

Docusaurus's documented Node requirement is compatible with the current Node
major; no package is installed or version selected. Application frontend choices
remain independent of documentation tooling.
[Docusaurus installation](https://docusaurus.io/docs/installation),
[Markdown behavior](https://docusaurus.io/docs/markdown-features),
[stable VitePress](https://vuejs.github.io/vitepress/v1/),
[VitePress local search](https://vuejs.github.io/vitepress/v1/reference/default-theme-search),
[Material features](https://squidfunk.github.io/mkdocs-material/),
[Material maintainer announcement](https://github.com/squidfunk/mkdocs-material/issues/8523).

Choose the generator in a reviewed OpenSpec implementation proposal, considering
maintenance, source compatibility, notices, visual customization and build size.
Do not add a paid hosted-search dependency; a suitable local-search plugin is an
option to evaluate, not installed by this plan.

## Authoritative sources and publication scope

Repository Markdown/OpenSpec stays authoritative. Define an explicit selection
or deterministic build-only staging step instead of duplicated authored pages.
Include approved guides/research and selected accepted specifications; active
changes/archive entries require an explicit editorial choice and status labels.
Preserve OpenSpec identifiers and SHALL/WHEN/THEN text.

Rewrite file links to valid site routes or repository source links and fail on
unresolved targets. Test existing tables, code fences and diagrams in the chosen
renderer, especially MDX-sensitive characters. Navigation omission alone does
not prevent publication: inspect every generated page, static asset and search
index. Exclude local files, corpora, logs, credentials, caches and unapproved
attachments from the publication selection.
[Docusaurus docs plugin](https://docusaurus.io/docs/api/plugins/@docusaurus/plugin-content-docs),
[Docusaurus static assets](https://docusaurus.io/docs/static-assets),
[VitePress configuration](https://vuejs.github.io/vitepress/v1/reference/site-config).

## Pages workflow to implement

Use GitHub's artifact deployment, with no gh-pages branch:
build the approved static output, configure Pages, upload a Pages artifact and
deploy through the github-pages environment. PRs build/validate without deployment.
Only a reviewed main revision or trusted manual run can enter the deployment job.
Give that job pages:write and id-token:write; keep ordinary jobs contents:read.
No custom personal access token or repository-setting change is required.
[GitHub custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Verify the actual Pages URL/custom-domain metadata during implementation.
Without a custom domain, the expected project prefix is /soulkiller/:
test production assets, deep links and search routes under that prefix.
Docusaurus baseUrl and VitePress base must match the selected URL.
[Docusaurus deployment](https://docusaurus.io/docs/deployment),
[stable VitePress deployment](https://vuejs.github.io/vitepress/v1/guide/deploy).

Use one bounded site workflow with relevant-change build checks and trusted
manual dispatch. Coordinate path filtering with any required quality gate so
skipped work does not leave required checks pending. Apply the
[development quality plan](development-quality.md) to custom executable site
code and tooling; pure Markdown has no fabricated coverage result.
Use standard runners, pinned tools/actions, bounded artifacts and no paid
hosting/search service. Current Pages eligibility/limits must be rechecked at
implementation time; an upload allowance is not the published-site size limit.
[Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).

## Acceptance for the future change

- Approved generator, visual direction and publication selection.
- Reproducible production build/preview inside the devcontainer.
- Responsive reading, keyboard navigation, contrast and working routes/assets.
- Canonical-source reuse, compatible Markdown/OpenSpec rendering and no unintended
  personal/local data in static output or search artifacts.
- PR build checks, isolated Pages deployment permissions and trusted-revision checks.
- Actual build/deployment results, costs/limits and maintenance commands documented
  in a ready-for-review PR for human review.

No build, accessibility scan or deployment result is claimed by this plan.
