## ADDED Requirements

### Requirement: Confined App authentication
The publisher SHALL use App ID 5174172, slug eneru-soulkiller-agent and repository
Eneru/soulkiller, and SHALL read an RSA private key only from an ignored local
path contained within Soulkiller. Tokens SHALL be repository/permission constrained,
kept in memory, redacted from diagnostics and revoked when possible.

#### Scenario: Installed App
- **WHEN** an explicit authenticated check uses the configured App and valid local key
- **THEN** the installation and repository are verified without changing repository settings

#### Scenario: Invalid or external key
- **WHEN** the key is missing, outside the local allowed directory, a symlink escaping it or invalid
- **THEN** authentication fails without printing the key or falling back to maintainer credentials

### Requirement: Explicit publication with preserved history
The publisher SHALL default to an offline dry run and SHALL publish only an
explicitly executed current permitted development branch. It SHALL refuse
main/tag/force/merge operations, stale parents, unsafe paths, LICENSE changes
and ambiguous workspace state, and SHALL publish the exact staged tree.

#### Scenario: Binary and text staged changes
- **WHEN** the contributor executes publication from a valid branch with validated staged changes
- **THEN** GitHub receives the same staged tree including binary bytes, modes and deletions while base history is preserved

#### Scenario: Stale or unsafe state
- **WHEN** main or the branch diverges, the index changes during execution, unstaged work exists or LICENSE is changed
- **THEN** publication fails before an unsafe branch update and local work remains intact

### Requirement: Verified bot commit and independent review
The publisher SHALL create commits without custom author, committer or signature
fields and SHALL require valid GitHub verification, author
eneru-soulkiller-agent[bot], and platform committer web-flow with raw name GitHub
and email noreply@github.com before publishing a ref. Completed changes SHALL produce a ready PR against main
for Eneru's review without merge, approval or repository-setting changes.

#### Scenario: Valid signed App commit
- **WHEN** GitHub returns the expected tree/parent and a verified commit authored by eneru-soulkiller-agent[bot] with the expected GitHub platform committer
- **THEN** the development ref and ready PR can be published and their public verification evidence reported

#### Scenario: Unverified or wrong identity
- **WHEN** GitHub returns an unsigned/unverified commit, a different author, or unexpected platform committer fields
- **THEN** the publisher refuses to expose that commit through the working branch

#### Scenario: PR failure after branch publication
- **WHEN** branch publication succeeds but PR creation fails
- **THEN** the failure identifies the published branch safely and a retry avoids duplicate PRs or history rewriting

### Requirement: Native quality gates
The component SHALL provide credential-free tests including errors/boundaries,
at least 70% maintained executable line coverage, explicit secret scans before
API publication, applicable static/Docker checks and bounded unprivileged CI.

#### Scenario: Synthetic secret or missing scanner
- **WHEN** a staged secret, secret in the proposed PR body or scanner execution failure is detected
- **THEN** pre-publication checks fail with redacted output before remote publication

#### Scenario: Coverage below threshold
- **WHEN** the measured maintained component has less than 70% line coverage
- **THEN** its test command fails locally and in CI

#### Scenario: Hook setup and partial staging
- **WHEN** a contributor explicitly installs hooks or stages only part of a file
- **THEN** existing unrelated hooks/configuration are preserved and the staged secret content is still checked
