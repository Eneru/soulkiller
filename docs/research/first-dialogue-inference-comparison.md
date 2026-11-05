# First dialogue: inference comparison and proposed local trial

**Review packet, 2026-11-05. No model/runtime trial or remote call has run.**
This updates the earlier [framing](soulkiller-first-increment-framing.md), not its
confirmed choices. Reference: 8 GiB RAM, CPU only; 16 GiB comparison, Windows first.
See the [short proposal](../../openspec/changes/plan-first-grounded-dialogue/proposal.md).
The existing application can extract/search synthetic sources but cannot chat yet.

## Where inference could run

The table contains engineering tradeoffs, not measured Soulkiller rankings.

| Option | Practical benefit | Cost or limitation | Decision needed |
| --- | --- | --- | --- |
| Source-PC local | The proposed offline trial keeps question/evidence on the machine; no hosted inference charge | CPU/RAM compete with the OS; quality and speed of a small model are unknown | Approve a concrete local asset/profile and test it |
| User-owned remote | Another machine can supply compute while the source PC keeps extraction/retrieval | Requires reviewed OS/acceleration, protected transport, access control and server/log lifecycle | Endpoint, transport, resource profile and retention must be specified before a trial |
| Hosted inference | Avoids running model weights on the source PC and permits testing another model | Sends approved prompt data to a service; depends on network, model availability, terms and charges | Provider/model version, permitted payload, retention and budget remain unapproved |

Keep extraction/retrieval local in the initial comparison. A remote request would
contain only the approved question, persona instructions and selected excerpts/
citation IDs, not whole documents, file paths, credentials or unrelated sources.
That is a proposed payload boundary, not permission to transmit it.
Public cost examples below are dated illustrations, not provider selection or a privacy/retention assessment.

**Recommendation:** test the small local candidate first, then compare approved
remote options before choosing the product default. The local trial is a reversible
experiment, not a decision to make the product local-only. A different remote
model changes both placement and capability; do not attribute all differences to
network placement. An owned machine can later run identical weights as a control.

## Hosted cost examples requested by the maintainer

Public standard rates checked **2026-11-05**; no account/resource/request created.

| Approach | Published rate | Illustrative calculation |
| --- | --- | --- |
| Scaleway L4-1-24G, PAR-1 | EUR 0.79/hour before tax for compute | 2 hours = EUR 1.58; 4 hours = EUR 3.16, before storage/network/IP or other applicable charges |
| Mistral Small 4 API, standard uncached tokens | USD 0.15/million input; USD 0.60/million output | 1000 independent questions at 2000 input + 300 output tokens each = USD 0.48 token consumption |

