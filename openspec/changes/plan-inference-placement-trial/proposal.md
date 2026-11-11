## Why

The [offline comparison](../../../docs/research/local-model-comparison.md)
found that Qwen3-4B answered the lamp conflict correctly in the synthetic
trial. Its container repeatedly reached the 4 GiB memory boundary. Compare
running that same artifact locally and on an operator-owned Linux worker to
see how placement affects client memory, end-to-end wait and the sourced
answer. Keep model quality and placement as separate questions.

## Scope for review

Approval authorizes one small implementation PR for the opt-in transport,
one-shot worker and credential-free integration tests described here. The
maintainer can verify the end-to-end dialogue with a synthetic worker and
inspect citations from the original local corpus.

A separate private approval is required before provisioning or contacting a
real endpoint. It must cover the destination and access, resource profile,
data and retention rules, and cost. This proposal has a zero paid-service
budget. The live comparison and its report follow in a separate PR once
authorized. Hosted providers, real-person data, Windows performance claims
and a production placement decision are outside this packet.
