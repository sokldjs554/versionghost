from pathlib import Path

import pytest

from versionghost.engine.patching import PatchApplicationError, apply_patch_set
from versionghost.models import PatchOperation, PatchSet


def test_patch_cannot_modify_contract_fixture(tmp_path: Path) -> None:
    target = tmp_path / "client_contracts" / "x.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"a": 1}', encoding="utf-8")
    patch = PatchSet(
        summary="cheat",
        operations=[PatchOperation(path="client_contracts/x.json", find="1", replace="2", rationale="no")],
    )
    with pytest.raises(PatchApplicationError):
        apply_patch_set(tmp_path, patch)
