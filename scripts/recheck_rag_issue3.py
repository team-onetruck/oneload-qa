"""Compare two pinned MemorySearch revisions on a precommitted R6 holdout.

No parameter sweep, live model, embedding or DB. Each revision runs in a fresh
process so Python package caches cannot mix the before/after implementations.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml
from evaluate_retrieval import score
from qa_inputs import InputError, digest
from rag_inputs import load_rag


def validate_holdout(data, meta, known_ids, exposed_queries):
    cases = data["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Holdout cases must be nonempty with unique ids")
    if len({c["q"].strip().casefold() for c in cases}) != len(cases):
        raise ValueError("Holdout has duplicate questions")
    if not any(c["gold"] for c in cases) or not any(not c["gold"] for c in cases):
        raise ValueError("Holdout must include positive and out-of-scope questions")
    for c in cases:
        if c["lang"] not in {"ko", "en"} or not c["q"].strip() or not c["family"]:
            raise ValueError("Invalid language, question or family")
        if not set(c["gold"]) <= known_ids:
            raise ValueError("Unknown gold document")
        if c["q"].strip().casefold() in exposed_queries:
            raise ValueError("Holdout exact question was already exposed")
    protocol = data["protocol"]
    if (protocol["primary_min_score"], protocol["k"], protocol["relative_cutoff"]) != (
        0.25,
        3,
        0.5,
    ):
        raise ValueError("This frozen protocol requires min_score0.25/k3/relative0.5")
    if meta["search_outputs_seen_at_freeze"] is not False:
        raise ValueError("Holdout was not frozen before observing search results")


def worker(root, qa, diagnostic_repo, holdout_path=None, meta_path=None):
    holdout_path = holdout_path or qa / "eval/retrieval_holdout_v2.json"
    meta_path = meta_path or qa / "eval/retrieval_holdout_v2.meta.json"
    data, meta = json.loads(holdout_path.read_text()), json.loads(meta_path.read_text())
    if digest(holdout_path) != meta["sha256"]:
        raise ValueError("Frozen dataset hash mismatch")
    search, inputs = load_rag(root, data["protocol"]["primary_min_score"])
    if (
        inputs["relative_cutoff"] != data["protocol"]["relative_cutoff"]
        or not inputs["working_tree_clean"]
    ):
        raise ValueError("Search policy changed or checkout is dirty")
    r6_path, r3_path, r3_hold_path = (
        qa / "eval/retrieval_cases.json",
        diagnostic_repo / "eval/retrieval.yaml",
        diagnostic_repo / "eval/retrieval_holdout.yaml",
    )
    r6 = json.loads(r6_path.read_text())["cases"]
    r3, r3_hold = (
        yaml.safe_load(r3_path.read_text())["cases"],
        yaml.safe_load(r3_hold_path.read_text())["cases"],
    )
    v2_path = qa / "eval/retrieval_holdout_v2.json"
    exposed_v2 = (
        json.loads(v2_path.read_text())["cases"]
        if holdout_path.resolve() != v2_path.resolve()
        else []
    )
    exposed = {c["q"].strip().casefold() for c in [*r6, *r3, *r3_hold, *exposed_v2]}
    validate_holdout(data, meta, set(inputs["document_ids"]), exposed)
    # Fixed protocol. All questions/gold and the gate were committed before this line.
    fresh = score(data["cases"], search)
    diagnostic = [
        {
            "id": "D-original-hotel",
            "q": "서울역 근처 호텔 객실 가격 알려줘",
            "lang": "ko",
            "gold": [],
        },
        {
            "id": "D-original-seats",
            "q": "지금 서울역 직통열차 빈 좌석이 몇 개 남았나요?",
            "lang": "ko",
            "gold": [],
        },
        {
            "id": "D-exposed-taxi",
            "q": "택시 기본요금이 얼마예요?",
            "lang": "ko",
            "gold": [],
        },
    ]
    result = {
        "rag": inputs,
        "fresh_holdout": fresh,
        "r6_development": score([c for c in r6 if c["split"] == "dev"], search),
        "r6_exposed_holdout": score([c for c in r6 if c["split"] == "holdout"], search),
        "r3_legacy": score(r3, search),
        "r3_exposed_holdout": score(r3_hold, search),
        "known_diagnostics": score(diagnostic, search),
        "dataset_hashes": {
            "fresh": digest(holdout_path),
            "meta": digest(meta_path),
            "r6_exposed": digest(r6_path),
            "r3_legacy": digest(r3_path),
            "r3_exposed": digest(r3_hold_path),
        },
    }
    if exposed_v2:
        result["r6_exposed_v2"] = score(exposed_v2, search)
        result["dataset_hashes"]["r6_exposed_v2"] = digest(v2_path)
    _, final = load_rag(root, data["protocol"]["primary_min_score"])
    if final != inputs or digest(holdout_path) != meta["sha256"]:
        raise ValueError("Inputs changed during evaluation")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--before-root", type=Path)
    ap.add_argument("--after-root", type=Path)
    ap.add_argument("--freeze-repo", type=Path)
    ap.add_argument("--freeze-commit")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dataset", type=Path, help="Precommitted dataset; default: v2")
    ap.add_argument("--metadata", type=Path, help="Matching precommitted metadata")
    ap.add_argument("--worker-root", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--diagnostic-repo", type=Path, help=argparse.SUPPRESS)
    args = ap.parse_args()
    qa = Path(__file__).resolve().parents[1]
    holdout_path = (args.dataset or qa / "eval/retrieval_holdout_v2.json").resolve()
    meta_path = (args.metadata or qa / "eval/retrieval_holdout_v2.meta.json").resolve()
    if args.output.exists():
        ap.error("Use a new report path")
    if args.worker_root:
        result = worker(
            args.worker_root.resolve(),
            qa,
            args.diagnostic_repo.resolve(),
            holdout_path,
            meta_path,
        )
    else:
        if not all(
            (args.before_root, args.after_root, args.freeze_repo, args.freeze_commit)
        ):
            ap.error(
                "before-root, after-root, freeze-repo and freeze-commit are required"
            )
        for path in (holdout_path, meta_path):
            relative = path.relative_to(qa).as_posix()
            committed = subprocess.check_output(
                ["git", "show", f"{args.freeze_commit}:{relative}"],
                cwd=args.freeze_repo,
            )
            if committed != path.read_bytes():
                ap.error("Holdout differs from the pre-evaluation Git commit")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        measurements = {}
        for label, root in (("before", args.before_root), ("after", args.after_root)):
            child = args.output.with_name(args.output.stem + "-" + label + ".json")
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker-root",
                    str(root.resolve()),
                    "--diagnostic-repo",
                    str(args.after_root.resolve() / "oneload-rag"),
                    "--dataset",
                    str(holdout_path),
                    "--metadata",
                    str(meta_path),
                    "--output",
                    str(child),
                ],
                check=True,
            )
            measurements[label] = json.loads(child.read_text())
        data = json.loads(holdout_path.read_text())
        held = measurements["after"]["fresh_holdout"]
        gate = data["protocol"]["proposed_qa_gate"]
        acceptable = (
            held["top3"] / held["positive_total"] >= gate["positive_top3_recall_min"]
            and held["false_positives"] <= gate["out_of_scope_false_positives_max"]
        )
        regressions = []
        for group, previous in measurements["before"].items():
            if (
                group == "fresh_holdout"
                or not isinstance(previous, dict)
                or "rows" not in previous
            ):
                continue
            current = {r["id"]: r for r in measurements["after"][group]["rows"]}
            for row in previous["rows"]:
                if row["gold"] and row["passed"] and not current[row["id"]]["passed"]:
                    regressions.append(
                        {
                            "group": group,
                            "id": row["id"],
                            "question": row["question"],
                            "gold": row["gold"],
                            "before": row["retrieved"],
                            "after": current[row["id"]]["retrieved"],
                        }
                    )
        fresh_met = acceptable
        if data["protocol"].get("positive_regression_guard"):
            acceptable = acceptable and not regressions
        result = {
            "executed_at_utc": datetime.now(UTC).isoformat(),
            "dataset_version": data["dataset_version"],
            "freeze_commit": args.freeze_commit,
            "protocol": data["protocol"],
            "measurements": measurements,
            "fresh_holdout_gate_met": fresh_met,
            "positive_regressions": regressions,
            "decision": "fresh_holdout_gate_met"
            if acceptable
            else "fresh_holdout_gate_not_met",
            "evaluation_repetitions_per_revision": 1,
            "runner_sha256": digest(Path(__file__)),
            "score_runner_sha256": digest(
                Path(__file__).with_name("evaluate_retrieval.py")
            ),
            "rag_inputs_sha256": digest(Path(__file__).with_name("rag_inputs.py")),
            "limitations": [
                "R6 synthetic questions; paired translations are correlated; same knowledge corpus",
                "Gold documents not human-certified service answers",
                "Known/taxi and earlier datasets are exposed diagnostics, not fresh holdout",
                "MemorySearch only; no live LLM, embeddings, pgvector quality or production wiring measured",
                "Do not tune or relabel on these outputs; a later fix needs another fresh holdout",
            ],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if not args.worker_root:
        print(result["decision"])
        for label, entry in result["measurements"].items():
            s = entry["fresh_holdout"]
            print(
                f"{label}: top3={s['top3']}/{s['positive_total']}, OOS empty={s['out_of_scope_empty']}/{s['out_of_scope_total']}"
            )
        return 0 if acceptable else 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InputError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
