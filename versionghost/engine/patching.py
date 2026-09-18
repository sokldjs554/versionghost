from __future__ import annotations

from pathlib import Path

from versionghost.models import PatchSet


class PatchApplicationError(RuntimeError):
    pass


PROTECTED_PARTS = {"client_contracts", "tests"}
ALLOWED_SUFFIXES = {".py", ".json", ".yaml", ".yml", ".ts", ".tsx"}


def apply_patch_set(repo_root: Path, patch: PatchSet) -> list[str]:
    changed: list[str] = []
    root = repo_root.resolve()
    for op in patch.operations:
        target = (repo_root / op.path).resolve()
        if root != target and root not in target.parents:
            raise PatchApplicationError(f"Path escapes workspace: {op.path}")
        rel_parts = set(target.relative_to(root).parts)
        if rel_parts & PROTECTED_PARTS:
            raise PatchApplicationError(f"Model patch may not edit tests/client contracts: {op.path}")
        if target.suffix not in ALLOWED_SUFFIXES:
            raise PatchApplicationError(f"File type is not patchable: {op.path}")
        if not target.exists():
            raise PatchApplicationError(f"Patch target does not exist: {op.path}")

        original = target.read_text(encoding="utf-8")
        count = original.count(op.find)
        if count != 1:
            raise PatchApplicationError(
                f"Expected exactly one match in {op.path}; found {count} for operation: {op.rationale}"
            )
        target.write_text(original.replace(op.find, op.replace, 1), encoding="utf-8")
        changed.append(op.path)
    return sorted(set(changed))
