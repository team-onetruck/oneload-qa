# v4 검색·최종 답변 분리 평가 — 2026-10-26

사용자 요청에 따라 검색과 최종 답변의 기준을 나눴다. **검색 기준 미달·모의 답변 계약5/6이며, 사용자 재개로 실제48문항1회를 완료했지만 명확한 사실 오류2건으로 답변 품질도 미달**다. 기존 v1~v3의 실패 기록을 새 기준의 합격으로 바꾸지 않았다.

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

## 3. 실제 모델 답변: 사용자 재개로48/48 완료, 품질 기준 미달

[실제 답변 상세](split-v4-live-review.md) · [48개 답변](../reports/split-v4-live-answers.json) · [문항별 AI 근거 검토](../reports/split-v4-live-review.json).

처음에는 인증 실패로0답변인 상태에서 사용자가 보류했다. 이 기록은 [최초 실패](../reports/split-v4-live-attempt.json)로 보존한다. 이후 키 설정과 **“실제답변만 한번”**이라는 명시적 재개 요청으로, 같은 동결 입력/후보/실행기에서 첫48답변을1회 완료했다. 검색은 반복하지 않았다.

양성24건 중15답변·9거절이며, 명확한 사실 오류는 김포공항→운서 운임과 기후동행 청소년 요금의2건이다. 동결 required_facts 전체 충족은 잠정10/24다. 핵심 답변은 맞지만 추가 사실 생략2건과 시행일 표현 검토1건은 확정 오답과 구분한다. 음성24건은 추측·출처가 없지만 status 계약은20/24다. 인용 구조 오류0/48·URL/확인일17개 일치가 의미상 정확도를 보장하지는 않는다. **R6 AI 근거 검토이며 사람 검토48건은 대기**다.

새 성공 요청125회, 입력90267/출력6559토큰으로 추정USD0.01747545다. 이전 미확인 예약USD0.00114405를 유지한 보수적 합계USD0.01861950<승인USD1이다. 예약은 과금액이 아니며 실제 청구서는 확인하지 않았다. 모델gpt-4o-mini/snapshot2024-07-18·promptv5·재시도0·출력800·기존 예산 보호 규칙은 그대로다. **48문항1회는 완료됐으므로 추가 호출하지 않는다.**

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

실제48답변은 이미 완료했다. 재개 명령을 다시 실행하지 않는다. 측정된 실행은 기존 `split_eval_v4.py --mode live`에 동결 profile/commit, 로컬 키 파일, `--previous-failed-run reports/split-v4-live-attempt.json`, 새 출력 경로를 전달해 이전 예약을 이어받았다. 비밀 파일·원시 로그는 공개하지 않는다. 실제 답변/검색어/출처와 발췌 해시는 구조화 결과에 남겼다.

이번에는 배포·운영/기존DB·HTTP 통합·현장 사진·실기기·실제 임베딩을 사용하지 않았다. 실제 답변은 stateless AgentContext의 합성 텍스트 검사이며 HTTP/배포 검사가 아니다. 당시 QA61/61은 이번 문서 갱신에서 재실행하지 않았다. **RAG/QA 이슈 전체 완료·임계값 승인·릴리스 승인으로 표시하지 않는다.**
