"""Separate frozen retrieval evaluation from bounded live Agent answer evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path


class EvaluationStop(BaseException):
    """Do not let the product's LLM fallback hide an evaluation/budget failure."""


class BudgetLedger:
    def __init__(self, policy, path=None):
        self.policy, self.path = policy, path
        self.charged = Decimal(0)
        self.attempts = []
        self.total_input = self.total_output = 0

    def save(self):
        if self.path:
            self.path.write_text(json.dumps(self.report(), indent=2) + "\n")

    def report(self):
        return {
            "charged_upper_estimate_usd": str(self.charged),
            "budget_usd": self.policy["max_usd"],
            "input_tokens": self.total_input,
            "output_tokens": self.total_output,
            "attempt_count": len(self.attempts),
            "attempts": self.attempts,
            "cached_discount_applied": False,
        }

    def reserve(self, content):
        if not isinstance(content, str):
            raise EvaluationStop("Text-only evaluation: nontext input rejected")
        size = len(content.encode("utf-8"))
        if size > self.policy["max_prompt_utf8_bytes"]:
            raise EvaluationStop("Prompt exceeds precommitted byte cap")
        if len(self.attempts) >= self.policy["max_api_attempts"]:
            raise EvaluationStop("API attempt cap reached")
        inp = size + self.policy["input_token_safety_overhead"]
        reserve = (
            Decimal(inp) * Decimal(str(self.policy["rate_input_usd_per_million"]))
            + Decimal(self.policy["max_output_tokens"])
            * Decimal(str(self.policy["rate_output_usd_per_million"]))
        ) / Decimal(1_000_000)
        if self.charged + reserve > Decimal(str(self.policy["max_usd"])):
            raise EvaluationStop("Budget cap reached before API call")
        self.charged += reserve
        row = {
            "prompt_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "input_token_upper_bound": inp,
            "reserved_usd": str(reserve),
            "state": "reserved",
        }
        self.attempts.append(row)
        self.save()  # A crash/unknown response retains the full reservation.
        return len(self.attempts) - 1

    def settle(self, index, prompt_tokens, completion_tokens, model):
        row = self.attempts[index]
        if row["state"] != "reserved":
            raise EvaluationStop("Attempt already settled")
        if (
            prompt_tokens > row["input_token_upper_bound"]
            or completion_tokens > self.policy["max_output_tokens"]
            or min(prompt_tokens, completion_tokens) < 0
        ):
            raise EvaluationStop("Reported usage exceeds reserved bounds")
        actual = (
            Decimal(prompt_tokens)
            * Decimal(str(self.policy["rate_input_usd_per_million"]))
            + Decimal(completion_tokens)
            * Decimal(str(self.policy["rate_output_usd_per_million"]))
        ) / Decimal(1_000_000)
        self.charged += actual - Decimal(row["reserved_usd"])
        self.total_input += prompt_tokens
        self.total_output += completion_tokens
        row.update(
            state="settled",
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            model=model,
            estimated_usd=str(actual),
        )
        self.save()


def restore_auth_attempt(previous, ledger, freeze, dataset_sha, commits):
    """Carry the unknown-cost failed request; never replay completed answers."""
    if (
        previous.get("completion") != "stopped"
        or previous.get("stop_reason") != "Provider failure: AuthenticationError"
        or previous.get("rows") != []
        or previous.get("freeze_commit") != freeze
        or previous.get("dataset_sha256") != dataset_sha
        or previous.get("commits") != commits
        or previous.get("protocol", {}).get("budget") != ledger.policy
    ):
        raise ValueError(
            "Only an identical, zero-answer authentication failure can resume"
        )
    prior = previous["budget"]
    attempts = prior["attempts"]
    if any(a.get("state") != "usage_unknown" for a in attempts):
        raise ValueError("Prior authentication attempts must retain unknown usage")
    charge = sum((Decimal(a["reserved_usd"]) for a in attempts), Decimal(0))
    if (
        charge != Decimal(prior["charged_upper_estimate_usd"])
        or not Decimal(0) <= charge <= Decimal(str(ledger.policy["max_usd"]))
        or len(attempts) != prior["attempt_count"]
    ):
        raise ValueError("Invalid prior budget accounting")
    ledger.charged, ledger.attempts = charge, list(attempts)
    ledger.save()


