# VersionGhost coding-agent rules

VersionGhost is a developer-productivity system that judges AI-authored code changes against a verification surface the model is not allowed to edit.

Before changing code:
1. Read `README.md`, `docs/ARCHITECTURE.md`, and `docs/BOUNDARIES.md`.
2. Preserve the historical client fixtures under `sample_app/liveops_service/client_contracts/`.
3. Preserve tests unless the human request explicitly changes the product contract; never weaken a test merely to make a patch pass.
4. Keep model-generated patches constrained to repository-local text replacement operations. Do not add arbitrary shell execution from model output.

Before declaring work complete:
1. Run `python -m pytest -q`.
2. Run `python -m versionghost.cli demo > /tmp/versionghost-packet.json`.
3. Verify the packet verdict is `ready_with_evidence`.
4. If a change alters the compatibility model, update `docs/EVALUATION.md` and regenerate measured artifacts with `python scripts/evaluate_demo.py`.

Do not claim a provider or deployment was used unless there is an actual run artifact or deployment URL proving it.
