from __future__ import annotations

from versionghost.models import AttemptResult, ChangeContract, RequirementEvidence

REQUIREMENT_TO_CASE_SNIPPET = {
    "REQ-1": ["New client expects"],
    "REQ-2": ["Legacy mobile client", "Current v1 client"],
    "REQ-3": ["retried claim"],
    "REQ-4": ["fourth unique daily claim"],
    "REQ-5": ["client upgrade"],
}


def build_requirement_evidence(
    contract: ChangeContract, attempts: list[AttemptResult]
) -> list[RequirementEvidence]:
    final = attempts[-1] if attempts else None
    evidence_rows: list[RequirementEvidence] = []
    for requirement in contract.requirements:
        evidence: list[str] = []
        proven = False
        snippets = REQUIREMENT_TO_CASE_SNIPPET.get(requirement.id, [])
        if final is not None:
            matched = [
                cell
                for cell in final.replay
                if any(snippet.lower() in cell.case_id.lower() for snippet in snippets)
            ]
            if matched and all(cell.status == "pass" for cell in matched):
                proven = True
                evidence.extend(
                    [f"client {cell.client_version}: {cell.case_id} -> pass" for cell in matched]
                )
            if requirement.id in {"REQ-3", "REQ-4"}:
                tests = [check for check in final.checks if check.name == "target-unit-tests"]
                if tests and tests[0].status == "pass":
                    evidence.append("target-unit-tests -> pass")
        if not evidence:
            evidence.append("No mapped passing probe in the final attempt.")
        evidence_rows.append(
            RequirementEvidence(
                requirement_id=requirement.id,
                status="proven" if proven else "unproven",
                evidence=evidence,
            )
        )
    return evidence_rows
