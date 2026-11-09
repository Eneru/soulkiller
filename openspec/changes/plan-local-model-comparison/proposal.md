## Why

PR #31 moved citation formatting into Soulkiller and reached 5/5 mechanically
valid generations with Qwen3-1.7B. The model still interpreted two conflicting
descriptions of one lamp as two possessions. The
[paired trial](../../../docs/research/structured-dialogue-trial.md) records
four answers meeting both the mechanical and human criteria.

## Proposed experiment

Compare the current Qwen3-1.7B Q8_0 profile with the official Qwen3-4B Q4_K_M
artifact on the same synthetic Inez questions. Use structured citations in
both profiles and keep the same offline CPU, memory, time and token limits.
The primary question is whether the candidate explicitly describes the lamp
colour disagreement and retains the passing results in the other cases.

Approval authorizes one implementation PR, explicit provisioning of the
pinned candidate (about 2.33 GiB) and the bounded offline comparison. A
larger resource profile, any remote endpoint and any paid run require their
own decision. Inference placement remains a later product decision.
