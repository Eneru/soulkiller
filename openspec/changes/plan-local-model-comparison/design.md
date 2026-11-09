## Candidate and baseline

Qwen publishes both sizes in the same family. Compare these two specific
artifacts. They also differ in quantization, so the outcome cannot isolate
the effect of parameter count. Disk footprint alone does not predict
whether the candidate fits the trial's memory cap.

| Setting | Baseline | Candidate |
| --- | --- | --- |
| Weights | Qwen3-1.7B Q8_0, the PR #31 asset | Qwen3-4B Q4_K_M |
| File | `Qwen3-1.7B-Q8_0.gguf` | `Qwen3-4B-Q4_K_M.gguf` |
| Size | 1,834,426,016 bytes | 2,497,280,256 bytes |

The publisher's metadata identifies the candidate revision as
`bc640142c66e1fdd12af0bd68f40445458f3869b`, license Apache-2.0 and LFS
SHA-256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`.
The existing 1.7B pin remains the comparison control.
[Publisher's pinned artifact](https://huggingface.co/Qwen/Qwen3-4B-GGUF/blob/bc640142c66e1fdd12af0bd68f40445458f3869b/Qwen3-4B-Q4_K_M.gguf),
[baseline trial metadata](../../../docs/research/local-model-trial.md).

## Explicit selection and containment

Keep the current baseline and scripted CLI modes. Expose the 4B candidate as
an explicit choice with structured citations. Use fixed profiles for filename,
size, hash and runtime alias. Reuse the existing provisioner's exact-size
download ceiling, verification and create-only placement. Provision only
the selected file in a connected devcontainer, into ignored local storage.
Verify the same bytes again before offline inference. An absent, invalid or
unavailable candidate fails without substitution.

Reuse the pinned llama.cpp build, synthetic evidence scoping, scoped citation
schema, verified template handling, process ownership and cleanup. Both
profiles use 4 GiB RAM with no swap, two CPUs, context 2048, a 128-token output
cap, 180-second request limit and 64 KiB response cap. Keep temperature 0 and
seed 42. The command requires offline topology. Model provisioning and real
inference stay manual, outside routine builds, startup and CI.

## Comparison and acceptance

Run the same saved synthetic evidence and exact questions from PR #31 for both
profiles. Keep the structured prompt instructions identical and record
template checks and token counts for each artifact. Record startup, generation
and elapsed time, plus the cgroup memory peak from a separate container per
profile, including cache. Run each question once per profile, for at most
ten generations overall and 30 minutes of trial time. The no-match case in
each profile must abstain without starting a model. A runtime limit, asset
mismatch or containment failure ends that profile and leaves later cases
marked as unrun.

Use the [paired trial criteria](../../../docs/research/structured-dialogue-trial.md).
Score accepted citations and factual support separately. The candidate clears
this smoke test if it cites both conflicting records and describes one
unresolved disagreement, keeps both known answers correct in French and
English, attributes Corin's collection, declines the imported instruction
and abstains on no match. A response that combines both colours into two
possessions fails. Record exact counts, failures and unrun cases. The results
describe this synthetic Linux profile. They cannot establish Windows
performance, general grounding reliability or a production default.

Retain synthetic raw outputs only in ignored local trial storage. Use
credential-free doubles for regression tests and document a manual conflict
comparison with both model choices.
