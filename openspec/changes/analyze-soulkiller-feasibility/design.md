# Research design

## Context

See [proposal.md](proposal.md) and the approved
[brief](../../../docs/research/soulkiller-feasibility-study.md).
PR #2 is merged and issue #3 tracks W1-W6. The study has no access to a
representative Windows target machine or an approved personal corpus.

## Decisions

1. Perform desk research using official documentation, project sources, model
   cards and original papers. Record the consultation date and any observed
   release; a moving documentation snapshot is not an installed version.
   Separate documented claims from recommendations and unknown measurements.

2. Deliver three linked documents: the report, evaluation proposal and decision
   register. Keep candidate-specific evidence in the report; the evaluation
   defines future experiments and the register presents choices to the maintainer.
   Links from README and the roadmap make the work recoverable in another chat.

3. Evaluate extraction separately from inference and facts separately from style
   and conversation memory. Compare a lightweight baseline before more complex
   options. No proposed architecture is treated as adopted by this study.

4. Use Windows on a household PC as the confirmed source-machine priority.
   Exact CPU/RAM and corpus/budget remain questions. Compare deployment
   alternatives conditionally when maintainer answers are unavailable.

5. Execute only documentation/OpenSpec/Git checks in the existing devcontainer.
   Do not install candidate libraries, fetch model weights, run personal-file
   scans, or interpret paper/provider benchmarks as Soulkiller measurements.
   New benchmark or implementation work needs a reviewed scope and dependencies.

## Risks and tradeoffs

- Broad library coverage can hide operational costs -> compare capability,
  licensing, native packaging, data flow and failure behavior together.
- Source snapshots evolve -> retain specific primary URLs and access date;
  select and pin actual versions only for approved experiments.
- Typical-PC limits are qualitative -> propose test profiles for approval and
  publish resource formulas instead of unsupported latency/RAM guarantees.
- Routing defaults could contradict local-only needs -> evaluate explicit local
  endpoints and egress restrictions before any OmniRoute adoption.
- Product questions are unresolved -> keep a decision register; do not turn
  unanswered questions into implied authorization.

## Delivery and validation

Validate all OpenSpec changes strictly, Markdown links, scope and Git whitespace
inside the devcontainer. Verify LICENSE byte for byte against the main baseline.
Record that research is completed but product decisions, experiments and human
review remain pending. No image rebuild is required for documentation changes.
