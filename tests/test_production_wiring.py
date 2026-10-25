"""A factory definition alone must not pass entrypoint wiring or hide demo search."""

import os
from pathlib import Path

from production_wiring import probe_entrypoint


def test_current_entrypoint_selects_shared_fake_agent_and_official_search():
    root = Path(os.environ.get("QA_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
    result = probe_entrypoint(root / "oneload-backend/app/main.py")
    assert result["agent_vision_conditionally_wired"]
    assert not result["production_knowledge_is_demo"]
    assert result["official_memory_search_wired"]
    assert result["branches"]["missing_key"]["agent"] == "RuleAgent"
    assert result["branches"]["missing_key"]["vision"] == "NoVision"
    assert result["branches"]["key_present"]["llm"] == "FakeLLM"
    assert result["real_model_calls"] == 0


def test_unused_factory_does_not_approve_the_actual_entrypoint(tmp_path):
    path = tmp_path / "main.py"
    path.write_text("""
from types import SimpleNamespace
from hangil_r2 import LLMAgent, LLMVision, OpenAILLM, MockKnowledgeSearch
from app.ai.rule_agent import RuleAgent
from app.ai.vision import NoVision
def production_ai():
    llm = OpenAILLM()
    vision = LLMVision(llm)
    return LLMAgent(llm, search_knowledge=MockKnowledgeSearch(), vision=vision), vision
app = SimpleNamespace(state=SimpleNamespace(agent=RuleAgent(), vision=NoVision()))
""")
    result = probe_entrypoint(path)
    assert not result["agent_vision_conditionally_wired"]


def test_separate_vision_clients_do_not_pass_shared_wiring(tmp_path):
    path = tmp_path / "main.py"
    path.write_text("""
from types import SimpleNamespace
from hangil_r2 import LLMAgent, LLMVision, OpenAILLM, MockKnowledgeSearch
agent = LLMAgent(OpenAILLM(), search_knowledge=MockKnowledgeSearch(), vision=LLMVision(OpenAILLM()))
app = SimpleNamespace(state=SimpleNamespace(agent=agent, vision=LLMVision(OpenAILLM())))
""")
    result = probe_entrypoint(path)
    assert not result["agent_vision_conditionally_wired"]


def test_arbitrary_search_callable_is_not_official_provenance(tmp_path):
    path = tmp_path / "main.py"
    path.write_text("""
from types import SimpleNamespace
from hangil_r2 import LLMAgent, LLMVision, OpenAILLM
llm = OpenAILLM()
vision = LLMVision(llm)
agent = LLMAgent(llm, search_knowledge=lambda *args: [], vision=vision)
app = SimpleNamespace(state=SimpleNamespace(agent=agent, vision=vision))
""")
    result = probe_entrypoint(path)
    assert result["agent_vision_conditionally_wired"]
    assert not result["production_knowledge_is_demo"]
    assert not result["official_memory_search_wired"]


def test_inherited_rag_settings_are_isolated_and_restored(monkeypatch):
    root = Path(os.environ.get("QA_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
    monkeypatch.setenv("RAG_BACKEND", "pgvector")
    monkeypatch.setenv("RAG_KNOWLEDGE_DIR", "/nonexistent-r6-corpus")
    monkeypatch.setenv("RAG_INCLUDE_COMMUNITY", "1")
    result = probe_entrypoint(root / "oneload-backend/app/main.py")
    assert result["official_memory_search_wired"]
    assert os.environ["RAG_BACKEND"] == "pgvector"
    assert os.environ["RAG_KNOWLEDGE_DIR"] == "/nonexistent-r6-corpus"
    assert os.environ["RAG_INCLUDE_COMMUNITY"] == "1"


def test_production_api_refuses_caller_database_before_import(tmp_path):
    import subprocess
    import sys

    env = dict(
        os.environ,
        DATABASE_URL="postgresql://x:x@127.0.0.1/existing",
        R6_DISPOSABLE_DB="1",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(
                Path(__file__).resolve().parents[1] / "scripts/probe_production_api.py"
            ),
            "--project-root",
            str(tmp_path),
            "--output",
            str(tmp_path / "not-created.json"),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "disposable loopback DB is required" in result.stderr
    assert not (tmp_path / "not-created.json").exists()
