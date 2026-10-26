"""Controlled FakeLLM output checks, independent of model factual accuracy."""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        ap.error("Use a new output path")
    root = args.project_root.resolve()
    sys.path[:0] = [
        str(root / "oneload-backend"),
        str(root / "oneload_agent"),
        str(root / "oneload-rag/src"),
    ]
    os.environ.update(
        OPENAI_API_KEY="",
        PROMPT_VERSION="v5",
        LANGSMITH_TRACING="false",
        LANGCHAIN_TRACING_V2="false",
        OTEL_SDK_DISABLED="true",
    )
    from app.ai.contracts import AgentContext, Slots
    from hangil_r2 import FakeLLM, LLMAgent
    from hangil_rag.loader import load_docs
    from hangil_rag.search_memory import to_hit
    from qa_inputs import load_live_map, source_commits

    docs = {
        d.doc_id: d
        for d in load_docs(root / "oneload-rag/knowledge", include_community=False)
    }
    ids = ["doc-allstop-ticket", "doc-arex-train-types"]
    hits = [to_hit(docs[x], "ko", docs[x].body("ko")) for x in ids]
    map_, metadata = load_live_map(root)
    rows = []

    class Controlled(FakeLLM):
        def __init__(self, text):
            super().__init__()
            self.text = text

        def compose(self, question, hits, language):
            return self.text

    for name, text, expected_status, expected_sources in [
        ("one-citation", "자료 안내입니다. [1]", "answered", ids[:1]),
        ("no-answer", "NO_ANSWER", "cannot_answer", []),
        ("invalid-citation", "자료 안내입니다. [99]", "cannot_answer", []),
        ("missing-citation", "자료에 답이 없습니다.", "cannot_answer", []),
        ("both-citations", "첫 안내입니다. [1] 두 번째입니다. [2]", "answered", ids),
        (
            "citation-after-truncation",
            "첫 안내입니다. [1] " + "안내" * 320 + " [2]",
            "answered",
            ids[:1],
        ),
    ]:
        ctx = AgentContext(
            language="ko",
            map=map_,
            state="idle",
            slots=Slots(),
            destination_poi_id=None,
            confirmed_node_id=None,
        )
        out = (
            LLMAgent(Controlled(text), search_knowledge=lambda *_: hits)
            .handle_message(ctx, "교통카드가 뭐야?", None, None)
            .response
        )
        actual = {"status": out.status, "sources": [s.document_id for s in out.sources]}
        expected = {"status": expected_status, "sources": expected_sources}
        rows.append(
            {
                "id": name,
                "passed": actual == expected,
                "expected": expected,
                "actual": actual,
            }
        )
    report = {
        "executed_at_utc": datetime.now(UTC).isoformat(),
        "commits": source_commits(root),
        "map": metadata,
        "checks": rows,
        "passed": sum(x["passed"] for x in rows),
        "total": len(rows),
        "live_model_calls": 0,
        "live_embedding_calls": 0,
        "scope": "Preselected two-document hits and controlled FakeLLM strings. Mechanical citation/refusal contract only; not factuality, real-model accuracy or retrieval quality.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Answer contract: {report['passed']}/{report['total']}")
    return int(report["passed"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
