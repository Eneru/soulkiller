## Why

Source search is usable after merged PR #26. The next visible outcome is asking
an invented persona a question and reading an answer with inspectable citations.

**Approved in merged PR #27. The first implementation delivers the scripted ask journey.** Read the
[local/remote comparison](../../../docs/research/first-dialogue-inference-comparison.md)
for the approved local trial plan and separate remote decisions.

## Proposed first journey

A small CLI experiment would let the maintainer select the invented Inez profile,
a saved synthetic run, a question, an answer language (fr/en), and a literal
evidence expression. For example: ask Inez about her lamp using "lampe" to retrieve
the relevant passages. Automatic semantic question-to-query retrieval is later.

Expected result: a short first-person answer with [S1] and an exact source excerpt,
or explicit uncertainty. Two conflicting sources remain visible without an
automatic winner. Each call is independent; accepted automatic-memory product
requirements are deferred, not replaced with a manual-saving workflow.

## Recommendation for review

Start with one local, CPU-only real-model experiment using llama.cpp and the
author-published Qwen3-1.7B Q8_0 artifact in the comparison. This is a proposal,
not a final local-versus-remote product decision or a claim about 8 GiB Windows.
Owned-remote and hosted alternatives, with dated cost examples, remain available
after endpoint/data/cost approval.

**Approval of this complete packet authorizes the following development scope:**
one source-grounded answer journey, a reproducible container-local runtime,
explicit provisioning of the pinned model (about 1.83 GB download), and the bounded
synthetic local smoke trial. Provisioning/runtime start remain explicit operations;
ordinary build/start/CI never downloads model weights or runs real inference.

## Delivery in small PRs

1. Deliver the complete ask journey with synthetic Inez fixtures and deterministic
   model doubles; include the approved response validation and human-readable sources.
2. Integrate the pinned real runtime, explicit model provisioning and bounded local
   trial; deliver a manual question/answer demo and actual measurements.

Each PR is a complete reviewable unit. The first validates application behavior;
it does not pretend that a model double demonstrates real persona quality.
The second supplies the real-model experience, not more storage foundations.

## Exclusions

No hosted call, remote deployment, money spend, real personal data, persistent
conversation memory/style learning, GUI, new index, fine-tuning or OmniRoute
service is authorized. A remote trial needs its own endpoint, data/retention
contract and budget. Production architecture and native Windows delivery stay open.
