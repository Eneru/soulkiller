# Contributing to Soulkiller

## Environment

Read the [README](README.md) and start the devcontainer before running commands.
Run installations and Git commands in its terminal. Do not modify other host
folders or [LICENSE](LICENSE).

Git identity and authentication remain personal. When needed, configure identity
at repository level using `git config --local` and use an approved authentication
mechanism, without tokens in tracked files or remote URLs. Do not copy credentials
into the image.

## Working language

Use **English** for project work: specifications, documentation, agent instructions,
code comments, issues, pull requests and new commit messages. Keep tool-defined
identifiers and validation keywords unchanged. Historical commits are preserved;
the language policy does not require rewriting history.

## GitHub Flow

We follow [GitHub Flow](https://blog.stephane-robert.info/docs/developper/version/git/workflows-git/#4-github-flow):

1. Start from an up-to-date `main` and a clean workspace. Preserve local work.
2. Create a short-lived branch, such as `feature/name`, `fix/name` or `docs/name`.
3. Prepare the [OpenSpec](docs/openspec.md) artifacts, then implement the authorized
   change with its checks and documentation.
4. Make focused commits with clear messages and open a **draft** PR.
5. Describe the problem solved, the OpenSpec reference, tests actually run and
   limitations. Request maintainer review when ready.
6. Wait for approval; merging into `main` remains manual. No auto-merge.

Example to run inside the container from a clean workspace:

```sh
git switch main
git pull --ff-only origin main
git switch -c feature/change-name
```

If Git refuses an update, inspect the divergence instead of forcing it.
This setup does not configure GitHub branch protection; review remains a
contribution rule.

## Validation and documentation

- Follow [docs/validation.md](docs/validation.md) and validate OpenSpec.
- Add meaningful tests for each future application behavior: success, invalid
  input, dependency failures and regressions.
- Use deterministic LLM test doubles for routine tests. Reserve external trials
  for explicit runs with an agreed budget and local secrets.
- Update the README, guides and [CHANGELOG](CHANGELOG.md) as appropriate.
- Check off a task only after verifying its outcome.

This PR introduces no CI. Include local validation evidence in the PR description;
a minimal CI setup may be proposed separately.

## Issues and security

Use the bug and feature templates for ordinary requests.
The [roadmap](docs/roadmap.md) contains proposals that have not been published yet.
Follow [SECURITY.md](SECURITY.md) for vulnerabilities.
