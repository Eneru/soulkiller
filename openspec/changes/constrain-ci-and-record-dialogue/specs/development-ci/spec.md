## ADDED Requirements

### Requirement: Restricted CI execution
Builds and tests SHALL run only for pull requests targeting main or pushes of valid SemVer 2.0.0 version tags. Tags SHALL accept an optional lowercase v prefix and valid prerelease/build identifiers. Main/other branch pushes, manual dispatch, other PR targets and tag deletion SHALL not run builds or tests.

#### Scenario: Reviewed PR or version tag
- **WHEN** the event is a PR targeting main or a nondeleted valid version tag push
- **THEN** bounded credential-free foundation checks are eligible

#### Scenario: Unsupported event or malformed tag
- **WHEN** a branch push, non-main PR, manual event, deleted tag or malformed version is received
- **THEN** builds and tests are not executed; a malformed tag admitted by glob filtering performs only lightweight eligibility work

### Requirement: Tested bounded gate
The eligibility guard SHALL use no provider credentials or new dependency and SHALL be included in canonical static analysis and measured executable line coverage with a minimum of 70%. Existing readonly token, pinned checkout, container isolation and runtime bounds SHALL be preserved.

#### Scenario: Synthetic event matrix
- **WHEN** local tests exercise valid, invalid and boundary event/tag inputs
- **THEN** independent named cases report the expected eligibility without creating tags or starting Docker builds
