# AI Coding Workflow

The target role explicitly values modern AI coding tools. This repository therefore defines a tool-neutral workflow that can be consumed by Claude Code, Cursor, or another repository agent without letting the agent become its own judge.

## Shared operating loop

1. Read repository rules (`CLAUDE.md`, `AGENTS.md`, Cursor rule).
2. Understand the requested change and affected contract.
3. Make a small edit.
4. Run repository tests.
5. Run the VersionGhost compatibility demo/gate.
6. Inspect the evidence packet instead of relying on the model's narrative confidence.
7. Record limitations if an external service/model was unavailable.

## Why repository rules are included

Vibe coding is useful when the model can move quickly, but speed makes forgotten constraints more expensive. The rule files give coding agents persistent, reviewable instructions:

- what they may not edit
- what command proves completion
- which claims require actual evidence
- how to avoid weakening tests to satisfy themselves

## Claim discipline

A portfolio reviewer should be able to distinguish:

- implemented code
- executed measurements
- optional integrations
- planned extensions

That distinction is deliberately preserved in README, evaluation artifacts, and deployment notes.
