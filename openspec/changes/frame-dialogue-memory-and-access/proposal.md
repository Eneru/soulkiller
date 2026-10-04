# Proposal

## Why

After merging PR #11, the maintainer supplied the next persona decisions.
Future implementation needs a durable record of uncertainty, contradictions and
speaking-style evolution, plus an access-model comparison before choosing rights.

## What Changes

- Record explicit uncertainty and sourced contradictions without automatic resolution.
- Record speaking-style evolution through explicit, inspectable and deletable changes.
- Preserve automatic memory saving/use, attribution and the exclusion of inferred preferences.
- Compare one local manager with separate accounts; select neither model.
- Add synthetic acceptance examples and identify remaining behavior/data-flow gates.
- Update research context, roadmap, README, OpenSpec context and CHANGELOG.

## Capabilities

### New Capabilities

None implemented. This is a product-decision and proposed acceptance packet.

### Modified Capabilities

None implemented. Use skip_specs: true because no application contract is delivered.
A separate reviewed behavioral change must define the remaining operational rules
before code or experiments. These decisions inform R1/F1; they do not complete R1.

## Impact

Markdown and OpenSpec YAML only. No stack, authentication implementation,
devcontainer change, model/provider, benchmark, data transfer or paid call.
No repository settings or issues are changed. LICENSE remains unchanged.
Personal network diagnostics are outside this repository change.
