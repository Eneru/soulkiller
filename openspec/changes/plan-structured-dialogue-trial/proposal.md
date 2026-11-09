## Why

PR #29 ran Qwen3-1.7B offline. Eight of nine generations in the final matrix
failed citation validation. The accepted conflict reply cited both passages
and described two lamps where the sources disagreed about one. The current
wire format asks the model for the same IDs in both prose and a list. The
report gives the rejection category, so the share attributable to this
duplication is unknown. See the [trial report](../../../docs/research/local-model-trial.md).

## Proposed experiment

Compare the current format with a structured format on the **same pinned
Qwen3 model and synthetic questions**. In the variant the model selects source
IDs once, in a structured field. Soulkiller validates those IDs and renders
the citation markers and exact excerpts. A reviewer checks that the prose
follows the cited facts, keeps uncertainty and preserves disagreements.
Review both scores before deciding whether to test a different model.

Approval authorizes one implementation and a bounded offline comparison with
the existing weights. Keep the current command behavior as the baseline and
make the variant explicit. A new model download, provider, remote endpoint,
real personal data or production inference choice requires separate review.
