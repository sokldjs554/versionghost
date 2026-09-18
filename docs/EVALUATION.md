# Evaluation

VersionGhost separates two questions:

1. Does the **orchestration and verification design** deterministically reject an incompatible patch and accept the repaired one?
2. How good is a particular **LLM provider** at producing the first or repaired patch?

The committed offline evaluation answers only the first question. Model-quality evaluation requires an actually configured model and a separately recorded run.

## Offline acceptance checks

`python scripts/evaluate_demo.py` repeats the built-in scenario and records:

- whether the final verdict is `ready_with_evidence`
- first-attempt replay pass count
- final replay pass count
- number of attempts
- requirement evidence status
- measured local pipeline time

The latency is only a local execution measurement from the evaluation environment; it is not a production performance claim.

## Unit/integration suite

`python -m pytest -q`

The suite covers:

- impact map discovering the reward service
- patch engine refusing edits to protected client contracts
- full pipeline rejecting attempt 1 and accepting repair attempt 2
- REST health endpoint
- OpenAI-compatible and hosted Messages API adapter protocol contracts (mock transport; not model quality)
- repository legal/demo guard: README forbidden-token check, no license file, six fixed historical contract fixtures
- synthetic target service idempotency and daily-limit invariants

## What is not yet a measured claim

- real GameSpring code or traffic
- production client-version distributions
- model accuracy on arbitrary repositories
- hosted-model success rate
- local open-source model success rate
- cloud throughput / concurrency / cost
