from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

from versionghost.models import ImpactEdge, ImpactNode, ImpactReport


INTEREST_TERMS = {
    "reward",
    "claim",
    "client",
    "version",
    "idempotency",
    "streak",
    "coins",
    "limit",
}


def analyze_repo(repo_root: Path, request_text: str) -> ImpactReport:
    nodes: list[ImpactNode] = []
    edges: list[ImpactEdge] = []
    symbol_locations: dict[str, list[str]] = defaultdict(list)
    calls: list[tuple[str, str]] = []
    uncertainty: list[str] = []

    py_files = sorted(repo_root.rglob("*.py"))
    for path in py_files:
        rel_path = path.relative_to(repo_root)
        if any(part in {".git", ".versionghost", ".venv"} for part in rel_path.parts):
            continue
        rel = rel_path.as_posix()
        file_id = f"file:{rel}"
        nodes.append(ImpactNode(id=file_id, kind="file", path=rel))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            uncertainty.append(f"Could not parse {rel}: {exc.msg}")
            continue

        for item in ast.walk(tree):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(item, ast.ClassDef) else "function"
                node_id = f"symbol:{rel}:{item.name}"
                nodes.append(ImpactNode(id=node_id, kind=kind, path=rel, symbol=item.name))
                edges.append(ImpactEdge(source=file_id, target=node_id, relation="contains"))
                symbol_locations[item.name].append(node_id)
            if isinstance(item, ast.Call):
                called = _call_name(item.func)
                if called:
                    calls.append((file_id, called))

    for source, called in calls:
        targets = symbol_locations.get(called, [])
        if len(targets) == 1:
            edges.append(ImpactEdge(source=source, target=targets[0], relation="calls"))
        elif len(targets) > 1:
            uncertainty.append(f"Ambiguous call target '{called}' from {source}; no guessed edge emitted.")

    query_terms = {term.lower() for term in request_text.replace("-", " ").split() if len(term) > 2}
    query_terms |= INTEREST_TERMS
    scored: list[tuple[int, str]] = []
    for path in py_files:
        rel = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        score = sum(1 for term in query_terms if term in text or term in rel.lower())
        if score:
            scored.append((score, rel))

    touched = [rel for _, rel in sorted(scored, key=lambda item: (-item[0], item[1]))[:10]]
    if not touched:
        uncertainty.append("No high-confidence candidate files from lexical/AST analysis.")

    return ImpactReport(
        nodes=nodes,
        edges=edges,
        touched_candidates=touched,
        uncertainty=sorted(set(uncertainty)),
    )


def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
