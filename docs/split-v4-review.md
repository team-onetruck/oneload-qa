# v4 검색·최종 답변 분리 평가 — 2026-10-26

사용자 요청에 따라 검색과 최종 답변의 기준을 나눴다. **검색 평가는 완료·기준 미달, 모의 답변 계약은5/6, 실제 답변 사실성은 인증 실패 후 사용자 요청으로 보류**다. 기존 v1~v3의 실패 기록을 새 기준의 합격으로 바꾸지 않았다.

[전체 판정](../reports/split-v4-summary.json) · [사전 규칙](split-v4-protocol.md) · [질문·정답48건](../eval/split_holdout_v4.json) · [메타데이터·SHA](../eval/split_holdout_v4.meta.json) · [인수인계](handoff.md).

## 사전에 고정한 것

후보 구현/새 검색 출력 확인 전에 질문·정답·판정·비용 규칙을 QA [`a4aa849`](https://github.com/team-onetruck/oneload-qa/commit/a4aa8495c5db4bfaf19a1149e09789fdd1e242f3)로 commit/push했다. 데이터 SHA256은 `a9ecdf632bfaf110dc12d1615974023a52d4a48b135e03b554975650e5365dd7`다.

- 양성24·음성24, 한·영24개 질문군이다. 저장된 공식 문서의 주장에 대한 합성 평가이며 현재 실제 요금·현장 사실을 새로 확인한 결과는 아니다. 같은 코퍼스/유사 의도이고 번역 쌍은 연관된다. 기존 공개셋과 정확한 질문 중복은 없으며 사람 정답 검토는 대기다.
- RAG main `f99704d3ced3cfd351eaaf65f0aeeefdc8882f93` / 후보 `024f3076574d02aa2347c9a9bc486629355c42c4`, Agent `21378b5ba02651a2e2f2f84b47612df4ea6cea5b`, Backend `2ebd94d3b93999a196fdfbec8dfa4331a3d51451`를 고정했다.
- 검색은 양쪽 각각1회, 실제 답변은 후보48문항1회만 계획했다. 실제 main 답변의 성능 개선을 측정했다고 주장하지 않는다. 결과 확인 후 질문·gold·기준·임계값을 수정하거나 primary 검색을 반복하지 않았다.

## 나눈 기준

| 단계 | 이번 실험의 QA 기준 | 합격으로 해석하면 안 되는 것 |
|---|---|---|
| 검색 | 공식 MemorySearch0.25/k3/상대0.5에서 양성 top3≥90% | 검색에 무관 문서가 없다는 보장이나 답변 사실성 |
| 범위밖 검색 | 빈 결과·오탐 수를 **진단 지표**로 별도 기록 | 과거 검색오탐0 gate의 실패를 소급 취소 |
| 최종 답변 안전성 | 근거 없는 주장0·무관 출처0·인용 오류0. 음성은cannot_answer+sources0+추측 없음 | FakeLLM 구조 통과를 실제 모델 사실성으로 표시 |
| 정상 답변 유용성 | 양성 질문의 올바르고 근거 있는 답변≥90% | 모든 질문을 거절해서 안전성만 통과 |
| 최종 검토 | 의미/근거 대조와 사람 검토 상태를 별도 기록 | regex 일치나 AI 검토를 사람 인증으로 표시 |

이는 이번 사용자 승인 실험의 분리 기준이다. 팀의 운영 배포·최종 서비스 인수 합격을 자동 확정하지 않는다.

## 1. 검색 평가: 완료, 후보 기준 미달

| v4 raw 질문 | main | 후보 |
|---|---:|---:|
| 양성 top1 | 15/24 | 17/24 |
| 양성 top3 | 16/24 | **19/24 (79.2%)** |
| 범위밖 빈 결과 | 18/24 | 14/24 |
| 범위밖 비어있지 않은 결과 | 6/24 | 10/24 |

90%를 넘으려면 최소22/24가 필요하다. 후보에서 빈 결과가 된 정상 문항은 다음5건이다.

- V4-06-en: T-money 최소/최대 충전액·충전 단위·최대 잔액.
- V4-08-ko: 1회용 카드 보증금의 당일 환급 제한 여부와 카드 훼손 조건.
- V4-11-ko/en: 직통열차에 교통카드 잔액으로 별도 승차권 없이 탑승할 수 있는지.
- V4-12-en: 해외 은행 신용카드로 일반열차1회권을 살 수 있는지.

누락5건의 후속 범위 판정 진단에서는 모두 coverage가 약0.19~0.24로0.25보다 낮아 out_of_scope로 분류됐다. 이 진단은 검색 점수의 재측정이나 임계값 조정이 아니다.

[main 문항별 결과](../reports/split-v4-retrieval-main.json) · [후보 문항별 결과](../reports/split-v4-retrieval-candidate.json). 이 점수는 빈 train slot으로 raw 질문을 넣은 검색 단계다. 실제 Agent가 검색어를 다시 작성한 서비스 답변 성공률과 같지 않다. 이제 v4도 공개됐으므로 다음 개선 구현의 미관찰 판정으로 재사용하지 않는다.

## 2. 답변 계약: FakeLLM 제어 검사5/6

[제어 검사](../reports/split-v4-answer-contract.json)는 공식 문서2개를 미리 주입하고 FakeLLM 문자열을 바꿨다. 한 출처만 인용, NO_ANSWER, 잘못된 번호, 인용 없음, 두 인용의5건은 통과했다.

**실패1건:** 첫 인용 뒤에 긴 글을 넣고600자 이후에 둘째 인용을 두면 둘째 인용이 최종 본문에서 잘리지만 출처2개가 남는다. Agent `_grounded()`가 전체 문자열에서 인용을 수집한 뒤600자로 자르는 순서 때문이다. 이는 인용/출처 기계적 계약의 실패이며 실제 모델의 사실성 측정이 아니다. 다른 역할 코드는 수정하지 않았다.

## 3. 실제 모델 답변: 보류, 사실성 점수 없음

사용자는 최초에 gpt-4o-mini로48문항1회·최대USD1을 승인했다. 첫 API 요청이 **AuthenticationError**로 거부돼 모델 답변은 **0/48**이다. 이후 사용자가 **‘실제 답변 평가는 보류’**를 선택했고 추가 호출은 하지 않았다.

따라서 근거 없는 주장·무관 출처·실제 거절률·양성 답변 유용성은 **미측정/null**이다. 이를0건 오류나 전 문항 안전으로 표시하지 않는다. [인증 실패 구조화 기록](../reports/split-v4-live-attempt.json)을 보존했다. R3의 자체 실제 LLM 수치를 대신 합산하지 않는다.

사용량 응답이 없어서 실제 청구액은 확인하지 못했다. 실행기는 첫 요청의 최악 비용 **USD0.00114405를 보수적으로 예약**해 두었으며 이는 실제 과금액이 아니다. 공식 문서의 [입력/출력 토큰 단가](https://developers.openai.com/api/docs/models/gpt-4o-mini)를 사용하고 캐시 할인은 적용하지 않았다. 재시도0·출력800토큰·입력UTF8 32000바이트+토큰 여유1024·API시도192회 상한·호출 전 비용 예약으로 승인액을 넘기기 전에 중단한다.

인증 실패 뒤 QA 실행기에 로컬 키 파일 선택과 이전 예약액을 이어받는 안전한 재개 경로를 보완했다. 완료된 답변이 있거나 동결 입력/커밋이 다르면 해당 재개 경로는 거부한다. 실행된 검색/첫 요청의 실행기 해시는 결과에 그대로 남기며, 이 보완을 이유로 검색·실제 호출을 다시 실행하지 않았다.

**사용자의 명시적인 재개 요청 전에는 실제 모델을 실행하지 않는다.** 같은 고정 코드에서 첫 실제 답변 평가를 재개할 때는 이전 실패 보고서를 전달해 예산을 초기화하지 않아야 한다. 다른 수정 코드로 바뀌면 v4는 공개 회귀셋으로 구분한다.

## QA 변경·재현

QA에 `split_eval_v4.py`, `probe_answer_contract.py`와 비용/인용/재개 회귀10건을 추가해 **QA61/61**을 확인했다. 기존 main 전체 기준선·동결 v1~v3·서비스/component gold는 보존했다. Backend/App/Agent/Data/RAG/Infra 원본의 HEAD·깨끗한 작업 트리도 전후 동일하다.

평가 환경은 기존 `requirements-validation.lock.txt`의 Python3.12.14다. 실행 명령의 project root 아래에는 고정한 여섯 저장소를 함께 둔다. 새 출력 경로를 사용한다. v4 검색을 다시 실행하면 독립 평가가 아니라 공개 회귀 재현이다.

```sh
OPENAI_API_KEY='' .venv/bin/python scripts/split_eval_v4.py \
  --project-root /path/to/pinned-profile --mode retrieval \
  --freeze-repo . --freeze-commit a4aa8495c5db4bfaf19a1149e09789fdd1e242f3 \
  --output results/new-v4-retrieval-reproduction.json

OPENAI_API_KEY='' .venv/bin/python scripts/probe_answer_contract.py \
  --project-root /path/to/pinned-candidate --output results/new-answer-contract.json
```

실제 답변 재개는 사용자 재개 지시 후에만 다음 형태로 실행한다. 키는 채팅/저장소에 올리지 않는다.

```sh
.venv/bin/python scripts/split_eval_v4.py \
  --project-root /path/to/pinned-candidate --mode live \
  --freeze-repo . --freeze-commit a4aa8495c5db4bfaf19a1149e09789fdd1e242f3 \
  --api-key-env-file /path/to/agent/.env \
  --previous-failed-run reports/split-v4-live-attempt.json \
  --output results/new-v4-answers.json
```

이번에는 배포·운영/기존DB·HTTP 통합·현장 사진·실기기·실제 임베딩을 사용하지 않았다. 실제 답변의 stateless AgentContext 검사는 계획만 했고 유효 모델 응답을 얻지 못했다. **RAG/QA 이슈 전체 완료·임계값 승인·릴리스 승인으로 표시하지 않는다.**
