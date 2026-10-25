"""Inspect the actual Backend entrypoint with a fake model and local official RAG."""

import os
import runpy
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from qa_inputs import digest


@contextmanager
def fake_entrypoint(path: Path, llm=None, *, key_present=True):
    """Keep the real assembly; replace only the paid model provider and external config."""
    import hangil_rag
    from hangil_r2 import FakeLLM

    rag_repo = Path(hangil_rag.__file__).resolve().parents[2]
    env = {
        "OPENAI_API_KEY": "r6-fake-key" if key_present else "",
        "RAG_BACKEND": "memory",
        "RAG_KNOWLEDGE_DIR": str(rag_repo / "knowledge"),
        "RAG_INCLUDE_COMMUNITY": "0",
        "LANGSMITH_TRACING": "false",
        "LANGCHAIN_TRACING_V2": "false",
    }
    hangil_rag._default.cache_clear()
    try:
        with (
            patch.dict(os.environ, env),
            patch("hangil_r2.OpenAILLM", return_value=llm or FakeLLM()),
        ):
            yield runpy.run_path(str(path))["app"]
    finally:
        hangil_rag._default.cache_clear()


def probe_entrypoint(path: Path) -> dict:
    import hangil_rag
    from hangil_rag.search_memory import MemorySearch

    branches = {}
    expected_src = path.resolve().parents[2] / "oneload-rag/src"
    selected_rag = Path(hangil_rag.__file__).resolve().is_relative_to(expected_src)
    for label, present in (("missing_key", False), ("key_present", True)):
        with fake_entrypoint(path, key_present=present) as app:
            agent, vision = app.state.agent, app.state.vision
            search = getattr(agent, "search_knowledge", None)
            official = search is hangil_rag.search_knowledge and selected_rag
            hits = search("직통열차 요금 얼마야?", "ko", {}) if official else []
            backend = hangil_rag._default() if official else None
            branches[label] = {
                "agent": type(agent).__name__,
                "vision": type(vision).__name__,
                "same_vision": getattr(agent, "vision", None) is vision,
                "same_llm": getattr(agent, "llm", None) is not None
                and getattr(agent, "llm", None) is getattr(vision, "llm", None),
                "llm": type(getattr(agent, "llm", None)).__name__,
                "knowledge": type(search).__name__,
                "knowledge_module": getattr(search, "__module__", None),
                "uses_selected_rag_checkout": official,
                "search_backend": type(backend).__name__,
                "official_documents_only": isinstance(backend, MemorySearch)
                and bool(backend.docs)
                and all(d.source_kind == "official" for d in backend.docs),
                "returned_document_ids": [h.document_id for h in hits],
                "returned_sources_have_url_and_date": bool(hits)
                and all(h.source_url and h.verified_at for h in hits),
                "fallback": type(getattr(agent, "fallback", None)).__name__,
            }
    live = branches["key_present"]
    return {
        "method": "execute_actual_entrypoint_with_OpenAILLM_replaced_by_FakeLLM",
        "entrypoint_sha256": digest(path),
        "branches": branches,
        "agent_vision_conditionally_wired": live["agent"] == "LLMAgent"
        and live["vision"] == "LLMVision"
        and live["same_vision"]
        and live["same_llm"]
        and live["llm"] == "FakeLLM",
        "production_knowledge_is_demo": live["knowledge"] == "MockKnowledgeSearch",
        "official_memory_search_wired": live["uses_selected_rag_checkout"]
        and live["official_documents_only"]
        and live["returned_sources_have_url_and_date"],
        "configuration": "explicit local memory/official corpus; no production environment or DB",
        "real_model_calls": 0,
        "real_embedding_calls": 0,
        "deployed_runtime_verified": False,
    }
