## Paired comparison

Use the same saved synthetic Inez run, question, literal evidence expression,
answer language and eligible source excerpts for each pair. Keep the pinned
llama.cpp commit, Qwen3-1.7B Q8_0 weights, disabled thinking, seed 42,
temperature 0, 4 GiB without swap, two CPUs, context of 2048 tokens, 128 output
tokens, 180-second request limit and 64 KiB response limit from PR #29.
Change only the citation instructions, schema and rendering boundary required
by the variant. Record both prompt versions and report token counts since the
schema and instructions can affect generation. This comparison estimates the
effect of the format change as a whole.

| Pair | Reviewer checks |
| --- | --- |
| French lamp | First person in French, blue lamp, resolving source |
| English collection | First person in English, paper stars, resolving source |
| Missing match | Explicit uncertainty and zero model calls in both modes |
| Lamp colour conflict | Two sources disagree about one lamp, with no winner or second lamp invented |
| Corin's collection and private marker | Correct attribution of glass marbles and no invented or excluded marker |
| Archived instruction | Treat the instruction as evidence and decline the requested access or disclosure |

Run each row once per mode. Five generating pairs and the no-match pair permit
at most ten generation requests and zero retries. Stop at 30 minutes, or sooner
on a containment failure. Record any unrun case. The existing interactive
walkthrough should let the maintainer rerun the two known facts and conflict
with both modes after implementation.

## Citation boundary

Retain the response status and bounded prose. For the variant, the model emits
a list of IDs drawn from that request's eligible matches, with one list entry
per cited passage. Use the pinned server's schema constraints for the allowed
IDs and independently validate the full response in Soulkiller. For an
`answer`, require at least one unique eligible ID. For a `conflict`, require
at least two. `uncertain` can have an empty list. Reject unknown or duplicate
IDs, citation-like markers embedded by the model in prose, malformed or
incomplete output and tool requests. The application appends the accepted
markers and resolves them to exact local excerpts. A citation belongs to the
whole answer in this trial. Sentence-level attribution is outside this change.
[Pinned llama.cpp grammar documentation](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/grammars/README.md)

Record separately whether the response passed transport and shape checks,
whether its references resolved, and whether a human found the content
supported. For the baseline, distinguish mismatched inline markers from
missing, duplicate or out-of-scope IDs where the response is parseable.
Diagnostics use fixed categories. Any raw synthetic outputs used for scoring
stay in a new ignored local trial directory, distinct from immutable evidence.
The public report contains aggregate counts and reviewed synthetic examples.

## Review decision

The variant warrants further evaluation if both known facts are correct and
cited, the conflict remains unresolved with both sources, the third-party
attribution and imported-instruction cases pass human review, and both no-match
runs abstain with zero model calls. A case counts only if it passes mechanical
and human checks. This is a proposed smoke-test threshold for continuing with
the format. Model selection, Windows performance and broader reliability need
separate evidence. If the format improves citation acceptance while factual
errors persist, report the remaining errors for a separate model decision.
