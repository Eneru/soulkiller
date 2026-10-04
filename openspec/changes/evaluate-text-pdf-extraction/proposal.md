# Proposal: evaluate native text and PDF extraction

**Status:** plan and proposed specifications for maintainer review only. The
maintainer requested preparation without implementation on 2026-10-04. No
runtime, dependency, fixture generator or benchmark is delivered in this PR.

## Why

Soulkiller has reviewed input and persona intent but no extraction measurements.
A small synthetic comparison will establish whether native PDF text and usable
source references can be recovered before choosing application languages or RAG
components. It makes the first part of E1 actionable without real-model trials.

## What Changes

- Propose a credential-free Python evaluation tool for UTF-8 TXT and born-digital
  French/English PDF, comparing pypdf with Docling's native, model-free pipeline.
- Define fixture selection, source references, observable failures, resource
  bounds, independent annotations and a reproducible comparison record.
- Specify tests, at least 70% executable line coverage and Python DevSecOps
  checks from the harness's first implementation, using existing CI event rules.
- Record the confirmed 8 GiB CPU-only reference profile, 16 GiB comparison, and
  initial sole-local-manager choice with unauthenticated interlocutor labels.
- Keep structured/model-based Docling, OCR, retrieval, generation and native
  Windows delivery in later reviewed work. This narrows E1; it does not resolve
  the full structured-layout comparison or local-versus-remote inference.

## Capabilities

### New Capabilities

- `text-pdf-extraction-evaluation`: explicit synthetic extraction runs with
  comparable evidence, bounded execution and honest quality/resource reports.

### Modified Capabilities

None. No integrated application capability is changed. The proposed delta below
is an experimental-tool contract, not an implemented application requirement.

## Impact

This PR contains Markdown and OpenSpec YAML only. Implementation would introduce
an isolated experimental Python environment, locked candidate/test/check tools,
container changes and credential-free checks. Candidate pins, dependency/license
inventory, enforcement mechanisms and review checkpoints are in design.md.
It contributes to E1 and roadmap R2/R3/R6 (Refs #7); broader R1/F1 and native
Windows results remain incomplete. No issue, service, provider, account, workflow,
repository setting or LICENSE change is part of this delivery.