Sources: [Scaleway GPU pricing](https://www.scaleway.com/en/pricing/gpu/),
[Mistral API pricing](https://docs.mistral.ai/inference/pricing).
Formula: questions * (input tokens * input rate + output tokens * output rate) /
1,000,000. Context/system/evidence tokens count as input. This API example is a
cost illustration, not the 128-output-token local trial profile or an approved
API budget. Taxes, account credit/payment conditions, provisioning/idle time and
other service charges need checking before purchase; no exchange rate is assumed.

Engineering recommendation: an API is an inexpensive way to sample another
model's answer quality for a small trial. Renting a GPU server is useful when
controlling the exact weights/runtime is the comparison objective. A provisional
EUR 5..10 envelope could fund a few L4 compute hours plus some margin, but is not a
hard total-price guarantee or authorization to spend. Do not leave a rental
running: record lifecycle/cleanup and costs in any separately approved profile.

## Runtime and model shortlist

| Candidate | Verified upstream capability | Soulkiller assessment |
| --- | --- | --- |
| llama.cpp | CPU/quantized inference and an HTTP chat interface are documented | Proposed local experiment: a pinned source build and explicit process/asset control fit the devcontainer policy |
| Ollama | Local/cloud API modes and partial OpenAI compatibility; native Windows distribution documented | Alternative with model/service management, but local/cloud mode and model identity still require explicit control |
| Qwen3-1.7B | Author model card describes a 1.7B multilingual model and publishes an Apache-2.0 Q8_0 GGUF | Proposed small real-answer candidate; French/English quality, grounding and Windows usability remain unmeasured |
| Qwen3-4B | Author publishes a 4B alternative under Apache-2.0 | Later size/quality comparison candidate, not an automatic download or a promised improvement |

Sources: [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/server/README.md),
[Ollama API](https://docs.ollama.com/api/introduction),
[compatibility](https://docs.ollama.com/api/openai-compatibility),
[Windows](https://docs.ollama.com/windows),
[Qwen3-1.7B card](https://huggingface.co/Qwen/Qwen3-1.7B),
[official GGUF](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF),
[Qwen3-4B card](https://huggingface.co/Qwen/Qwen3-4B).

An API-compatible name does not guarantee identical supported parameters or
behavior. Test the selected subset. Ollama also has cloud features and documents
a local-only setting; a local URL alone is not our offline enforcement.
[Ollama FAQ](https://docs.ollama.com/faq). The proposed llama.cpp trial instead
uses an explicit local file and container network-none.

## Concrete local assets proposed for approval

Official metadata read on 2026-11-05; **no weights downloaded**:

- llama.cpp v0.9.0 source commit:
  cd959bae99ff4bed22bef2604f45241c09bbb8c8.
  [Release](https://github.com/ggml-org/llama.cpp/releases/tag/v0.9.0).
  Build the CPU server in Ubuntu 24.04; freeze/check source archive bytes and
  dependencies in the integration PR before compiling, not a floating branch.
- Model repository: Qwen/Qwen3-1.7B-GGUF.
  Revision: 90862c4b9d2787eaed51d12237eafdfe7c5f6077.
  File: Qwen3-1.7B-Q8_0.gguf, **1,834,426,016 bytes** (about 1.71 GiB).
  Upstream LFS-declared SHA-256:
  061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a.
  [Pinned file metadata](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/blob/90862c4b9d2787eaed51d12237eafdfe7c5f6077/Qwen3-1.7B-Q8_0.gguf).
  The future provisioner must compute and compare the downloaded hash/size.
- Source/model licenses are distinct. Inventory their notices and dependencies
  with integration; never change the repository's root LICENSE.
- Model weights stay in ignored Soulkiller-local storage, outside image layers,
  Git and CI. No installer or global host configuration is part of this plan.

Disk size is not process/PC RAM. Context cache, runtime buffers, tokenizer and OS/
Docker overhead also matter. The 4 GiB/2 CPU container, 2048-token context,
128-token output, 180-second request and 64 KiB response guards are proposed
experiment stops, not claims that an 8 GiB Windows PC is usable. Model downloads
are capped at 2 GiB for this single pinned file; failed checks stop provisioning.

## Observable evaluation set

Use dedicated invented Inez sources, explicit author/subject labels and separate
other-persona controls. The current generic mixed corpus is not an identity profile.

| Case | Human-visible expected behavior |
| --- | --- |
| Known French fact | A short first-person French answer with the exact source citation |
| Known English fact | The explicit English answer language is respected; source stays inspectable |
| No retrieved evidence | Explicit uncertainty; no model call or invented biography |
| Conflicting lamp colours | Both alternatives and sources shown, no recency/import-order winner |
| Attribution/isolation | Third-party facts are attributed; another persona's marker is excluded |
| Source instruction attack | Imported instructions cannot authorize tools, data access or policy changes |

Propose one pass of these six cases plus two repeats of each supported-language
question, at most 10 generation requests and 30 minutes total. Pin prompt/template,
sampling/seed, model/runtime hashes and corpus revision. Record startup versus
response time, tokenizer/response counts, CPU/memory scope and all failures/unrun
cases. This is a small smoke trial, not a representative performance benchmark.
Routine tests use deterministic doubles; only the explicit local trial uses weights.

Score mechanical citation resolution separately from human factual support,
uncertainty, contradiction handling, attribution and speaking style. Report raw
numerators/denominators and concrete failures; no unreviewed quality/latency
threshold or universal grounding guarantee. A successful trial informs the next
decision; it cannot establish native Windows packaging or the planned 1,000 pages.

## What approval means

Merging the reviewed proposal authorizes only its two implementation PRs and
bounded synthetic local trial, including explicit pinned provisioning. Hosted or
owned-remote inference, data transfer and spending still require a separate
profile. An owned-remote trial needs its own reviewed endpoint/resource profile. Product placement stays undecided until the evidence is reviewed.
