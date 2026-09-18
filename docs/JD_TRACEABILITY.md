# Target-role Traceability

Target: GameSpring — AI Programmer (AI system design & development), reviewed 2026-09-18.

Public job source: https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=54469685

This document maps public job requirements to repository evidence. It does not claim access to GameSpring's private systems or codebase.

| Public requirement | VersionGhost evidence |
|---|---|
| LLM-based services that improve development/work productivity | A change request is compiled into a contract, patched, verified, repaired, and returned as an evidence packet rather than handled manually. |
| Full-stack web service integrating LLM APIs and open-source models | FastAPI API + browser product UI; optional hosted Messages API adapter; OpenAI-compatible adapter for Ollama/local coder models. |
| AI agents / automation / code generation pipeline | `VersionGhostPipeline` orchestrates impact → contract → patch → verify → repair → packet. Model output is constrained by the patch applicator. |
| Frontend and backend breadth | Browser dashboard, REST endpoints, background execution, persisted run/events, provider adapters, AST analysis, subprocess verification. |
| Rapid prototyping with AI coding tools | `CLAUDE.md`, `AGENTS.md`, and `.cursor/rules/versionghost.mdc` define repeatable AI-assisted development gates. These files are integration rules; they are not evidence that a specific external tool authored a commit. |
| End-to-end AI full-stack project | Product concept, code, tests, local demo, CI definition, container build, deployment manifest, evaluation script, operations/limitations docs are in one new repository. Public deployment must be added only after actually executed. |
| Ability to learn current AI trends / English technical material | Architecture/research docs are written in English and the project uses provider-neutral model routing plus current agent-tool conventions. |

## Why existing portfolio projects were not simply reused

Existing work already demonstrates full-stack delivery, tool-calling agents, internal workflow automation, retrieval/evidence systems, and robust backend design. Those are useful foundations, but none makes **developer code-generation productivity + old mobile-client compatibility** the central problem. A new repository makes the target role legible immediately and avoids presenting an older project as if it were built for this role.
