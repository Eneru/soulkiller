# Soulkiller

Soulkiller is a multi-stage application project inspired by the Soulkiller from
Cyberpunk 2077. The first goal is to define its use cases and progressively build
an application that uses LLMs. Its stages, data and expected behavior still need
to be specified: no "consciousness digitization" capability has been implemented
or demonstrated.

## Project status

This initial setup provides a development environment and contribution rules.
There is no application code, server or functional test suite yet. Python, .NET
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
they do not replace future application tests. No GitHub Actions workflow is
included at this stage.

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
