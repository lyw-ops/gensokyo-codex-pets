# Roadmap

## Milestone 0 — repository and specification

Local scaffold and persistent GPT handoff complete. The baseline is synchronized with GitHub; visual-direction review remains pending.

- [x] Inspect the workspace, Git state, branch, remotes, and Git identity.
- [x] Configure the requested GitHub origin on `main`.
- [x] Verify connectivity and synchronize the remote.
- [x] Establish the repository structure and fan-work notice.
- [x] Document Reimu's discrete `0…5` task-to-food progression.
- [x] Review the maintainer-provided GPT visual prototypes and record their design implications without committing the source images.
- [x] Research the current public, bundled, and shipped-app pet contracts.
- [x] Record local v1/v2 dimensions, rows, metadata, installation, and state behavior.
- [x] Record that native custom task-count logic is not currently exposed.
- [ ] Maintainer review of the scaffold.
- [x] Add a canonical `HANDOFF.md` and cross-session update procedure.
- [x] Publish the initial commit and persistent GitHub handoff baseline.

## Milestone 1 — lock Reimu's visual system

- Audit and record approved official/officially licensed references.
- Choose the logical pixel grid and scaling method.
- Approve neutral front silhouette, proportions, and baseline.
- Approve the face grid and expression vocabulary.
- Approve a limited palette and shade hierarchy.
- Approve the low-table footprint, recurring anchors, exact dish vocabulary, expression progression, and all six meal-density compositions.
- Decide whether directional flight can preserve costume and prop handedness.

Output: a reviewed model sheet/specification, not a complete animation atlas.

## Milestone 2 — static Codex-compatible prototype

- Produce original source art for the nine standard state rows.
- Produce the 16 coherent look directions for local v2.
- Assemble and validate a 1536×2288 transparent atlas.
- Generate an installable `pet.json` with `spriteVersionNumber: 2`.
- Review reduced motion, actual-size readability, loop timing, and direction semantics.
- Select the honest static tier treatment for each standard row.
- Test local installation without claiming task-count-driven tier switching.

## Milestone 3 — workload interface proof

- Recheck official Codex APIs, hooks, and app behavior.
- Define a supported `WorkloadSnapshot` observer.
- Implement the centralized `ReimuFoodTier` clamp and transition policy with tests.
- Demonstrate exact `0`, `1`, `2`, `3`, `4`, and capped `5+` switching without scraping or inventing state.
- Document failure and unavailable-source behavior.

If no supported integration exists, keep workload variants as design assets and do not ship a brittle runtime workaround by default.

## Milestone 4 — polish and distribution review

- Complete motion and accessibility QA.
- Recheck the current Touhou fan-creator guidelines and Codex format.
- Select explicit licenses for original code/docs/art where appropriate.
- Write installation, update, removal, and attribution guidance.
- Decide supported desktop, web, and terminal targets separately.

## Later phases

Only after the Reimu pipeline is stable, define character-specific concepts for the remaining cast. Reuse engineering contracts, not Reimu's face, proportions, or food gimmick by default.
