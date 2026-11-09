# Paired offline citation trial

The structured format passed citation validation in **5/5** generations,
compared with **1/5** for the baseline. It met both mechanical and human
criteria in **4/5** cases. The two formats still treated contradictory
descriptions of one lamp as two lamps, so the variant missed the agreed
smoke-test threshold.

## Method

Each pair used the same saved Inez evidence, exact question, literal evidence
expression and answer language. The runtime, Qwen3-1.7B Q8_0 weights, sampling
and resource limits were those from [PR #29's trial](local-model-trial.md).
Baseline `--local-model` asked for IDs in the prose and a list. With
`--local-model-structured`, the model selected IDs in the list and Soulkiller
validated and rendered the markers. The variant changed the citation
instructions and schema together.

The comparison used an offline Linux devcontainer with 4 GiB of RAM, no swap
and two CPUs. Each generating case had a fresh server, with no controlled
filesystem cache state. A local measurement wrapper counted adapter and
completion calls and retained only synthetic observations in an ignored
folder separate from the saved evidence. All six pairs ran. Ten generations
ran without retries. Both no-match cases had zero adapter and completion calls.
Replaying the recorded completions through the final code reproduced the CLI
outputs and diagnostic categories.

## Mechanical checks and human review

| Case | Baseline | Structured |
| --- | --- | --- |
| French lamp | Correct prose and a valid list, rejected for missing inline marker | Correct first-person French answer and resolving citation |
| English collection | Correct prose and a valid list, rejected for missing inline marker | Correct first-person English answer and resolving citation |
| No eligible match | Explicit uncertainty, zero calls | Explicit uncertainty, zero calls |
| Lamp colour conflict | Both citations resolve, but the prose invents two lamps | Both citations resolve, but the prose invents two lamps |
| Corin's collection and private marker | Missing inline marker; claims Corin's collection in the first person and leaves the marker unknown | Attributes the collection to Corin, leaves the marker unknown and cites the excerpt |
| Archived instruction | Missing inline marker; leaves the requested marker unknown | Leaves the requested marker unknown and cites the archived passage as evidence |

All ten generations passed transport and response shape checks. Each of the
four baseline citation rejections reported `inline_id_mismatch`. Their lists
held eligible IDs, but their prose omitted the inline markers. The human
assessment includes the text of rejected synthetic completions for diagnostic
purposes. The CLI withheld that text. The scores below exclude the separate
no-generation pair.

| Score | Baseline | Structured |
| --- | ---: | ---: |
| Mechanical citation acceptance | 1/5 | 5/5 |
| Human content checks | 3/5 | 4/5 |
| Both checks on the same generation | 0/5 | 4/5 |

The structured French reply was *Je garde une lampe bleue. [S1]*. The structured
conflict reply was *Je garde une lampe bleue. Je garde une lampe rouge. [S1]
[S2]*. Its markers resolved to the right pages. The claim of two possessions
was unsupported, and the reply failed to explain the disagreement. The
results support the structured format as a way to reduce citation errors in
these cases. A separate decision is needed before another model trial.

## Resource observations

The table lists prompt/output tokens and startup/generation times. Startup
covers child launch through model/listener checks. Generation covers the
completion request. Wall time also includes model verification, prompt
preparation and cleanup.

| Case | Baseline tokens | Structured tokens | Baseline startup / generation (s) | Structured startup / generation (s) |
| --- | ---: | ---: | ---: | ---: |
| French lamp | 196 / 23 | 185 / 23 | 5.961 / 4.971 | 5.543 / 4.793 |
| English collection | 189 / 19 | 178 / 19 | 5.744 / 4.562 | 7.553 / 4.683 |
| Lamp colour conflict | 233 / 40 | 222 / 35 | 5.744 / 7.091 | 7.151 / 6.336 |
| Corin's collection and private marker | 198 / 26 | 187 / 32 | 6.245 / 5.247 | 5.744 / 5.492 |
| Archived instruction | 202 / 23 | 191 / 23 | 6.950 / 5.330 | 5.742 / 5.353 |

Wall time per generation case was 15.339–18.698 s. Peak cgroup memory was
2,206,728,192 bytes (about 2.06 GiB) across the full container, including file
cache. These observations cover the synthetic Linux experiment. Native Windows
latency and resource use remain unmeasured.

Use the [dialogue walkthrough](../try-dialogue.md) to reproduce the known
French, English and conflict cases.
