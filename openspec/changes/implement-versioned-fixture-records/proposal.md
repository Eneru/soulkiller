# Why
The accepted runner returns typed in-memory observations and the reviewed run
store holds opaque bytes. Add the smallest bridge: a strict, versioned record for
one accepted fixture's result, without coupling serialization to scheduling.

# What changes
- Encode/decode one FixtureRun using exact version-1 JSON, bound to the caller's
  accepted fixture ID, format and source revision.
- Preserve exact TXT/PDF evidence, supervisor failures, unavailable observations
  and unfinished reasons within the existing encoded storage ceiling.
- Document every new or changed function, including private helpers; explain
  low-level/OS assumptions when relevant. Record this maintainer rule in agent
  and contribution guidance.
- Add independent known-wire, malformed-input, boundary and real-store tests.

# Impact
This ninth small tranche follows approved evaluate-text-pdf-extraction and
confirmed PR #21 merge. Python/runtime/editor/CI/dependencies stay unchanged.
No source I/O, parser execution, automatic checkpoints, whole-run report,
environment inventory, scoring, comparison, CLI, model or provider is added.
The existing run_corpus and child-response protocols retain their behavior.
