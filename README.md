# Soulkiller

Soulkiller is a multi-stage application project inspired by the Soulkiller from
Cyberpunk 2077. The first goal is to define its use cases and progressively build
an application that uses LLMs. Its stages, data and expected behavior still need
to be specified: no "consciousness digitization" capability has been implemented
or demonstrated.

## Project status

This initial setup provides a development environment and contribution rules.
There is no application code or server yet. Tested GitHub App publication tooling
and native quality checks are available; these are development tools, not application
features. Python, .NET
and possibly Angular are candidates; their use and versions will be decided in
future specifications.

The canonical repository is [Eneru/soulkiller](https://github.com/Eneru/soulkiller).
Every change goes through a branch and a pull request reviewed by the maintainer.

## Feasibility study

The [approved brief](docs/research/soulkiller-feasibility-study.md) is tracked in
[issue #3](https://github.com/Eneru/soulkiller/issues/3). The
[desk-research report](docs/research/soulkiller-feasibility-report.md) compares
local text/PDF, image and video extraction, RAG/fine-tuning, languages, deployment
and OmniRoute. Windows on an ordinary household PC is the source-machine priority.

Read the [evaluation proposal](docs/research/soulkiller-evaluation-plan.md) and
[decision register](docs/research/soulkiller-decisions.md) before the next increment.
The study was reviewed and merged in [PR #4](https://github.com/Eneru/soulkiller/pull/4).
The [first-increment framing](docs/research/soulkiller-first-increment-framing.md)
records TXT/PDF text, French/English, a small planning corpus and automatic,
inspectable/deletable memories used immediately and shared within one persona,
with their conversational origin preserved. Local versus remote operation remains a comparison
request. Candidate performance and native Windows packaging have not been tested;
no production stack is adopted.

## Quality and documentation roadmap

DevOps/DevSecOps will accompany each implementation, with a **70% minimum test
coverage**, secret/Dockerfile scans, language-appropriate analysis and web DAST
when applicable. The [quality plan](docs/development-quality.md) and
[issue #7](https://github.com/Eneru/soulkiller/issues/7) define local/Actions gates
and bounded deeper tag checks. It also defines repository-local secret-scanning
hooks, container-side editor diagnostics, benchmarks and load-test execution points.
The first tooling tranche provides pinned Gitleaks/Hadolint/ESLint, an explicit
repository-local hook installer, publisher and coverage-validator tests, Bash
integration tests with kcov, and a 70% executable line-coverage gate for maintained
JavaScript and shell helpers. A small PR/main Actions workflow repeats these checks. Read [quality commands](docs/quality-checks.md).
Web DAST and product benchmarks remain planned.

The [site plan](docs/documentation-site-plan.md) and
[issue #8](https://github.com/Eneru/soulkiller/issues/8) cover a styled English
GitHub Pages site deployed by Actions. Docusaurus leads the candidate comparison
with stable VitePress; no generator is adopted and no site has been built/deployed.

## Working language

**English is the project's working language.** Write specifications, documentation,
agent instructions, code comments, issue and PR content, and new commit messages
in English. Keep tool-defined identifiers and validation keywords unchanged.
This policy is also recorded in [AGENTS.md](AGENTS.md), the
[OpenSpec configuration](openspec/config.yaml) and the development foundation
specification.

## Start the devcontainer

Host prerequisites:

- Docker running Linux containers; on Windows, Docker Desktop with WSL 2
  integration enabled for Ubuntu.
- A Dev Containers-compatible editor, such as VS Code with the Dev Containers
  extension.
- Network access to the Ubuntu, Node.js and npm registries for the first build.

Open the Soulkiller folder in your editor and choose **Dev Containers: Reopen in
Container**. The folder is mounted at `/workspaces/soulkiller`; the terminal runs
as the non-root `ubuntu` user. Startup does not launch an application service,
make LLM calls or generate repository files.

To build and run the same environment directly from a **host terminal opened
in Soulkiller**, the only required host commands are:

```sh
docker build -t soulkiller-dev .devcontainer
docker run --rm -it --init --mount "type=bind,source=${PWD},target=/workspaces/soulkiller" soulkiller-dev bash
```

These examples use a POSIX shell, including Ubuntu on WSL. Run all subsequent
development commands, including Git and OpenSpec, inside the container.
Workspace changes persist on the host; manual installations inside the container
are lost when it is rebuilt. Do not mount other host folders or the Docker socket
for this initial setup.

## Available tools

| Component | Version / choice |
| --- | --- |
| Operating system | Ubuntu 24.04, image pinned by digest |
| Shell and search | Bash and ripgrep |
| Git | 2.43.0, Ubuntu package pinned in the Dockerfile |
| Node.js | 24.21.0 LTS, archive verified with SHA-256 |
| npm | Version bundled with Node.js |
| OpenSpec | 1.13.2, with locked dependencies |
| Gitleaks / Hadolint | 8.30.1 / 2.15.1, verified release artifacts |
| ESLint / security rules | 10.12.0 / eslint-plugin-security 4.2.0, locked dependencies |
| Bash coverage | kcov 43, source archive verified with SHA-256 |

The [.devcontainer configuration](.devcontainer/devcontainer.json) is the source
of truth. The [Dockerfile](.devcontainer/Dockerfile) pins direct packages; the
[npm lockfile](.devcontainer/tools/package-lock.json) pins OpenSpec dependencies.
Transitive system dependencies are still resolved by APT: this setup does not
guarantee bit-for-bit reproducibility. If a pinned APT version is removed from
the mirrors, update it explicitly in a PR.

To update tools, change their versions and checksums, regenerate the npm lockfile
**inside the container** if needed, then rebuild and repeat the checks.
Python, the .NET SDK, Angular and nested Docker are not installed.

## Validate the foundation

In the container terminal:

```sh
id
git --version
node --version
npm --version
openspec --version
openspec validate --all --strict --no-interactive
git diff --check
```

The complete procedure and expected results are in
[docs/validation.md](docs/validation.md). These checks validate the foundation;
they do not replace future application tests. The bounded
[quality workflow](.github/workflows/quality.yml) repeats tooling checks without
App keys or paid services.

```sh
npm --prefix tools/github-app test
bash tools/checks/check.sh all
```

## Agent publication

[GitHub App publication](docs/github-app-publication.md) uses
`eneru-soulkiller-agent` (App ID `5174172`) to create verified bot commits and ready
PRs for independent maintainer review. Public configuration lives in
[tools/github-app/config.json](tools/github-app/config.json); the private PEM stays
in ignored `.soulkiller-local/github-app/` and never enters the image or CI.
Use the CLI in the devcontainer; the existing GitHub connector still has its
own identity and does not switch accounts automatically. [CODEOWNERS](.github/CODEOWNERS)
requests Eneru's review after it reaches `main`; enforcement requires
maintainer-configured repository rules.

The [App avatar](docs/assets/README.md) is an original cyberpunk portrait with
circular-crop guidance. Upload it manually in the App's settings.

## Specifications and LLMs

[OpenSpec](https://openspec.dev/) structures proposals, specifications, decisions
and tasks before implementation. Read the [OpenSpec guide](docs/openspec.md)
and [agent instructions](AGENTS.md).

[OmniRoute](https://github.com/NStambovsky/OmniRoute) is a candidate for centralizing
LLM calls and exploring routing between providers. Its integration is only
planned: no service, provider or account is configured. Evaluation must measure
compatibility, costs, latency, privacy and failure behavior before adoption.
See the [roadmap](docs/roadmap.md).

## Contribute

- [CONTRIBUTING.md](CONTRIBUTING.md): GitHub Flow, review and validation.
- [SECURITY.md](SECURITY.md): bugs and vulnerability reporting.
- [CHANGELOG.md](CHANGELOG.md): unreleased changes and future versions.
- [Roadmap](docs/roadmap.md): proposed issues to review before publication.

The existing license is available in [LICENSE](LICENSE).
