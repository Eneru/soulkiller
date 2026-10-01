# Proposal

## Why

Soulkiller has a development foundation but no agreed path from local personal
files to an evidence-grounded digital persona. A reviewable research brief will
guide the next study and expose choices before adopting technologies.

## What Changes

- Add a study brief covering local text/PDF, image and video extraction,
  provenance, retrieval and persona conversations.
- Frame RAG as the leading hypothesis while retaining a resource-based
  comparison with prompting, fine-tuning and combinations.
- Define comparison criteria, candidate references, synthetic evaluation,
  deliverables and maintainer questions.
- Add a roadmap entry and README link; record preparation in the changelog.

Confirmed: local extraction, multimodal inputs, technology/language comparison
and maintainer decisions. Assumptions such as offline inference, hardware,
formats beyond those listed and persona behavior remain explicit questions.
The study itself, benchmarks, product code, dependency installation, provider
configuration and technology adoption are excluded from this preparation.

## Capabilities

### New Capabilities

None. This is a documentation-only planning change.

### Modified Capabilities

None. No application behavior or existing requirement changes.
The metadata sets `skip_specs: true`, as supported by the OpenSpec CLI.
The existing initialization documentation requirement provides context;
future product decisions will need their own behavior-specific specifications.

## Impact

Affected files: the research brief, README, roadmap, changelog and this OpenSpec
change. No APIs, runtime dependencies, devcontainer settings or workflows change.
The study topic is submitted through a draft PR for human review; proposed issues
remain unpublished until maintainer approval.
