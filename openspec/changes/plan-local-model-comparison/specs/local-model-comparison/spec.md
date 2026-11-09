## ADDED Requirements

### Requirement: Explicit model asset selection

The experiment SHALL offer an explicit offline Qwen3-4B Q4_K_M profile with
structured citations alongside the existing Qwen3-1.7B modes. Provisioning
SHALL verify the selected artifact's exact size and SHA-256 before create-only
placement in ignored local storage. Inference SHALL verify the selected asset
before launching the pinned runtime. Startup and routine checks SHALL remain
independent of provisioned weights.

#### Scenario: Candidate is unavailable

- **WHEN** the operator selects the candidate and its file is missing or fails verification
- **THEN** Soulkiller SHALL report the failure without downloading, replacing or selecting another model

### Requirement: Bounded offline model comparison

The trial SHALL compare the two pinned artifacts with identical structured
citation instructions, saved evidence and questions within the documented
offline CPU and memory limits. It SHALL stop after ten generations or 30
minutes, whichever comes first. It SHALL record the scope, mechanical checks,
human grounding assessment, resource observations and any unrun cases.

#### Scenario: No eligible evidence exists

- **WHEN** the evidence expression finds no eligible passage for either profile
- **THEN** Soulkiller SHALL report uncertainty without starting the model

#### Scenario: Two records disagree about one lamp

- **WHEN** a response cites both records but claims two possessions
- **THEN** the report SHALL record a factual-support failure even when both citations resolve
