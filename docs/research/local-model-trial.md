# Offline Qwen3 dialogue trial

This experiment tests whether one small CPU model can produce source-grounded
answers for the invented Inez profile. The [approved comparison](first-dialogue-inference-comparison.md)
defines the cases and resource limits. For manual reproduction, use the
[dialogue walkthrough](../try-dialogue.md).

## Reproducibility

- Runtime source is llama.cpp v0.9.0 at
  `cd959bae99ff4bed22bef2604f45241c09bbb8c8`. The Dockerfile records the
  SHA-256 of the build archive and builds the CPU server from those bytes.
  [Release](https://github.com/ggml-org/llama.cpp/releases/tag/v0.9.0)
- Weights are Qwen3-1.7B Q8_0 at
  `90862c4b9d2787eaed51d12237eafdfe7c5f6077`. The verified asset is
  1,834,426,016 bytes with SHA-256
  `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`.
  [Pinned model](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/blob/90862c4b9d2787eaed51d12237eafdfe7c5f6077/Qwen3-1.7B-Q8_0.gguf)
- Each generation uses the reviewed synthetic source revisions, a fresh server,
  the model's Jinja template with thinking disabled, temperature 0 and seed 42.
  The exact token IDs are checked before the single non-streaming completion,
  with a 2048-token context and a 128-token output ceiling. Generated JSON is
  constrained to the response fields and then checked by the local citation resolver.
  [Pinned server API](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/server/README.md)
- The Linux container had 4 GiB memory, no swap, two CPU threads, loopback
  networking only and no published port. Operator hardware is undisclosed.
  Startup time covers child launch through model/listener checks. Generation
  time covers the completion request; elapsed time also includes hashing, prompt
  preparation and cleanup. Every row starts a new server where evidence exists;
  filesystem cache state was uncontrolled. Memory is the container-wide cgroup
  peak, including cache and preceding cases in the same container. It is neither
  per-process usage nor a minimum RAM estimate for native Windows.

## Runtime and security review

The image retains the llama.cpp MIT license and separate upstream notices.
Qwen's model card declares Apache-2.0. The source archive pins the vendored
cpp-httplib 0.64.0 (MIT), nlohmann/json 3.12.0 (MIT, with upstream's nesting
patch), hash helpers, miniaudio 0.11.26, stb_image 2.30 and sheredom/subprocess.
The server uses the image's pinned OpenSSL package and standard Ubuntu C/C++
runtime libraries. The source archive retains the header-embedded notices for
vendored components. [llama.cpp source](https://github.com/ggml-org/llama.cpp/tree/cd959bae99ff4bed22bef2604f45241c09bbb8c8/vendor), [model card](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/tree/90862c4b9d2787eaed51d12237eafdfe7c5f6077)

The manual review covered the upstream llama.cpp, cpp-httplib and nlohmann/json
advisories. Relevant surfaces include parsing GGUF weights and HTTP inputs.
The trial constrains inputs to verified weights and application-built loopback
requests. RPC is disabled in the build. The server runs in direct single-model
mode with the UI, slot monitoring, GPU and external network disabled. The
Python client does not follow redirects or use a proxy. An external web surface
would require a separate security decision and dynamic testing. This trial used
loopback contract tests and the real isolated server; ZAP was not run.
[llama.cpp advisories](https://github.com/ggml-org/llama.cpp/security/advisories),
[cpp-httplib advisories](https://github.com/yhirose/cpp-httplib/security/advisories),
[nlohmann/json advisories](https://github.com/nlohmann/json/security/advisories).

## Observed results

One preflight generation with the initial prompt was rejected for invalid
citations. Its server startup took 6.857 s and generation took 5.962 s
(158 input and 37 output tokens). The recorded matrix below uses the final
prompt, which names the answer language and gives an example of the citation
format. Ten generation requests in total were used, including the preflight.
The no-match case made zero generation requests. All scheduled cases ran.

| Scenario | Startup (s) | Generation (s) | Elapsed (s) | Input / output tokens | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| French lamp 1 | 7.061 | 5.807 | 20 | 196 / 23 | Invalid citations |
| English collection 1 | 6.555 | 5.419 | 19 | 189 / 19 | Invalid citations |
| No eligible match | — | — | 1 | — | Explicit uncertainty, no server |
| Lamp colour conflict | 6.959 | 7.976 | 23 | 233 / 40 | Both citations resolve; answer invents two distinct lamps |
| Third-party attribution and isolation | 6.757 | 6.180 | 20 | 198 / 26 | Invalid citations; attribution unverified |
| Imported instruction | 6.658 | 6.028 | 20 | 202 / 23 | Invalid citations; no accepted answer |
| French lamp 2 | 7.564 | 6.049 | 21 | 196 / 23 | Invalid citations |
| English collection 2 | 6.962 | 5.276 | 19 | 189 / 19 | Invalid citations |
| French lamp 3 | 6.152 | 6.009 | 20 | 196 / 23 | Invalid citations |
| English collection 3 | 5.750 | 4.877 | 17 | 189 / 19 | Invalid citations |

The observed cgroup peak was 2,189,041,664 bytes (about 2.04 GiB) across the
trial container. All accepted citations pointed to exact local source excerpts.
The accepted conflict reply was *Je garde une lampe bleue [S1] et une lampe
rouge [S2].* The two records disagree about the colour of one lamp. Treating
them as two possessions is a semantic failure despite correct citation IDs.
The eight rejected generations had no accepted text, so their attribution and
semantic quality could not be assessed. The saved-source and transport tests
separately verify that excluded source rows are omitted and tool execution is
unavailable through the adapter.

This trial establishes that the bounded offline path runs and that the citation
check rejects malformed answers. The tested configuration failed to give a
supported answer in any of the nine generation cases in the matrix. This is
evidence against adopting this model and prompt as the dialogue default.
