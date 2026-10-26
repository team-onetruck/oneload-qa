# QA #3 — RAG PR #4 v3 판정 (2026-10-26)

[QA #3](https://github.com/team-onetruck/oneload-qa/issues/3)의 최신 댓글이 요청한 [RAG PR #4](https://github.com/team-onetruck/oneload-rag/pull/4)를 검사했다. **새 평가와 QA 실행기 보완은 완료했지만, 검색 품질 기준은 미달이다. 임계값 확정은 보류하고 QA #3을 open으로 유지한다.** 기존 Q10·근거 열 반영·로컬 R3 연결 완료는 유지한다.

## 사전 고정과 비교 범위

- 질문·근거·판정 규칙을 후보 구현과 검색 결과를 읽기 전에 QA [`7fc51da`](https://github.com/team-onetruck/oneload-qa/commit/7fc51da8c80a0ced78160f9dc057cb6138b7602d)로 먼저 commit/push했다. [사전 절차](issue3-v3-protocol.md), [질문 48개](../eval/retrieval_holdout_v3.json), [메타데이터](../eval/retrieval_holdout_v3.meta.json)를 따른다.
- 데이터 SHA256: `ed34a3fa3237eff4833ff8f090eccde89cc813d8dac8cbee8f1657d751f02d6a`. 양성24·범위밖24, 한·영 24개 질문군이다. 합성 질문이며 번역 쌍은 서로 연관된다. 사람 검토 완료나 독립 사용자48명을 의미하지 않는다.
- RAG main `f99704d3ced3cfd351eaaf65f0aeeefdc8882f93`와 PR4 `d83e89fadf17c397b45103a8c0b529d6a539c38d`를 각각 한 번 측정했다. 각 커밋의 공식14문서·자체 메타데이터를 사용했다. 후보는 검색 코드와 `priced` 지식 메타데이터를 함께 바꿨으므로 코드만 바꾼 실험이 아니다.
- 공식 MemorySearch의 min_score0.25/k3/상대0.5를 고정했다. 임계값 sweep·결과 확인 후 질문/정답 수정·기준 완화는 하지 않았다. 기존 잠정 조건은 **양성 top3≥90%와 범위밖 오탐0**, 노출 회귀셋의 기존 양성 적중 보존이다.

## 새 v3 결과

| 검사 | main f99704d | PR4 d83e89f | 후보 판정 |
|---|---:|---:|---|
| 양성 top1 | 18/24 | 13/24 | 참고 지표 |
| 양성 top3 | 21/24 | **14/24 (58.3%)** | 90% 미달: 최소22/24 필요 |
| 범위밖 빈 결과 | 14/24 | **15/24** | 오탐9건, 기준0건 미달 |
| 노출 평가셋의 이전 적중 양성 회귀 | — | 0건 | 이 조건만 충족 |

[문항별 결과·코드/지식/실행기 SHA](../reports/retrieval-v3-review-20261026.json). 새 양성 중 이전 적중→실패는 H3-01-en, H3-05-ko/en, H3-06-ko/en, H3-08-ko/en의7건이다. 후보의 총 양성 누락은10건이다. 새 v3는 이제 노출된 회귀셋이며 다음 수정의 미관찰 합격 판정으로 재사용하지 않는다.

대표 실패는 다음과 같다. 질문 원문과 반환 ID는 보고서에 모두 보존했다.

| 종류 | 문항 | 관찰 |
|---|---|---|
| 정상 질문 누락 | H3-01-en: T1/T2 직통열차 정상운임 비교 | 기존 적중이 후보에서 빈 결과 |
| 정상 질문 누락 | H3-05-ko/en: 기후동행 2일권과 실물 카드 가격 분리 | 기존 적중이 두 언어 모두 빈 결과 |
| 정상 질문 누락 | H3-06-ko/en: 오후5시 이후 Mpass 3일권 가격 | 기존 적중이 두 언어 모두 빈 결과 |
| 정상 질문 누락 | H3-08-ko/en: Tmoney Travel/Plus 구매 가격 비교 | 기존 적중이 두 언어 모두 빈 결과 |
| 근거 없는 비용 질문에 검색 반환 | H3-13-ko: 직통열차 창가 좌석 변경 추가 비용 | 직통·일반 요금 등 문서 반환 |
| 근거 없는 속성에 검색 반환 | H3-16-ko/en: 분실 WOWPASS 재발급 수수료 | 카드 구매/일반 안내 문서 반환 |
| 실시간 질문에 검색 반환 | H3-22-ko: 다음 직통열차가 매진됐는지 | 정적 요금·안내 문서 반환 |

이는 **검색 반환의 범위 판정 실패**다. 실제 LLM이 잘못된 금액을 답했다고 판정한 결과가 아니다. Agent의 답변 가능 여부·인용 근거 검사는 별도로 필요하다.

후보 코드 검토상 `price_reason()`은 가격 외 낱말에 모르는 말이 하나만 있어도 먼저 거절하며, 반대로 알려진 `priced` 대상이 포함되면 그 대상의 어떤 비용을 묻는지까지 구분하지 않는다. 정상 질문 표현의 보존과 대상·속성별 근거 판정을 함께 살펴볼 필요가 있다. `_REALTIME`의 표현 목록에도 한국어 ‘매진’은 없다. 이 원인 분석은 코드와 실패 사례를 대조한 해석이며 모든 실패의 원인을 개별 추적한 결과는 아니다. 다른 역할의 코드는 수정하지 않았다.

## 이미 노출된 평가셋: 진단용

| 세트 | main 양성 top3 → 후보 | main 범위밖 빈 결과 → 후보 |
|---|---:|---:|
| R6 개발 | 10/10 → 10/10 | 5/6 → 6/6 |
| R6 기존 holdout v1 | 10/10 → 10/10 | 6/6 → 6/6 |
| R6 기존 holdout v2 | 17/20 → 19/20 | 15/20 → 20/20 |
| R3 현재 legacy (총47문항) | 42/43 → 42/43 | 4/4 → 4/4 |
| R3 기존 holdout | 16/16 → 16/16 | 9/12 → 10/12 |

노출된 v2의 개선은 확인했다. 이 결과를 새 v3와 합산하거나 미관찰 품질 개선으로 표시하지 않는다. 기존 호텔·잔여석·택시 진단은 범위밖 차단2/3→3/3이다.

## 연결·회귀 검사와 새 main 관찰

처음 고정한 연결 프로필은 Backend2ebd94d·Agenta732577·Data89ec570(지도2026-10-25.1)·RAG PR4다. **RAG125/125·Backend72/72·공식검색 API28/28·실제 전역app 모의API7/7**, Data 검증기·Agent 호환/E2E·RAG↔Backend E2E가 통과했다. QA 실행기는 `--dataset/--metadata`와 사전 커밋 대조, 기존 양성 회귀 방지 판정을 추가했고 **QA51/51**을 확인했다.

마지막 원격 대조에서 Data PR3과 Agent PR10의 병합도 확인했다. 새 main은 **Data72d5eb8(지도2026-10-25.2)·Agent55b0220**이다. 둘만 교체하고 RAG는 같은 PR4로 둔 별도 프로필의 결과는 다음과 같다.

- Backend72/72·공식검색 API28/28·전역app 모의API7/7·Data 검증기·RAG↔Backend E2E 통과.
- **RAG122/125 통과, 실패3·skip0:** 위치 카드와 별칭 사전의 지도 버전이25.1에 머문2건, 정확한 POI 기대 불일치1건(질문8개)이다. 첫 예는 ‘보증금 환급기’가 `poi-single-use-card-refund`, `poi-arex-deposit-refund` 두 후보를 반환한다.
- **Agent 호환 검사 exit1:** Data 새 지도와 Agent `mocks/maps` 사본이 달라 E2E 실행을 건너뛰었다. 이를 E2E 통과나 실제 API 실패로 집계하지 않는다.

[두 연결 프로필의 커밋·지도 SHA·테스트 결과·API 구조화 증거](../reports/issue3-compatibility-20261026.json). 새 지도/Agent 조합으로 v3 검색을 다시 실행하지 않았다. 기존 main 전체 검사/경로 실패 보고서는 그 당시 SHA의 이력으로 남기며, 새 병합 main 전체 검증을 했다고 바꾸지 않았다. 이번에는 다른 역할의 checkout을 pull·수정·push하지 않았다.

## 이슈 완료 조건과 후속 작업

| QA #3 조건 | 현재 처리 |
|---|---|
| Q10 유형·기대 | 완료 유지, 근거·확인일 기대 보존 |
| service_gold 근거 열20건 | 반영 완료 유지, 사람 검토 대기 |
| R3 로컬 검색 연결 재검사 | 완료 유지, 새 main 조합에서도 API28/28·7/7 |
| RAG PR4 v3 평가 요청 | **평가·실패 분석·보고 완료** |
| 보강 평가셋을 통한 임계값 확정 | **미완료: v3 정상 누락10·오탐9** |

R3가 정상 표현·근거 없는 속성/실시간 질문·새 지도 매핑을 보완하고 R2가 지도 사본을 동기화한 뒤, 노출된 v1/v2/v3 회귀와 새 미관찰 평가를 구분해 다시 판정해야 한다. `v0.4.0` 태그·Backend 의존성 pin·배포 조합 승인을 이번 QA 결과로 진행할 근거는 없다. 이 작업에서는 QA 저장소와 QA #3만 갱신하며 다른 저장소의 이슈/댓글/PR은 변경하지 않는다.

모든 AI·임베딩 호출0회, FakeLLM/FakeEmbedder·합성 입력·QA 전용 일회용 PostgreSQL만 사용했다. DB는 정리했다. 실제 모델·pgvector 실제 임베딩·릴리스 설치·배포·실기기·현장 사진·사람 근거 검토는 미검증이다. 원시 로그·키·DB 비밀값은 공개하지 않는다.

## 재현

`requirements-validation.lock.txt`의 Python3.12 환경과 별도 고정 checkout을 사용한다. 각 root 아래 여섯 저장소를 함께 두고 `oneload-rag`를 각각 f99704d/d83e89f로 지정한다. 공개 후에는 아래 실행도 v3 회귀 재현이며 새 holdout으로 보지 않는다. 출력은 새 경로를 사용한다.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/recheck_rag_issue3.py \
  --before-root /path/to/main-profile \
  --after-root /path/to/pr4-profile \
  --freeze-repo . \
  --freeze-commit 7fc51da8c80a0ced78160f9dc057cb6138b7602d \
  --dataset eval/retrieval_holdout_v3.json \
  --metadata eval/retrieval_holdout_v3.meta.json \
  --output results/new-v3-reproduction.json

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests
OPENAI_API_KEY='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_backend_tests.py \
  --project-root /path/to/pr4-current-profile --with-rag \
  --output results/new-issue3-api
```

첫 명령의 exit1은 이번 검색 기준 미달의 정상 보고다. Backend 검사는 실행기가 새로 만든 폐기 DB만 사용한다. RAG 전체 검사도 자체 일회용 pgvector DB·FakeEmbedder와 `RAG_REQUIRE_CONTRACT=1`, 각 프로필의 Data/Agent/Backend 경로를 명시했다. 기존 DB URL이나 배포 스크립트로 재현하지 않는다.
