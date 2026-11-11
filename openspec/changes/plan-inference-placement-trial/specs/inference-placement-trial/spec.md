## ADDED Requirements

### Requirement: Explicit synthetic remote inference trial

The trial SHALL keep evidence selection, response validation and citation
resolution on the client. An explicit remote invocation SHALL send only the
bounded generated prompt and request-local citation IDs for an approved
synthetic fixture and trial case, in a single versioned request to a
privately approved and authenticated endpoint.

#### Scenario: A reviewed synthetic question has matching evidence

- **WHEN** the operator explicitly selects remote inference for the approved fixture and case and the endpoint passes its identity checks
- **THEN** the client SHALL send one request and render a validated response with citations resolved against the local run

#### Scenario: The request cannot leave the client

- **WHEN** no eligible evidence exists, the run or case is outside the allowlist, or the endpoint lacks approved configuration
- **THEN** the client SHALL make no outbound inference connection

#### Scenario: The configured host key does not match

- **WHEN** the transport cannot verify the configured host key
- **THEN** the client SHALL fail before sending prompt bytes and SHALL neither retry nor fall back

### Requirement: Bounded remote execution

The client and worker SHALL enforce a fixed model and runtime profile,
independent deadlines and request/response bounds. The worker SHALL run
inference with external networking disabled and SHALL release its owned
resources on completion or failure. The application SHALL omit request and
completion content from routine logs.

#### Scenario: The reply is rejected

- **WHEN** the reply is oversized, malformed, late or contains an invalid citation
- **THEN** the client SHALL report a bounded failure without rendering an answer or retrying

#### Scenario: The client disconnects during generation

- **WHEN** the session drops after generation has started
- **THEN** the worker SHALL release its inference resources by its own deadline

### Requirement: Comparable placement measurements

The live trial SHALL compare one pass of the same five generation cases and
one no-match control per arm with the same model artifact, runtime revision,
prompt, citation constraints and generation settings. It SHALL record
citation and factual quality, response status, elapsed client time, client
and worker memory separately, and any failures or skipped cases. The trial
SHALL stop after ten generation attempts or 30 minutes, whichever comes first.

#### Scenario: Offloading succeeds but misses the latency target

- **WHEN** citations resolve and the answer is supported but client elapsed time exceeds 60 seconds for a generation case
- **THEN** the report SHALL record the exceeded target separately from answer quality
