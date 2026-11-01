# Tasks

## 1. Preparation
- [x] 1.1 Confirm PR #20 merge and branch from clean updated main.
- [x] 1.2 Read the approved output contract and prepare the confined-storage design before code.

## 2. Implementation
- [x] 2.1 Add safe errors/constants, descriptor-confined create/open and source separation.
- [x] 2.2 Add bounded framed records with exclusive publication, interruption handling and read-only reopening.
- [x] 2.3 Add independent filesystem/frame/failure tests and preserve existing corpus/worker behavior.
- [x] 2.4 Update guides, README, roadmap, parent progress and CHANGELOG.

## 3. Verification and delivery
- [x] 3.1 Run canonical quality/security/audit/tests and all-source line coverage >=70%.
- [x] 3.2 Run the complete Python suite in a fresh bounded offline container.
- [x] 3.3 Validate strict OpenSpec, links, whitespace and unchanged LICENSE/Python runtime/editor/CI.
- [x] 3.4 Prepare exact staged Conventional Commit/ready-PR inputs and run offline App preflight.
- [x] 3.5 Obtain human review and confirm manual merge (PR #21).

After preflight, publish through the App and record live bot identity/signature/tree
verification in the PR; maintainer review and manual merge remain required.

## 4. Hosted build correction
- [x] 4.1 Confirm current APT artifacts and align curl-family patch pins after the hosted build failure.
- [x] 4.2 Rebuild/start the corrected image; rerun canonical/offline checks and document actual results.
