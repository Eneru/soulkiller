# Design

## Context

See [proposal.md](proposal.md) for motivation. The foundation is on main, while
its initialization OpenSpec change remains active. There is no application code
or integrated product specification. The current change prepares a study.

## Decisions

1. Keep the complete topic in
   [docs/research/soulkiller-feasibility-study.md](../../../docs/research/soulkiller-feasibility-study.md).
   Link it from the roadmap and README so new chats can recover the context.
   This avoids scattering the study scope across conversation-only notes.

2. Use a documentation-only OpenSpec change with `skip_specs: true`.
   The CLI supports this when behavior does not change. Adding a fictional
   product requirement would prematurely commit the project to an architecture.
   Product specifications will follow the study and maintainer decisions.

3. Separate the research work packages from product stages. Use a shared matrix,
   evidence labels and an unanswered decision register. A preselected stack
   would obscure tradeoffs; candidate references only seed the research.

4. Separate facts, style and conversation memory, and local extraction from
   storage/inference location. RAG is the user's preferred hypothesis, with
   alternative costs and limitations to be assessed during the future study.

5. Submit the topic through a draft PR and keep issue proposals in the roadmap.
   Topic approval precedes issue publication or adoption decisions.

## Risks / Trade-offs

- Candidate references may change -> the study must record versions, dates,
  licenses and primary evidence; this preparation makes no benchmark claims.
- Open product questions could be mistaken for defaults -> keep Q1-Q8 unanswered,
  distinguish assumptions and ask before dependent experiments.
- A full study could grow too broad -> start with W1, compare against declared
  constraints and propose the smallest increment for review.
- Preparation could be mistaken for completion -> future study acceptance boxes
  remain unchecked and no performance or application test results are claimed.

## Validation approach

Run strict OpenSpec validation and Git whitespace checks in the devcontainer.
Check changed Markdown links and verify that the diff contains only the planned
documentation and change metadata. Compare LICENSE with the main baseline.
The container configuration is unchanged, so an image rebuild is unnecessary.
