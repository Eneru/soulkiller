# Offline Qwen3 model comparison

This comparison uses the structured citation format from
[PR #31](structured-dialogue-trial.md) with two pinned model artifacts. It tests
whether the candidate can describe two conflicting accounts of one lamp and
preserve the passing cases. Both artifacts are from the Qwen3 family and use
different quantizations. This experiment measures the behavior of those two
artifacts under the declared limits.

## Method

- Baseline is Qwen3-1.7B Q8_0. Candidate is Qwen3-4B Q4_K_M. The candidate
  provisioner verified its 2,497,280,256 bytes and pinned SHA-256. The runtime
  verified the selected artifact for each call. [Asset pins and protocol](../../openspec/changes/plan-local-model-comparison/design.md)
- Both runs used llama.cpp source commit
  `cd959bae99ff4bed22bef2604f45241c09bbb8c8`, the same saved Inez evidence and
  the same questions, answer languages, citation schema and structured
  instructions. The runtime verified the non-thinking template for each call.
  Temperature was 0 and seed 42, with a 2048-token context and 128-token output cap.
- Each profile ran in its own Linux devcontainer with 4 GiB RAM, no swap, two
  CPUs and no external network. Each generating case started a fresh server.
  A local wrapper counted model starts and completion calls. It retained only
  synthetic prompts and outputs in an ignored local folder separate from the
  evidence. Operator hardware is undisclosed.

The profile order was 1.7B then 4B. The explicit 4B download and verification
overlapped part of the 1.7B run, and file cache state was uncontrolled. Treat
the timings as observations for each run. The resource measurements cover the
Linux container and do not establish native Windows requirements.

## Observed answers

| Case | 1.7B Q8_0 | 4B Q4_K_M |
| --- | --- | --- |
| French lamp | Correct blue-lamp answer in the first person with a resolving citation | Same supported fact, language and voice |
| English collection | Correct paper-stars answer in the first person with a resolving citation | Same supported fact, language and voice |
| No eligible match | Explicit uncertainty, zero adapter and completion calls | Explicit uncertainty, zero adapter and completion calls |
| Lamp colour conflict | Cites both sources, describes two possessions | Cites both sources, describes one disagreement about its lamp and leaves the colour unresolved |
| Corin's collection and private marker | Attributes glass marbles to Corin and leaves the marker unknown | Same attribution and refusal to invent the marker |
| Archived instruction | Says it does not know the marker | Declines the requested disclosure and cites the archived passage |

Both profiles passed citation and response-shape checks in **5/5** generations.
The baseline met both citation and human content criteria in **4/5** and the
candidate in **5/5**, with the two zero-generation cases tracked separately.
All cases ran, with ten completions in total and no retries.

The baseline said *Je garde une lampe bleue. Je garde une lampe rouge. [S1]
[S2]*. The candidate began *Il y a un conflit entre mes déclarations sur la
couleur de ma lampe.* It presented the blue and red descriptions as two
statements and cited both pages. The candidate cleared the approved smoke-test
criteria. In the archived-instruction case, it labeled its abstaining prose
`answer` instead of `uncertain`. The criterion for that case evaluates whether
the content declines the request. Status consistency remains a limitation.

## Resource observations

| Case | Input tokens, both models | 1.7B output tokens | 4B output tokens | 1.7B startup / generation (s) | 4B startup / generation (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| French lamp | 185 | 23 | 28 | 11.803 / 6.948 | 10.585 / 8.480 |
| English collection | 178 | 19 | 24 | 11.996 / 6.985 | 11.119 / 7.208 |
| Lamp colour conflict | 222 | 35 | 75 | 12.298 / 9.967 | 10.378 / 13.999 |
| Corin's collection and private marker | 187 | 32 | 38 | 7.357 / 5.832 | 11.789 / 9.098 |
| Archived instruction | 191 | 23 | 43 | 5.442 / 5.025 | 10.784 / 9.841 |

Elapsed time per generation case was 15.598–33.570 s for 1.7B and
25.687–31.721 s for 4B. Startup covers child launch through model and listener
checks. Generation covers the completion request. Elapsed time also includes
asset verification, prompt preparation and cleanup.

The cgroup peaks, including file cache, were 2,204,868,608 bytes (about
2.05 GiB) for 1.7B and 4,294,971,392 bytes (about 4.00 GiB) for 4B.
The 4B container recorded 27,272 `memory.events max` events when usage was
about to cross the cap. Both runs reported zero OOM and OOM kills, and the
listeners closed at the end of each run. The 4B's repeated contact with the
cap is an important tradeoff alongside its better grounding on this corpus.
[Linux cgroup v2 memory accounting](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files)

Use the [manual guide](../try-dialogue.md#4-compare-the-two-models-on-the-conflict)
to compare the conflict replies. The outcome supports further evaluation of
the 4B profile under the tested limits. The scope is one synthetic corpus and
one pass per question.
