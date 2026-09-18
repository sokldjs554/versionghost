# VersionGhost Architecture

## Product boundary

VersionGhost is a developer-productivity service for live-service API evolution. It accepts a change request and a repository snapshot, lets a model propose bounded text replacements, then independently verifies the candidate against unit checks and historical client contracts.

```text
feature request
     |
     v
[impact analyzer] ----> AST nodes / resolved edges / uncertainty
     |
     v
[change-contract compiler]
     |
     v
[LLM provider]
 deterministic | Ollama/OpenAI-compatible | hosted API
     |
     v
[safe patch applicator]
 exact find/replace, repo-local paths only
     |
     v
+---------------- verification authority ----------------+
| compile check                                             |
| existing unit tests                                       |
| historical client replay matrix                           |
| idempotency / limit / cross-version probes                |
+-----------------------------------------------------------+
     | fail
     v
[bounded repair request] -> same verification surface
     |
     v
[merge packet]
 requirement -> evidence, attempts, changed files, limits
```

## Trust separation

The model is allowed to propose code changes. It is not allowed to:

- edit `client_contracts/`
- edit tests through the patch engine
- run arbitrary shell commands
- choose which verification checks run
- reinterpret a failed probe as a pass

This is the central design choice. Code generation and change acceptance are separate authorities.

## Historical-client replay

The built-in synthetic target contains three client generations and additional behavioral probes:

- v1.4 legacy response contract
- v1.9 current v1 response contract
- v2.0 new response contract
- duplicate-idempotency probe
- daily-limit boundary probe
- cross-version retry probe

The first generated patch intentionally implements the new v2 payload globally. v2 succeeds, but the v1 clients and cross-version retry fail. The repair stores a canonical reward record and renders it at the version boundary, after which the same replay surface is run again.

## Static impact analysis

`versionghost/engine/impact.py` parses Python ASTs and emits:

- file/symbol nodes
- containment edges
- call edges only when a symbol target is unique
- an uncertainty entry instead of a guessed edge when a call target is ambiguous

The implementation is deliberately modest and honest: it is not a whole-program analyzer and does not claim to resolve dynamic dispatch/reflection.

## Providers

### Deterministic demo

Used by default so the complete agent loop is reproducible without credentials. It intentionally contains a realistic first-attempt compatibility mistake. This route validates orchestration and gates; it is not a benchmark of model intelligence.

### OpenAI-compatible route

`versionghost/agent/openai_compat.py` supports an OpenAI-compatible chat endpoint. The default configuration targets a local Ollama endpoint and a Qwen coder model name, but any compatible server can be configured through environment variables.

### Hosted API route

`versionghost/agent/anthropic.py` provides an optional direct Messages API adapter. Credentials are environment-only and the route is disabled unless configured.

## Persistence

Run state, trace events, and final packets are persisted in SQLite with WAL enabled for the portfolio demo. The service does not claim this as the only production storage choice.

## Frontend

The browser UI is served by the same FastAPI service and polls run state. It is a real API-backed product screen rather than a static portfolio page: every matrix row, attempt, requirement result, metric, and trace event comes from a persisted run.
