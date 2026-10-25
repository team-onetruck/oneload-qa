# GitHub 현재 main 전체 검증 — 2026-10-25

GitHub의7개 main 커밋을 조회한 뒤 QA 내부에 깨끗한 테스트 복사본을 만들었다. 검사 후 원격 main이 그대로임도 확인했다. 사용자 원본7개 저장소의 파일 해시·HEAD·브랜치·상태는 모두 보존했다. Data의 로컬 미커밋 지도는 이번 Git 검증에 섞지 않았다.

[구조화 증거](../reports/git-main-review-20261025.json) · [현재 main 기준선](../reports/baseline.json) · [이슈 초안](git-main-issue-drafts-20261025.md) · [인수인계](handoff.md)

## 고정한 버전

| 저장소 | 현재 main | 실제 검증 범위 |
|---|---|---|
| QA | 5c082f8에서 실행, 이번 기록은 후속 커밋 | 회귀48·실행기/평가셋·구조화 증거 |
| App | 12ba6c6 | lint·타입·단위513·빌드·모의 API 자동 화면24·생성 계약 비교 |
| Backend | **2ebd94d** | 단위72·API·경로·개찰구 비용 변경·정적 검사 |
| Agent | a732577 | 단위47·component20/21·자체 Backend 호환/E2E·출처 제어 |
| Data | 89ec570 | 지도2026-10-25.1·구조3·경로24조합·R3와 교차 검증 |
| Infra | 6cf4a65 | 소스/구성·CI 상태 확인, 배포 실행 없음 |
| RAG | f99704d | 전체101건·MCP·FakeEmbedder pgvector·검색 노출v2·POI/합성 위치 |

전체 SHA·실행 시각·검사 후 원격 재확인 시각은 구조화 증거와 lock에 있다. Backend만 이전 main 검토의9067553에서 바뀌었다. 새 변경은 통과하는 개찰구 수를 먼저 줄이고 그다음 이동 거리를 비교하는 경로 비용이다.

## main 결과 — 전체 인수 미승인

| 검사 | 실제 결과 |
|---|---|
| QA / Agent / Backend / Data 구조 | **48/48 · 47/47 · 72/72 · 3/3** |
| component | 자동20/20시나리오·21/21턴, 사람 검토21턴 대기·최종 품질점수null |
| 모의검색 API / 공식 MemorySearch API / 전역app 모의API | **27/27 · 28/28 · 7/7** |
| Agent 자체 Backend 호환 / 자체 API E2E | 모두 통과. main 지도 사본은 일치 |
| 출구·반납기 경로 | **5/24 연결·19건 실패 → 표준 전체 실행 exit1** |
| App | lint·타입·단위513/513·빌드·자동 화면24/24 통과 |
| RAG 전체 | **99통과·2실패·skip0**. 별칭 사전/위치 카드의 map_version 불일치 |
| RAG MCP / pgvector 관련 검사 | **6/6 · 7/7**. pgvector 적재/검색 DB 통합1건 포함, FakeEmbedder 사용 |
| 노출된 검색v2 | 양성 top1 14/20·top3 17/20·범위밖 빈 결과15/20. 기준 미달 |
| App 생성 계약 | intent3개·slot4개·plan/steps 계약 누락 유지 → App#41 |
| 인용 출처 제어 | 공식 문서2개를 주입하고 FakeLLM이[1]만 인용해도 출처2개 반환 → Agent#5 미완료 |

RAG 실패는 `test_aliases_match_the_map`, `test_cards_and_cases_match_the_map`다. 두 평가 자료의 버전은2026-10-23.1인데 현재 Data main은2026-10-25.1이다. 질문·정답·버전을 바꿔 통과시키지 않았다. 원본 POI 정확 일치는22/40, R3의 제안 별칭을 메모리에서 덧붙이면40/40이다. 그 별칭이 Data main에 구현됐다는 뜻은 아니다.

기존 GitHub RAG CI 성공은10월23일 실행 기록이다. 이번10월25일의 현재 주변 저장소 조합에서는 위2건이 실패한다. CI의 과거 성공을 현재 조합의 성공으로 대체하지 않는다. 검색v2 역시 이미 노출된 회귀이며 새 holdout이나 실제 답변 품질로 집계하지 않는다.

## 미병합 Git 변경의 별도 검사

### Data PR #3 + 현재 main 코드

