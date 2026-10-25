"""Asset evidence must follow the imported Agent rather than stale root copies."""

import json
import os
import subprocess
import sys

import pytest
from conftest import PROJECT_ROOT, QA_ROOT
from evaluate_agent import agent_assets
from qa_inputs import SOURCE_REPOS, InputError


def assets(root):
    prompts, mocks = root / "prompts", root / "mocks"
    prompts.mkdir(parents=True)
    mocks.mkdir(parents=True)
    for name in ("understand", "compose", "scene"):
        (prompts / f"{name}_v3.md").write_text(name)
    (mocks / "knowledge.json").write_text("{}")
    return prompts, mocks


@pytest.mark.parametrize("packaged", [False, True])
def test_actual_assets_are_recorded(tmp_path, packaged):
    root = tmp_path / "hangil_r2" if packaged else tmp_path
    prompts, mocks = assets(root)
    if packaged:
        assets(tmp_path)  # Obsolete copies must not enter the evidence.
    p, m = agent_assets(tmp_path, "v3", prompts, mocks)
    assert all(path.parent == prompts for path in p)
    assert m == [mocks / "knowledge.json"]


def test_missing_imported_assets_do_not_fall_back(tmp_path):
    assets(tmp_path)
    with pytest.raises(InputError, match="prompt version"):
        agent_assets(tmp_path, "v3", tmp_path / "hangil_r2/prompts", tmp_path / "mocks")


def test_assets_from_another_checkout_rejected(tmp_path):
    prompts, mocks = assets(tmp_path / "other")
    with pytest.raises(InputError, match="selected checkout"):
        agent_assets(tmp_path / "selected", "v3", prompts, mocks)


def test_verifier_asset_enters_evidence(tmp_path):
    prompts, mocks = assets(tmp_path)
    for name in ("understand", "compose", "scene", "verify"):
        (prompts / f"{name}_v4.md").write_text(name)
    recorded, _ = agent_assets(tmp_path, "v4", prompts, mocks, requires_verify=True)
    assert {path.name for path in recorded} == {
        f"{name}_v4.md" for name in ("understand", "compose", "scene", "verify")
    }


def test_required_verifier_cannot_be_omitted(tmp_path):
    prompts, mocks = assets(tmp_path)
    with pytest.raises(InputError, match="verify"):
        agent_assets(tmp_path, "v3", prompts, mocks, requires_verify=True)


def test_cli_writes_complete_evidence_for_symlinked_checkouts(tmp_path):
    project = tmp_path / "profile"
    project.mkdir()
    for name in SOURCE_REPOS:
        (project / name).symlink_to(
            (PROJECT_ROOT / name).resolve(), target_is_directory=True
        )
    output = tmp_path / "evidence"
    result = subprocess.run(
        [
            sys.executable,
            str(QA_ROOT / "scripts/evaluate_agent.py"),
            "--project-root",
            str(project),
            "--cases",
            str(QA_ROOT / "eval/component_cases.json"),
            "--output",
            str(output),
        ],
        env=dict(os.environ, OPENAI_API_KEY="", PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True,
        text=True,
        check=False,
    )
    # Product checks may fail; a valid run must still publish its complete metadata.
    assert (output / "metadata.json").is_file(), result.stderr
    metadata = json.loads((output / "metadata.json").read_text())
    assert metadata["turn_count"] == 21
    assert metadata["prompt_directory"] == "hangil_r2/prompts"
    assert metadata["fixture_directory"] == "hangil_r2/mocks"
