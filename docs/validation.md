# Validating the foundation

Run the development commands below inside the devcontainer. Only building and
relaunching the container happens through Docker or the editor on the host.
Record results and limitations in the PR in English.

## Build and tools

Rebuild the image using the [.devcontainer configuration](../.devcontainer/devcontainer.json)
in your editor, or use the host commands in the [README](../README.md).

In the container terminal:

```sh
id
pwd
git --version
node --version
npm --version
openspec --version
rg --version
test "$(id -u)" -ne 0
test "$PWD" = /workspaces/soulkiller
test ! -S /var/run/docker.sock
```

Expected: a non-root user, the correct workspace, Git 2.43.0, Node.js v24.21.0,
OpenSpec 1.13.2 and ripgrep 14.1.0. No LLM credential is required.

## Writes and persistence

Create an ignored local marker without overwriting an existing file:

```sh
test ! -e .soulkiller-local/persistence-check.txt
mkdir -p .soulkiller-local
printf 'soulkiller-persistence-check\n' > .soulkiller-local/persistence-check.txt
```

Recreate the container with the same Soulkiller mount, then verify:

```sh
test "$(cat .soulkiller-local/persistence-check.txt)" = soulkiller-persistence-check
test -w .soulkiller-local/persistence-check.txt
```

After this check, delete only that marker if desired, from inside the container.
Never include the local directory in a commit.

## Specifications and repository

```sh
openspec list
openspec status --change initialize-repo
openspec validate --all --strict --no-interactive
git diff --check
git diff --cached --check
git diff origin/main -- LICENSE
git status --short
git check-ignore .env .env.local .soulkiller-local/persistence-check.txt .devcontainer/tools/node_modules/example
```

The `status --change initialize-repo` command applies to this PR; after archiving,
use the active change's identifier. The LICENSE diff must be empty. Also compare
its checksum with the initialization baseline:

```sh
sha256sum LICENSE
```

Initial checksum: `30cd79522ebd85148c43a931036e514e8b5cf8372776be39fc65a2f6293b051c`.

## Configuration and document review

- Verify that devcontainer.json is valid JSON and matches the Dockerfile:
  user, workspace, build context and startup command.
- Verify that the npm manifest and lockfile pin the same OpenSpec version.
- Check internal Markdown links and command consistency.
- Verify both issue templates' YAML headers and required fields.
- Check that project text, specifications, templates and configuration guidance
  are in English and state a consistent working-language policy.
- Inspect tracked files: no secrets, unapproved application code/workflows or
  LICENSE changes. Development tooling and its quality workflow are allowed in
  configure-github-app-publication. Git exclusions do not replace this inspection.
- After publication, verify the branches, PR link and ready-for-review status.
  A draft is only appropriate for unfinished work offered for early reading;
  record what remains instead of requesting final approval.

## Tooling and security checks

Inside the rebuilt container, follow [quality commands](quality-checks.md):

```sh
gitleaks version
hadolint --version
eslint --version
npm --prefix tools/github-app test
bash tools/checks/check.sh all
```

The test command enforces at least 70% executable line coverage for the publisher;
its API tests use fakes and generated ephemeral keys. Live App identity/signature
verification is a separate explicit run described in
[publication setup](github-app-publication.md). Never print tokens or PEM contents.
Record the tested architecture and distinguish a local equivalent from an actual
hosted Actions run. Verify container-side editor diagnostics manually; configuring
an extension does not prove that its UI ran.

## Limitations

This procedure does not test an application yet. Editor UI startup and each
hardware architecture must be distinguished from checks performed through the
Docker CLI; do not claim they were tested unless they were actually exercised.