[Data PR #3](https://github.com/team-onetruck/oneload-data/pull/3)의 head는 `be91a04`이며 아직 open이다. 지도는2026-10-25.2, SHA256 `6c30e61ebb8ee26517458567e843e9c6168dc630873f9841b644b3f88cc79b18`, 노드39·간선106·POI40이다. 사용자 로컬 미커밋 후보의 간선102·SHAe89bc42c와 다르다. **같은 지도 버전 문자열만으로 같은 입력이라고 판단하지 않는다.**

이 PR 지도만 명시적으로 선택하고 나머지 코드는 위 main 버전으로 검사했다. main baseline은 이 결과로 덮어쓰지 않았다.

- 표준 QA exit0, 경로78/78, 모의API27/27·공식검색API28/28·전역app7/7 통과.
- 실제 Backend 전체 노드쌍1,521/1,521·지정 휠체어9지점81/81 연결. 동일 위치 검사 포함이며 현장 접근성 검증은 아니다.
- 무료 구역의 서로 다른 지점870쌍에서 개찰구를 경유하는 경로가 이전 Backend9067553에서는60건, 최신2ebd94d에서는 **0건**이다. KTX맞이방→반납기도 개찰구0개로 이동한다.
- 이전 로컬 후보에서 실패했던 합성 L24는 이 Git PR 지도에서 다시 빈 후보로 차단된다. 현재 지도 매처의 양성13/20·음성4/4다.
- R3 POI는32/40이다. 새 장소5질문·복수 후보3질문은 범위/기대값 검토가 남는다. 환승 중 표 구매 문구와9-1출구 FakeLLM 처리의 잔여 기록도 유지한다.
- Agent main의 지도 사본은12노드 지도 그대로다. PR 지도 사본 동기화와 R3 메타데이터/기대 범위 조정은 담당 역할의 작업으로 남긴다. QA가 사본·정답을 교체하지 않았다.

### Agent PR #10

[Agent PR #10](https://github.com/team-onetruck/oneload_agent/pull/10)의 head `6f10806`은 아직 open이다. 별도 checkout의 단위 검사는 **72통과·2xfail**이다. L05(트래블센터)·L06(도심공항터미널)의 지도 문구/위치 확인은 미완료로 남아74통과로 집계하지 않았다.

main 지도의 같은 R3 합성24입력에서 main ranker의 중복 후보 사례3건이 PR에서는0건이 됐다. 양성 top1 16/20·top3 18/20·음성4/4는 유지됐다. 이 ranker는 실제 Backend API의 `match_location`과 별개다. PR10+DataPR3의 전체 결합 검사를 했거나 사진 API 순위가 개선됐다고 표시하지 않는다.

Unity PR#39·#42는 둘 다 open·draft다. 현재 모바일 웹2D·거리뷰 인수 범위에 적용하지 않았으며 Unity/AR 런타임·실기기 검증은 수행하지 않았다.

## 이슈·CI·제한

열린 이슈10건의 현재 본문·댓글을 확인했다. Data#2·App#41·Agent#5/#7·RAG#3·QA#3은 위 근거대로 잔여 조건을 유지한다. App#2는ko/en·확인일 표시 경로를 확인했지만 정책 사실에 대한 실제 답변 인수는 하지 않았다. Agent#4는 공식 검색 로컬 연결과 배포/MCP 연결 범위를, Data#1은 아직 반영되지 않은 별칭·시설을, Infra#2는 철회된 과거 복사 제안과 현재 패키지 설치/키 기반 조립을 구분한다. Backend#2와 Infra#1은 해결 확인·closed 상태를 유지한다. **실제 이슈·댓글·PR 상태는 변경하지 않았다.**

해당 head의 GitHub CI에서 App verify/e2e, Backend test/image, Agent test/backend, Data validate, RAG test 성공을 관찰했다. App deploy는cancelled, Backend/Agent deploy는queued여서 배포 완료로 표시하지 않는다. QA 저장소에는 별도 Actions 실행이 없다.

App24개 화면 검사는 Pixel7/데스크톱 크기의 Playwright에서 모의 API와 가상 카메라·센서를 사용했다. 실제 Backend가 연결된 화면·물리 휴대폰·실제 카메라·현장 사진·실제 AI 품질 인수가 아니다. 별도 QA 가상환경의 MCP2.3.0·FakeEmbedder로 DB/도구 연결은 확인했지만 의미적 벡터 검색 품질을 측정한 것은 아니다. Backend가 pin한 RAG v0.3.0 설치 이미지 조합은 이번 형제 main 테스트와 구분한다.

실제 모델/임베딩 호출0회, 운영 DB·배포 사용 없음이다. QA용 일회용 DB는 모두 정리했고 기존 사용자 서버/DB는 건드리지 않았다. 다른 저장소의 코드·평가 정답·미커밋 변경은 수정하지 않았다. QA 기준선·관찰 버전·인수인계·초안만 갱신했다.

## 재현

`PROJECT`는 위 커밋으로 고정한 깨끗한6개 테스트 복사본의 부모다. 사용자의 미커밋 Data가 있는 원본 부모를 main 검사에 지정하지 않는다. 이번 복사본은 QA의 `results/git-main-review-20261025-001/project`에 있다. 항상 새 출력 경로를 사용한다.

```sh
PROJECT="$PWD/results/git-main-review-20261025-001/project"
PYTHONDONTWRITEBYTECODE=1 OPENAI_API_KEY= .venv/bin/python scripts/run_checks.py --project-root "$PROJECT" --with-backend --output results/next-main-full-001
PYTHONDONTWRITEBYTECODE=1 OPENAI_API_KEY= .venv/bin/python scripts/run_backend_tests.py --project-root "$PROJECT" --with-rag --rag-min-score 0.25 --output results/next-main-rag-001
```

현재 main의 예상 표준 종료코드는 경로 실패 때문에1이다. 추가 RAG 메타데이터2건의 DB 없는 재현은 이슈 초안을 따른다. 데이터/코드 변경 후에는 main·PR·미커밋 입력의 SHA를 다시 고정하고 서로 다른 프로필로 실행한다.