def citation_diagnostic(response, compose_ids):
    numbers = [int(x) for x in re.findall(r"\[(\d+)\]", response["assistant_message"])]
    source_ids = [s["document_id"] for s in response.get("sources", [])]
    valid = all(1 <= x <= len(compose_ids) for x in numbers)
    visible_ids = sorted({compose_ids[x - 1] for x in numbers}) if valid else []
    return {
        "visible_numbers": numbers,
        "returned_sources": source_ids,
        "visible_source_ids": visible_ids,
        "number_range_valid": valid,
        "visible_citations_match_sources": valid
        and set(visible_ids) == set(source_ids),
        "answered_has_source": response["status"] != "answered" or bool(source_ids),
    }


def validate_frozen(qa, freeze_repo, freeze_commit):
    data_path, meta_path = (
        qa / "eval/split_holdout_v4.json",
        qa / "eval/split_holdout_v4.meta.json",
    )
    for path in (data_path, meta_path):
        original = subprocess.check_output(
            ["git", "show", f"{freeze_commit}:{path.relative_to(qa)}"],
            cwd=freeze_repo,
        )
        if original != path.read_bytes():
            raise ValueError("Frozen evaluation input changed")
    data, meta = json.loads(data_path.read_text()), json.loads(meta_path.read_text())
    if hashlib.sha256(data_path.read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError("Dataset hash mismatch")
    return data, meta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project-root", type=Path, required=True)
    ap.add_argument("--freeze-repo", type=Path, required=True)
    ap.add_argument("--freeze-commit", required=True)
    ap.add_argument("--mode", choices=("retrieval", "live"), required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument(
        "--api-key-env-file", type=Path, help="Read only OPENAI_API_KEY; never print it"
    )
    ap.add_argument(
        "--previous-failed-run",
        type=Path,
        help="Carry a zero-answer auth failure's budget",
    )
    args = ap.parse_args()
    qa, root = Path(__file__).resolve().parents[1], args.project_root.resolve()
    if args.output.exists() or args.output.with_suffix(".ledger.json").exists():
        ap.error("Use a new report path; primary evaluation is not overwritten")
    data, meta = validate_frozen(qa, args.freeze_repo, args.freeze_commit)
    sys.path[:0] = [
        str(root / "oneload-backend"),
        str(root / "oneload_agent"),
        str(root / "oneload-rag/src"),
    ]
    os.environ.update(
        PROMPT_VERSION="v5",
        LANGSMITH_TRACING="false",
        LANGCHAIN_TRACING_V2="false",
        OTEL_SDK_DISABLED="true",
        RAG_BACKEND="memory",
        RAG_INCLUDE_COMMUNITY="0",
    )
    from qa_inputs import load_live_map, source_commits
    from rag_inputs import load_rag

    search, inputs = load_rag(root, 0.25)
    commits = source_commits(root)
    if not inputs["working_tree_clean"]:
        ap.error("RAG source checkout must be clean")
    expected = (
        {meta["before_rag"], meta["candidate_rag"]}
        if args.mode == "retrieval"
        else {meta["candidate_rag"]}
    )
    if inputs["commit"] not in expected:
        ap.error("RAG is not the precommitted revision")
    if (
        commits["oneload_agent"] != meta["agent"]
        or commits["oneload-backend"] != meta["backend"]
    ):
        ap.error("Agent/Backend is not the precommitted revision")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "executed_at_utc": datetime.now(UTC).isoformat(),
        "mode": args.mode,
        "freeze_commit": args.freeze_commit,
        "dataset_sha256": meta["sha256"],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "commits": commits,
        "rag": inputs,
        "protocol": data["protocol"],
    }
    if args.mode == "retrieval":
        from evaluate_retrieval import score

        result["retrieval"] = score(data["cases"], search)
        metric = result["retrieval"]
        result["new_retrieval_gate_met"] = (
            metric["top3"] / metric["positive_total"] >= 0.9
        )
        result["out_of_scope_empty_is_diagnostic"] = True
        result["live_model_calls"] = 0
    else:
        key = os.environ.get("OPENAI_API_KEY")
        if args.api_key_env_file:
            from dotenv import dotenv_values

            key = dotenv_values(args.api_key_env_file).get("OPENAI_API_KEY")
        if not key:
            ap.error("OPENAI_API_KEY is required (value is never logged)")
        from app.ai.contracts import AgentContext, Slots
        from hangil_r2 import LLMAgent
        from hangil_r2.llm import OpenAILLM
        from openai import OpenAI

        policy = data["protocol"]["budget"]
        ledger = BudgetLedger(policy, args.output.with_suffix(".ledger.json"))
        if args.previous_failed_run:
            previous = json.loads(args.previous_failed_run.read_text())
            restore_auth_attempt(
                previous, ledger, args.freeze_commit, meta["sha256"], commits
            )
            result["previous_auth_failure_sha256"] = hashlib.sha256(
                args.previous_failed_run.read_bytes()
            ).hexdigest()
        api = OpenAI(
            api_key=key,
            base_url="https://api.openai.com/v1",
            max_retries=0,
            timeout=policy["timeout_s"],
        )

        class BoundedLLM(OpenAILLM):
            def __init__(self):
                self.compose_ids = []

            def _ask(self, content):
                index = ledger.reserve(content)
                try:
                    reply = api.chat.completions.create(
                        model=data["protocol"]["final_answer"]["model"],
                        messages=[{"role": "user", "content": content}],
                        temperature=0,
                        max_tokens=policy["max_output_tokens"],
                    )
                except Exception as exc:  # noqa: BLE001 - redact errors and retain cost reservation
                    ledger.attempts[index].update(
                        state="usage_unknown", error_class=type(exc).__name__
                    )
                    ledger.save()
                    raise EvaluationStop(
                        "Provider failure: " + type(exc).__name__
                    ) from None
                if reply.usage is None:
                    raise EvaluationStop("Provider did not return token usage")
                ledger.settle(
                    index,
                    reply.usage.prompt_tokens,
                    reply.usage.completion_tokens,
                    reply.model,
                )
                if reply.choices[0].finish_reason != "stop":
                    raise EvaluationStop(
                        "Incomplete model response; no automatic retry"
                    )
                return reply.choices[0].message.content or ""

            def compose(self, question, hits, language):
                self.compose_ids = [h.document_id for h in hits]
                return super().compose(question, hits, language)

        map_, map_info = load_live_map(root)
        result["map"] = map_info
        rows, traces = [], []

        def traced_search(query, language, context):
            hits = search(query, language, context)
            traces.append(
                {
                    "query": query,
                    "language": language,
                    "slots": context.get("slots", {}),
                    "hits": [
                        {
                            "document_id": h.document_id,
                            "excerpt": h.excerpt,
                            "source_url": h.source_url,
                            "verified_at": h.verified_at,
                        }
                        for h in hits
                    ],
                }
            )
            return hits

        llm = BoundedLLM()
        agent = LLMAgent(llm, search_knowledge=traced_search)
        result.update(rows=rows, completion="running", semantic_review="pending")
        try:
            for case in data["cases"][: policy["max_questions"]]:
                traces.clear()
                llm.compose_ids = []
                calls_before = len(ledger.attempts)
                ctx = AgentContext(
                    language=case["lang"],
                    map=map_,
                    state="idle",
                    slots=Slots(),
                    destination_poi_id=None,
                    confirmed_node_id=None,
                )
                response = agent.handle_message(
                    ctx, case["q"], None, None
                ).response.model_dump(mode="json")
                cite = citation_diagnostic(response, llm.compose_ids)
                rows.append(
                    {
                        "id": case["id"],
                        "question": case["q"],
                        "kind": case["kind"],
                        "response": response,
                        "search_traces": list(traces),
                        "compose_document_ids": list(llm.compose_ids),
                        "citation_diagnostic": cite,
                        "diagnostic_patterns_present": [
                            bool(
                                re.search(
                                    p, response["assistant_message"], re.IGNORECASE
                                )
                            )
                            for p in case["diagnostic_patterns"]
                        ],
                        "api_calls": len(ledger.attempts) - calls_before,
                        "semantic_review": "pending",
                    }
                )
                result["budget"] = ledger.report()
                args.output.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2) + "\n"
                )
                print(
                    f"{case['id']}: {response['status']}; calls={len(ledger.attempts)}",
                    flush=True,
                )
            result["completion"] = "complete"
        except EvaluationStop as exc:
            result.update(completion="stopped", stop_reason=str(exc))
        finally:
            result["budget"] = ledger.report()
            result["not_executed"] = [c["id"] for c in data["cases"][len(rows) :]]
    _, final = load_rag(root, 0.25)
    if final != inputs or source_commits(root) != commits:
        raise ValueError("Pinned source inputs changed during evaluation")
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 1 if result.get("completion") == "stopped" else 0


if __name__ == "__main__":
    raise SystemExit(main())
