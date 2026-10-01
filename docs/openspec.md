# Working with OpenSpec

The project uses [OpenSpec](https://openspec.dev/docs/cli), installed in the
devcontainer. Its configuration is [openspec/config.yaml](../openspec/config.yaml).
The selected schema is `spec-driven`. Initialization used
`openspec init --tools none`: agents follow [AGENTS.md](../AGENTS.md)
and the CLI without depending on assistant-specific commands.

## Organization

- `openspec/specs/` contains integrated reference requirements.
- `openspec/changes/<name>/` contains a proposed change, specification deltas,
  design and tasks.
- `openspec/changes/archive/` holds archived changes.

Reference and archive directories may be empty until the first change is
integrated. The active [initialize-repo](../openspec/changes/initialize-repo/proposal.md)
proposal describes the foundation and remains active during review.

## Workflow

Run all commands below inside the devcontainer.

1. Inspect existing work with `openspec list` and `openspec list --specs`.
2. Create a change:

   ```sh
   openspec new change change-name
   openspec status --change change-name
   openspec instructions proposal --change change-name
   ```

3. Write `proposal.md`, then `specs/<capability>/spec.md` deltas,
   `design.md` and `tasks.md`. Consult the schema instructions:

   ```sh
   openspec instructions specs --change change-name
   openspec instructions design --change change-name
   openspec instructions tasks --change change-name
   ```

4. Obtain approval for decisions that require it, then implement and validate.
   Check off tasks only when supported by evidence, and record decisions in
   versioned artifacts.
5. Validate before delivering the PR:

   ```sh
   openspec validate change-name --strict --no-interactive
   openspec validate --all --strict --no-interactive
   ```

6. After implementation is accepted, prepare archiving on a branch for review:

   ```sh
   openspec archive change-name
   openspec validate --all --strict --no-interactive
   ```

   Inspect the diff: archiving updates the reference specifications and moves
   the change into the archive. It does not replace GitHub review or authorize
   a direct push to `main`.

## Language and validation

**English is the working language for all OpenSpec artifacts**, including
proposals, requirements, scenarios, designs, tasks and configuration guidance.
Use the validator's recognized structures, including `## ADDED Requirements`,
`### Requirement:`, `#### Scenario:`, `SHALL`, `WHEN` and `THEN`.
Each requirement describes observable behavior and has at least one scenario.
Structural validation does not prove that the implementation satisfies the
requirements: include actual test results.

OpenSpec telemetry and automatic update checks are disabled in the image.
Version upgrades are explicit and go through a PR with an updated npm lockfile.
