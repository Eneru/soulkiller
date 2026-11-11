## What stays on the client

Reuse the Inez synthetic fixture, local evidence selection, prompt builder,
response validation and citation renderer. Compare the structured 4B mode
against an explicit remote trial mode with the same artifact hash, pinned
llama.cpp source/build settings, prompt, citation constraints and generation
settings. Keep retrieval and source resolution local. If evidence is empty
or the fixture is not the approved synthetic run, the remote trial does not
start a connection. Verify the saved fixture against reviewed synthetic
content and the trial question/language/query tuple against the approved
cases before constructing any outbound request.

## Request and worker

Send one versioned, bounded UTF-8 JSON request over SSH standard input. The
payload carries only the generated synthetic prompt and its request-local
citation IDs. Keep generation settings and the artifact pin fixed at both ends.
The prompt includes the approved synthetic question and excerpts, so those
bytes do cross the boundary. File paths, complete documents, source-location
metadata, other questions, histories, memories and secrets stay local.
Return only one bounded JSON result with the model response and bounded
runtime measurements. Treat all worker output as untrusted. Only the client
validates and resolves citation IDs. Never use the reply to choose a file,
execute a command or rewrite the saved run.

Use an explicit endpoint profile and a dedicated key with an independently
verified host key. The profile, key and known-hosts file live in ignored
repository-local storage. Use a pinned OpenSSH client in the devcontainer
(check the existing image first), batch mode, a fixed destination per
invocation and a dedicated known-hosts file with strict checking. Disable
ambient SSH configuration, agent use, forwarding, proxies, interactive
prompts and session reuse. Use a dedicated restricted key and fixed remote
command with no PTY or forwarding. The trial will run over a private route
without exposing an inference API. The worker takes one request and starts
the existing guarded offline runtime in an isolated Linux container. Keep
SSH termination outside the inference container and verify that the container
has no external network. The worker gets access to the pinned runtime/model
and the request stream. It receives no source corpus mount, Docker socket or
host credential mount. The operator must approve any remote setup separately.
[OpenSSH client options](https://man.openbsd.org/ssh_config)
and [server key restrictions](https://man.openbsd.org/sshd.8).

Cap request and response at 64 KiB each, including framing. Reject oversized
or incomplete frames, extra output and unrecognized protocol versions.
Apply a five-second connection timeout and a 180-second end-to-end deadline
per question. The worker has its own shorter deadline (170 seconds from
session start), so a disconnected client cannot leave unbounded work.
Run one request at a time with no automatic retries, fallback or remote
downloads. Timeouts, failed checks and malformed output give a fixed
diagnostic and no answer. The client must terminate and reap its transport
process. The worker must release its runtime process and container on
completion, expiry or failure. Verify cleanup on forced disconnect before
the live comparison.

Keep prompt and completion content in memory during the remote request and
omit it from routine logs, diagnostics and process arguments. Review the
operator's SSH/session logging, crash dumps and storage policy before a
live run. SSH protects transport to the authenticated endpoint. The
operator must trust the endpoint and verify its actual runtime and data
handling. Keep any retained raw synthetic evidence in ignored local
storage and publish only approved reference limits and aggregate results.

## Paired trial and interpretation

Run the same five generation cases and no-match control from the
[offline comparison](../../../docs/research/local-model-comparison.md) in
both modes. Confirm prompt and citation-constraint equality locally.
Use separate clean client containers per arm with a declared 4 GiB cap,
no swap and two CPUs. Run the worker at the same CPU-only limits and record
its runtime pin and limits independently. Keep the local reference arm
offline. Record wall time from client command start to rendered answer,
client and worker cgroup memory peaks (including cache), model startup and
generation time, token counts, limits reached, and each failed or skipped
case. Report the two cgroup peaks separately. Use one pass per arm, with at
most ten generation attempts and a 30-minute overall limit. Stop on a
containment failure, identity mismatch, timeout or reached trial limit.
Report the test order and cache conditions.

A usable trial arm has five resolving and factually supported answers,
an abstention with zero inference on no match, and a maximum of 60 seconds
to answer each generation case. This latency target is proposed for the
manual smoke test. Score content, citations and response status separately,
including the known mismatch between the archived-instruction refusal and
its status label. Report how much client memory moves to the worker and what
happens to user-visible time. Different CPUs, networks and caches can affect
elapsed time even under identical resource ceilings. A faster-worker or
hosted comparison would require its own approved profile. Native Windows
performance and the production default remain open.
