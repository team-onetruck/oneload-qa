"""Exercise the real global Backend app; fake only its paid provider and external config."""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from production_wiring import fake_entrypoint
from qa_inputs import digest, load_live_map, source_commits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    url = urlparse(os.environ.get("DATABASE_URL", ""))
    if (url.hostname, url.path, url.username, os.environ.get("R6_DISPOSABLE_DB")) != (
        "127.0.0.1",
        "/hangil_r6_test",
        "hangil_r6",
        "1",
    ):
        ap.error("Use run_backend_tests.py; a disposable loopback DB is required")
    root = args.project_root.resolve()
    sys.path[:0] = [
        str(root / "oneload-backend"),
        str(root / "oneload_agent"),
        str(root / "oneload-rag/src"),
    ]
    import hangil_rag
    from fastapi.testclient import TestClient
    from hangil_r2 import FakeLLM
    from rag_inputs import load_rag

    _, rag = load_rag(root)
    _, map_info = load_live_map(root, Path(os.environ["MAP_DIR"]))
    commits = source_commits(root)
    checks = []

    def check(id_, expected, actual):
        checks.append(
            {
                "id": id_,
                "expected": expected,
                "actual": actual,
                "passed": expected == actual,
            }
        )

    def start(http):
        response = http.post(
            "/api/v1/sessions",
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json={
                "language": "ko",
                "map_id": "seoul-station",
                "client": {"platform": "web", "app_version": "r6-production-probe"},
            },
        )
        response.raise_for_status()
        body = response.json()
        return (
            "/api/v1/sessions/" + body["session_id"],
            body["session_token"],
            body["map_version"],
        )

    def say(http, session, message):
        base, token, _ = session
        response = http.post(
            base + "/messages",
            json={"message": message},
            headers={
                "Authorization": "Bearer " + token,
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )
        response.raise_for_status()
        return response.json()

    llm = FakeLLM(
        scene={
            "image_quality": "usable",
            "texts": [
                {"text": "공항철도", "kind": "line_name"},
                {"text": "4호선", "kind": "line_number"},
            ],
        }
    )
    entrypoint = root / "oneload-backend/app/main.py"
    with fake_entrypoint(entrypoint, llm) as app, TestClient(app) as http:
        agent, vision = app.state.agent, app.state.vision
        check(
            "PROD-01-default-assembly",
            [True, True, True],
            [
                agent.search_knowledge is hangil_rag.search_knowledge,
                agent.vision is vision,
                agent.llm is llm,
            ],
        )
        fare = say(http, start(http), "직통열차 요금 얼마야?")
        check(
            "PROD-02-official-fare",
            True,
            fare["status"] == "answered"
            and any(
                s["document_id"] == "doc-fare-arex-express"
                and s.get("source_url")
                and s.get("verified_at")
                for s in fare["sources"]
            ),
        )
        session = start(http)
        say(http, session, "일반열차")
        say(http, session, "없어요")
        base, token, version = session
        photo = http.post(
            base + "/localizations",
            data={"map_version": version},
            files={
                "image": (
                    "synthetic.jpg",
                    b"\xff\xd8\xff\xe0" + b"\x00" * 64,
                    "image/jpeg",
                )
            },
            headers={
                "Authorization": "Bearer " + token,
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )
        body = photo.json()
        check(
            "PROD-03-shared-vision",
            [200, "needs_confirmation", True],
            [photo.status_code, body.get("status"), bool(body.get("candidates"))],
        )
        with patch("hangil_rag._default", return_value=lambda *args: []):
            empty = say(http, start(http), "직통열차 요금 얼마야?")
        check(
            "PROD-04-empty-search-control",
            ["cannot_answer", []],
            [empty["status"], empty["sources"]],
        )
    with fake_entrypoint(entrypoint, key_present=False) as app, TestClient(app) as http:
        check(
            "PROD-05-no-key-fallback",
            ["RuleAgent", "NoVision"],
            [type(app.state.agent).__name__, type(app.state.vision).__name__],
        )
        fallback = say(http, start(http), "직통열차")
        check(
            "PROD-06-fallback-official-sources",
            True,
            bool(fallback["sources"])
            and all(
                s.get("source_url")
                and s.get("verified_at")
                and "demo" not in s["title"].lower()
                for s in fallback["sources"]
            ),
        )
        refused = say(http, start(http), "직통열차 요금 얼마야?")
        check(
            "PROD-07-fallback-refuses-unverified-fare",
            ["cannot_answer", []],
            [refused["status"], refused["sources"]],
        )
    _, final_rag = load_rag(root)
    if rag != final_rag or commits != source_commits(root):
        raise ValueError("Source input changed during production probe")
    report = {
        "probe_version": "r6-production-entrypoint-v1",
        "executed_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
        "commits": commits,
        "map": map_info,
        "rag": rag,
        "entrypoint_sha256": digest(entrypoint),
        "scope": "Actual global app; FakeLLM provider; forced local official MemorySearch; disposable DB. Not deployed runtime or AI quality.",
        "checks": checks,
        "passed": sum(c["passed"] for c in checks),
        "total": len(checks),
        "real_model_calls": 0,
        "real_embedding_calls": 0,
        "deployed_runtime_verified": False,
        "runner_sha256": digest(Path(__file__)),
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Production entrypoint API: {report['passed']}/{report['total']}")
    return int(report["passed"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
