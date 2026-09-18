# Limitations

- All client contracts, player identifiers, and live-ops data in the demo are synthetic.
- The project does not reproduce or infer GameSpring's private backend, client protocol, deployment pipeline, or incidents.
- The default provider is deterministic. It exists to make the agent loop reproducible without a paid service and must not be described as an LLM-quality result.
- The current impact analyzer supports Python ASTs and lexical ranking. It does not solve whole-program analysis, dynamic dispatch, reflection, native code, or cross-language resolution.
- The patch format is intentionally restrictive: existing-file exact text replacements only. This is safer for the demo but less flexible than a mature coding agent.
- SQLite is sufficient for the portfolio run store. A real multi-instance deployment would need an external shared store and queue.
- Browser polling is used instead of WebSocket/SSE streaming in v0.1.
- Public cloud deployment is not claimed until a deployment is actually created and smoke-tested.
- Claude Code/Cursor rule files are integration surfaces. Their existence does not prove that either external tool authored this repository.
