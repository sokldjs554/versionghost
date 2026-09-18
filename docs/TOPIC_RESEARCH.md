# Topic Research and Novelty Collision Audit

Date: 2026-09-18

## Why this research happened

The target role asks for developer-productivity AI services, full-stack applications that connect to LLM APIs and open-source models, and agentic/code-generation automation. Those requirements make a generic coding assistant an obvious portfolio idea — and therefore a poor differentiator.

Before implementation, public GitHub projects were sampled across these themes:

- terminal / repository coding agents
- issue-to-code agents
- specification-driven development
- multi-agent code review
- requirements-to-test generation
- code-change impact analysis
- proof/evidence gates for AI-authored changes
- API backward compatibility and historical-client replay

This is a collision audit, not an exhaustive literature review.

## Public patterns that were deliberately rejected

### Generic pair-programming / repository agent

Representative project: Aider — https://github.com/Aider-AI/aider

Observed pattern: repository mapping, model chat, edit/commit flow, lint/test loop. It is a strong general-purpose product, but recreating a smaller version would mainly demonstrate an already-established interaction pattern.

Decision: do not build "chat with repo → model edits files" as the project identity.

### Spec-first multi-agent planning

Representative project: Spec2Ship — https://github.com/spec2ship/spec2ship

Observed pattern: multiple agent roles debate requirements/architecture and emit structured planning artifacts.

Decision: VersionGhost may compile a change contract, but the differentiator cannot be multi-agent deliberation itself.

### AI code review dashboard

Representative project: Open Code Review — https://github.com/spencermarx/open-code-review

Observed pattern: multiple reviewers inspect code, discuss findings, and synthesize review output in a dashboard.

Decision: do not make review commentary or reviewer personas the center of the demo.

### Requirements → generated tests

Representative project: Test Case Generation Agent Advanced — https://github.com/codemaker2015/test-case-generation-agent-advanced

Observed pattern: upload requirements and generate test cases / reports.

Decision: VersionGhost uses fixed historical contracts plus deterministic probes as an independent verification surface. The model is not allowed to manufacture the evidence and then grade itself.

### Generic proof-carrying change / behavioral diff

Representative projects:

- proof-carrying-ops — https://github.com/aharwelik/proof-carrying-ops
- veridelta — https://github.com/it-all-playpark/veridelta
- Veris — https://github.com/vighriday/Veris

Observed patterns: receipts for change reach/rollback/verification, verification-surface deltas, and behavioral impact/coverage analysis.

Decision: these projects make a generic "AI change + proof packet" insufficiently novel on its own. VersionGhost therefore narrows the problem to **historical mobile-client compatibility during live-service API evolution** and makes client-version replay the first-class product object.

## Search gap that led to VersionGhost

GitHub searches on 2026-09-18 for combinations such as:

- `LLM API compatibility migration agent`
- `AI agent API backward compatibility`
- `mobile game liveops AI agent`
- `game backend API compatibility testing`
- `contract testing AI agent backward compatibility`

returned no obvious direct match in the sampled top results. That does not prove the idea is unique. It does show that this exact combination was materially less saturated than generic coding-agent, PR-review, spec-agent, and test-generation themes.

## Final project choice

**VersionGhost — an AI compatibility agent that changes a live-service API only after replaying synthetic historical mobile-client contracts.**

The project treats old deployed clients as "ghosts" that still exercise the backend after the current codebase has moved on.

Core differentiator:

`feature request → change contract → bounded code patch → historical client replay matrix → repair → evidence packet`

The important part is not that an LLM can write code. The important part is that a code-generation loop is forced to survive client versions it cannot edit.

## Why this is specifically useful for a mobile-game company

The target company publicly describes itself as a long-running online/mobile game developer serving multiple client platforms and countries. A mobile live service can have backend changes and app-store client versions moving on different timelines. VersionGhost uses that general product reality as the portfolio domain without claiming knowledge of the company's private architecture, deployment process, protocols, or incidents.
