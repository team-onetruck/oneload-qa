"""A fresh passing holdout cannot hide a known positive-query regression."""

import json
import sys
from pathlib import Path

import pytest
import recheck_rag_issue3 as review


@pytest.mark.parametrize("regressed", [False, True])
def test_fresh_gate_and_exposed_positive_guard_are_separate(
    tmp_path, monkeypatch, regressed
):
    qa = Path(review.__file__).resolve().parents[1]
    output = tmp_path / "result.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "recheck",
            "--before-root",
            str(tmp_path / "before"),
            "--after-root",
            str(tmp_path / "after"),
            "--freeze-repo",
            str(tmp_path),
            "--freeze-commit",
            "precommitted",
            "--dataset",
            str(qa / "eval/retrieval_holdout_v3.json"),
            "--metadata",
            str(qa / "eval/retrieval_holdout_v3.meta.json"),
            "--output",
            str(output),
        ],
    )

    def frozen_bytes(command, **_):
        relative = command[-1].split(":", 1)[1]
        return (qa / relative).read_bytes()

    def worker(command, **_):
        after = Path(command[command.index("--worker-root") + 1]).name == "after"
        old_positive_ok = not (after and regressed)
        result = {
            "fresh_holdout": {
                "top3": 24,
                "positive_total": 24,
                "false_positives": 0,
                "out_of_scope_empty": 24,
                "out_of_scope_total": 24,
            },
            "r6_exposed_v2": {
                "rows": [
                    {
                        "id": "positive",
                        "question": "known question",
                        "gold": ["doc-a"],
                        "passed": old_positive_ok,
                        "retrieved": ["doc-a"] if old_positive_ok else [],
                    },
                    # A changed negative query is diagnostic, not a positive-query regression.
                    {
                        "id": "negative",
                        "question": "outside",
                        "gold": [],
                        "passed": not after,
                        "retrieved": ["doc-a"] if after else [],
                    },
                ]
            },
        }
        Path(command[command.index("--output") + 1]).write_text(json.dumps(result))

    monkeypatch.setattr(review.subprocess, "check_output", frozen_bytes)
    monkeypatch.setattr(review.subprocess, "run", worker)
    assert review.main() == (1 if regressed else 0)
    result = json.loads(output.read_text())
    assert result["fresh_holdout_gate_met"] is True
    assert [r["id"] for r in result["positive_regressions"]] == (
        ["positive"] if regressed else []
    )
