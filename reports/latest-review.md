# 최신 QA 검토

## 원격 공유와 수정 이슈 — 2026-10-25

배포 서버는 꺼진 상태로 로컬 검증했다. 검증 코드·보고서는 포크에 push했고 [QA PR #5](https://github.com/team-onetruck/oneload-qa/pull/5)로 원본 main 반영을 요청했다. 원본 직접 쓰기는403으로 거절돼 병합 대기이며, 현재 공유/이슈 증거는 [publication](publication-20261025.json)를 따른다. 소스가 같아 새 테스트 통과로 재집계하지 않았다.

수정 항목은 [App #40: 생성 계약 누락](https://github.com/team-onetruck/oneload-app/issues/40), [Data #2: 경로19/24 단절](https://github.com/team-onetruck/oneload-data/issues/2#issuecomment-6392629139), [RAG #3: 검색 누락3·오탐5](https://github.com/team-onetruck/oneload-rag/issues/3#issuecomment-6392629320)에 남겼다. Agent #5/#7·QA #3도 최신 근거를 추가했고 Backend #2는 해결 재확인/closed를 유지했다.


## 인수 후 최신 QA — 2026-10-25 11:30 KST

[검토·환경·다음 작업](takeover-review-20261025.json) · [기준선](baseline.json) · [인수인계](../docs/handoff.md).

현재 검증 묶음은 App `12ba6c6` / Backend `9067553` / Agent `a732577` / Data `89ec570` / Infra `6cf4a65` / RAG `f99704d`다. GitHub main과 대조한 새 복사본에서 실행했으며 원래 사용자 checkout은 보존했다. QA는 로컬 `qa/` 폴더, 새 Python **3.12.9** 가상환경이다.

| 검사 | 실제 결과와 범위 |
|---|---|
| QA / Agent / Backend / 데이터 구조 | 48/48 · 47/47 · 71/71 · 3/3 |
| component v2 | 20/20 시나리오·21/21 턴, 사람 검토 21턴 대기 |
| 모의 검색 주입 API / 공식 RAG 주입 API | 27/27 · 28/28, 별도 프로필 |
| 실제 전역 app 조립의 모의 API | 7/7, FakeLLM·공식 로컬 MemorySearch 강제 설정 |
| 출구·반납기 경로 | **5/24 연결(자기 위치 2건 포함), 19건 경로 없음 → 전체 exit1** |
| App 로컬 검사 | lint·타입·단위 513/513·빌드 통과; 브라우저·실기기 인수 NOT_RUN |
| 노출된 검색 v2 회귀 | top3 17/20·범위밖 빈 결과 15/20, 새 독립 검증 아님·기준 미달 |

Backend #2의 반납 완료 갱신은 API-26과 기존 회귀에서 해결 확인했다. Data #2는 계속 open이다. App HTTP 연결을 새 소스 해시에 묶어 wired로 검토했지만 생성 타입은 구 intent 6개이며 plan/steps 화면 연결은 남아 있다. Agent #7은 open이다.

INT-07은 **로컬 강제 MemorySearch 프로필에서 실제 전역 entrypoint→공식 검색→API 연결 확인**으로 갱신했다. 배포 환경·pgvector·실제 모델의 인수는 아니다. Backend 의존성은 RAG `v0.3.0`(`ec27e09`)을 pin하지만 이번에는 형제 최신 main을 사용했다. 두 버전의 지식 메타데이터가 달라 release 설치/배포 조합은 별도로 검증해야 한다.

App CI의 verify/e2e는 성공했지만 deploy는 취소됐고 Backend·Agent deploy는 대기다. 과거 배포 성공을 최신 배포 완료로 표시하지 않는다. 실제 모델·임베딩 호출 **0회**, 현장 사진 정답 **0건**, 휴대폰·카메라/센서 정확도·거리뷰 현장 인수 **NOT_RUN**이다. Camera 오버레이·AR 기반 코드와 draft Unity PR #39로 현재 2D·거리뷰 QA 범위를 확대하지 않았다.

설치 충돌(`langgraph-sdk0.4.8`의 websockets<17)을 해결해 `websockets16.1.1`로 고정하고 새 설치·pip check를 확인했다. QA 실행기는 형제 RAG를 명시적으로 선택하고 커밋을 기록한다. Agent 단독 시험에는 Backend 경로를 섞지 않는다. 추가한 경로 검사와 운영 조립 API 검사는 기존 동결 평가셋을 바꾸지 않는다.

아래 10월 23일 기록은 각 당시 버전의 이력이며 현재 판정은 위 기록과 최신 기준선을 따른다.

## 2026-10-23 과거 기록

# 최신 Data·Backend 확인

## Data·Backend 최신 확인 — 2026-10-23 17:00 KST

[새 검토 증거](data-backend-review-20261023.json) · [현재 기준선](baseline.json) · [전체 아키텍처](../docs/architecture-current-20261023.md).

- Backend **b1aa5f5**: 행동 계획·규칙 엔진·다중 경유지 경로·추천 단계 수락/건너뛰기/완료 API·폐쇄/휠체어 필터·DB migration0003 추가. Agent intent3개/슬롯4개도 공개 계약과 동기화됐다.
- Data **9fc786e**: node.area(paid/free), edge/POI.closed 스키마가 추가됐다. 지도 JSON은3b5ef0e 때와 동일한2026-10-23.1이며 유료구역 필드는12노드 모두 미입력이다. 새 출구/반납기 경로 단절 **Data #2는 유지**한다.
- QA44·Agent47·Backend68·Data3·component20/21 통과. 기존 모의 API20/20 확인 후 여러 턴/행동 계획 검사7개를 추가해 `r6-boundary-v2`로 구분했다. **모의 API26/27·공식 MemorySearch 주입 API27/28**, 공통 실패는 API-26이다. 실제 모델/임베딩 호출0·현장 사진 정답0이다.
- **Agent #7의 Backend500·슬롯 유실은 해결 확인:** 새 구매/출구/탑승 intent와6슬롯이 실제 여러 턴 API에서 유지된다. App42455dc의 생성 schema.d.ts는 기존 intent6개라 Frontend 타입 동기화가 남아 이슈는 닫지 않았다.
- **새 [Backend #2](https://github.com/team-onetruck/oneload-backend/issues/2):** PATCH 없이 대화로 미반납→반납 완료를 말하면 응답 슬롯은yes인데 plan.facts.refund_status는NOT_REFUNDED, 미완료 환급 추천1개가 남는다. _learn_facts가UNKNOWN만 채워 과거 대화 정보를 갱신하지 못한다. 클라이언트 PATCH 우선순위 보호와 대화 정보 갱신을 구분해야 한다.
- Backend CI39920169066의 시험/이미지/배포 성공, Agent39913229016 재실행의 시험/호환/API/배포 성공. 로그 조합은 Backendb1aa5f5·Agenteca420e·Data9fc786e·App42455dc다. 배포 GET도200·DB ok·intent9개·지도2026-10-23.1을 확인했다. 과거16:16의 skipped/구지도 관찰은 최신 상태가 아니다.
- 운영 RAG는 여전히MockKnowledgeSearch(INT-07 partial). App에 plan/steps API 화면 연결은 없고 실제 모바일·모델·현장 인수는NOT_RUN이다. 행동 계획 테스트는 가상 역 fixture와 일회용 DB 검증을 포함하며 서울역 현장 정확도 평가가 아니다.

다음 순서: Backend #2 상태 갱신 → Data #2 경로 연결 → App 생성 타입·행동 계획 UI 연결 → 동일 커밋 묶음 API 재검증 → 공식 RAG·근거/인용·실제 모바일 인수. 사용자 대화의 토론은 계속 참고 자료로만 유지한다.

---

## 이전 아키텍처·회귀 확인 — 2026-10-23 16:16 KST

[전체 구조 설명](../docs/architecture-current-20261023.md) · [새 구조화 증거](architecture-review-20261023.json) · [계약 감사](architecture-contract-audit-20261023.json) · [배포 GET](architecture-server-readonly-20261023.json).

App42455dc·Backend15ddd9f·Agenteca420e·Data3b5ef0e·Infra6cf4a65·RAG8c8e902다. Agent/Data만 새 변경이다. QA44/44·Agent47/47·Data3/3·component20/20시나리오와21/21턴 통과, Backend50/51이다. 새 intent가 MessageOut에서 거절돼500, 슬롯4개도 다음 context에서 소실된다(INT-02). Agent 최신 CI도 동일 실패·배포 skipped다. [Agent #7](https://github.com/team-onetruck/oneload_agent/issues/7)에 등록했다.

Backend의 실제 plan_route로 새 목적지 연결을 검사해 대합실·KTX·4호선·공항철도 승강장에서 반납기/1번 출구까지 경로 없음도 확인했다([Data #2](https://github.com/team-onetruck/oneload-data/issues/2)). 데이터 스키마 통과와 경로 완성은 다르다.

운영 RAG는 MockKnowledgeSearch이고 verify_v4는 질문/응답 관련성 검사만 한다. 근거 판정·인용 처리는 Agent #5 미완료다. 배포 GET4곳은200·DB ok지만 지도2026-10-22.1로 최신 Data와 다르다. 서버 Agent SHA는 GET으로 확인하지 못했다.

QA 실행기는 v3 고정을 제거하고 선택 Agent 기본 버전·verify 파일까지 검증/해시한다. Backend 시험 실패로 후속 모의 API·RAG API는 이번 조합에서 NOT_RUN이다. 필요한 전체 API 증거가 없어 baseline.json을 덮어쓰지 않았다. 아래·baseline의 성공 수치는 직전 조합이다. 질문·정답·평가셋 SHA를 변경하지 않았으며 실제 모델/임베딩 호출0회다.

---

## 직전 완결 실행: 의존성·QA 확인 (15:40)


Backend15ddd9f·Agent5038b5c·Infra6cf4a65 변경을 확인했다. App42455dc·RAG8c8e902·Data606f648은 그대로다. 제품 동작 코드 변화는 없으며 로컬 Agent editable 설치와 CI/배포 커밋 URL 고정을 정리한 변경이다.

별도 Git 복사본에서 uv sync --frozen의 editable 설치, 정확한 SHA로 pin_agent.sh 실행 후 archive 설치, 코드·프롬프트3종·mock 지식 포함, 잘못된 SHA의 수정 전 차단을 확인했다. 원본 Backend source/lock과 배포는 변경하지 않았다.

최신 QA42·Agent43·Backend51·데이터3·component20시나리오/21턴·모의 API20·RAG 주입 API21 통과. 현재 Backend CI(39912151867)·Agent CI(39912174444)의 시험·이미지/호환·배포도 성공이다. 전체 exit1은 운영 검색이 demo인 INT-07 partial 때문이다. 실제 모델/임베딩 호출0회다.

[설치·CI·실행 증거](dependency-review-20261023.json) · [현재 기준선](baseline.json) · [RAG API](rag-integration-probe.json)

아래는 직전 기능/배포 변경 검토다. 각 기록의 커밋과 시각을 구분한다.

## 직전 QA — 2026-10-23 15:29 KST

[현재 구현과 토론 맥락](../docs/current-implementation-20261023.md) · [소스·CI·검증 범위](current-system-review-20261023.json) · [배포 GET 확인](server-readonly-20261023.json)

App42455dc·Backendf9d790f·Agenta089746·Data606f648·Infra8f03327을 사용했다. 개발 pin7f116de와 Agent a089746의 패키지 코드는 같고 문서/CI가 다르다. 공용 배포는 Agent main을 체크아웃해 개발 pin을 덮어쓴다.

| 검사 | 결과 |
|---|---|
| QA | 42/42, skip0 |
| 데이터 | 3/3 |
| Agent | 43/43 |
| Backend | 51/51 |
| component v2 | 20/20시나리오·21/21턴 |
| 모의 검색 API | 20/20 |
| RAG8c8e902 MemorySearch0.25 주입 API | 21/21 |
| Frontend 호출 경로 | ApiAdapter 단일 흐름의 새 profile42455dc, wired |
| 운영 entrypoint | FakeLLM으로 실제 전역 app 조립 검사, Agent·Vision 조건부 연결/공유 확인 |

[기준선](baseline.json) · [감사](contract-audit.json) · [RAG 주입 API](rag-integration-probe.json)

**INT-07은 부분 완료**다. 운영은 키가 있으면 LLMAgent·LLMVision, 없으면 RuleAgent·NoVision이다. 따라서 과거의 무조건 RuleAgent/NoVision 판정은 최신에 적용하지 않는다. 다만 검색이 MockKnowledgeSearch여서 R3 운영 연결은 미완료이고 전체 exit1이다. DATA-01과 사람 정답 검토도 남는다.

App 최신 CI는 단위429·E2E11(mock7+모의 HTTP4), Agent CI는 자체/Backend 호환/API 시험·배포가 모두 통과했다. 공용 reusable 배포로 GH_TOKEN 전달 경로를 제거해 App #32·Agent #6을 닫았다. Backend 최신 CI도 시험·이미지·배포 성공이다. App 최신 배포39911399631의 서버 실행 커밋은 위 조합과 일치한다. 홈/언어 메뉴·기기 언어 감지도 반영됐다.

배포 첫 화면/health/OpenAPI는 GET만 실행해200·DB ok·LLMAgent/LLMVision 표시를 확인했다. R2의 실제 OpenAI 메시지1회 확인 문서는 작성자 보고로 구분하며 이번 R6가 반복하지 않았다.

사용자 토론은 참고 맥락이다. 현재는 모의 고정 사진 결과와 Live 인식이 구분되고, 실제 안내는 단계 문구+도식형 노선+거리뷰다. 평면도·도착지 입구 전용 사진·완전한 가상 역을 구현하거나 인수조건을 확정한 것으로 쓰지 않는다.

실제 모델/임베딩 호출0회, 현장 사진 정답0건, component21턴 사람 검토 대기다. 이전 retrieval v2 top3 17/20·범위밖 빈 결과17/20은 노출된 과거 검색 증거로 유지했다. Agent #5/RQ-32와 RAG #3·QA #3은 미완료다. 최초 Backend 실행기 의존성 오류는 보완 후 새 일회용 DB로 재실행했으며 실패한 초기 시도를 제품 결함이나 통과 수치로 집계하지 않았다.
