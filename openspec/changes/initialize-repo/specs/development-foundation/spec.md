## ADDED Requirements

### Requirement: Containerized development environment
The repository SHALL provide an Ubuntu 24.04 devcontainer with Git,
Node.js 24.21.0 and OpenSpec 1.13.2, explicit versions and a non-root user.

#### Scenario: Startup from the repository
- **WHEN** a contributor builds and starts the documented environment
- **THEN** a non-root terminal is available at /workspaces/soulkiller and Git, Node.js and OpenSpec can be executed

#### Scenario: Workspace persistence
- **WHEN** the contributor writes a workspace file and recreates the container
- **THEN** the file retains its content and remains writable by the development user

#### Scenario: Invalid Node.js archive
- **WHEN** the Node.js archive checksum does not match the pinned value
- **THEN** the build fails before installing that archive

### Requirement: Minimal scope without implicit services
The environment SHALL start without an application service, LLM provider,
mounted Docker socket or additional Docker privileges; the repository SHALL
not add a GitHub Actions workflow during initialization.

#### Scenario: Foundation startup
- **WHEN** the devcontainer starts with its versioned configuration
- **THEN** no LLM call or OmniRoute service is triggered and no provider secret is required

### Requirement: OpenSpec and review workflow
The repository SHALL provide a spec-driven OpenSpec configuration,
initialization change artifacts and contribution instructions requiring human
review before merge.

#### Scenario: Specification validation
- **WHEN** the contributor runs openspec validate --all --strict --no-interactive
- **THEN** the initialization artifacts are recognized and valid

#### Scenario: Initialization delivery
- **WHEN** the change is submitted to the maintainer
- **THEN** a draft PR proposes feature/initialize-repo against main without automatic merge

### Requirement: Documentation and tracking
The repository SHALL document its status, startup, contributions, bug and
vulnerability reporting, changes and roadmap; it SHALL provide Markdown PR
and issue templates.

#### Scenario: Planning the next steps
- **WHEN** the maintainer reads the roadmap
- **THEN** each proposal includes a goal, dependencies and acceptance criteria without claiming that an issue has already been published

#### Scenario: Suspected vulnerability
- **WHEN** a contributor reads SECURITY.md
- **THEN** they are directed to an available private channel or a request for one without publicly disclosing sensitive details

### Requirement: English working language
The project SHALL use English for specifications, documentation, agent
instructions, code comments, issue and PR content, and new commit messages.
The README, contribution guide, agent instructions and OpenSpec configuration
SHALL explicitly state this policy.

#### Scenario: Creating or updating project artifacts
- **WHEN** a contributor or agent creates or updates project text or an OpenSpec artifact
- **THEN** its authored content is in English and preserves tool-defined identifiers and validation keywords

#### Scenario: Applying the policy to the existing foundation
- **WHEN** the initialization change is reviewed
- **THEN** its documentation, specifications, templates and configuration guidance are in English, with no remaining instruction to use French

### Requirement: License preservation
Initialization SHALL preserve LICENSE byte for byte and retain the existing
repository history.

#### Scenario: Change inspection
- **WHEN** the maintainer compares the initialization branch with its main baseline
- **THEN** LICENSE is unchanged and the base commit remains an ancestor of the branch
