# 본인 작성 이슈 재확인 — 2026-10-26 10:46 KST

현재 GitHub 계정 `mootwo0202`가 작성한 한길 이슈 **18건(열림4·닫힘14)**의 본문·답글·상태를 확인했다. 다른 프로젝트의 이슈는 채팅에서 별도로 전달하며 공개 QA 문서에 내용을 옮기지 않는다. 이번 요청은 확인이므로 실제 이슈·댓글·종료 상태는 변경하지 않았다.

[구조화 기록·댓글 링크](../reports/authored-issue-review-20261026.json) · [직전 동일 SHA 실행](latest-main-retest-20261026.md) · [인수인계](handoff.md).

## 열린 한길 이슈 4건

| 이슈 | 현재 확인 결과 | 정리 방향 |
|---|---|---|
| [Data #2](https://github.com/team-onetruck/oneload-data/issues/2) | **등록 그래프 단절은 해결 확인.** Data72d5eb8·Backend2ebd94d의 직전 실행에서 출구/반납기78/78, 모든 노드쌍1521/1521 연결. 무료구역870쌍에 불필요한 gate0건 | 원래 경로 단절 범위의 **종료 후보**. 현장 통행·거리·접근성 검증을 완료했다는 의미는 아님 |
| [Agent #7](https://github.com/team-onetruck/oneload_agent/issues/7) | **Backend500·슬롯 유실은 해결.** Agent21378b5·Backend2ebd94d에서 API20~25의 구매/출구/탑승 여러 턴이 통과. 최신 R2 답글도 서버 쪽 해결과 App#41 이관을 제안 | App#41로 Frontend 잔여를 모으고 원래 서버 오류 이슈를 정리할 수 있음 |
| [App #41](https://github.com/team-onetruck/oneload-app/issues/41) | **미해결.** 최신1d0fc11도 생성 타입 SHA가 동일. 새 intent3개·슬롯4개·plan/steps 타입 누락 유지. 새 답글 없음 | 현재 Backend OpenAPI로 재생성하고 소비 경계 검증 필요 |
| [RAG #3](https://github.com/team-onetruck/oneload-rag/issues/3) | **최초 예시는 개선, 전체 품질 조건은 미완료.** 호텔/잔여석 원문은 현재 main·0.35에서 다시 빈 결과 확인. 공개v3는 main21/24·차단14/24, 직전 후보315701a22/24·차단8/24로 기존 조건 미달 | 검색/답변 기준 합의와 새 평가 필요. 새 PR head b6e3ad3의 정적 대조와 직전315701a 실행을 구분 |

Data#2 본문의 ‘19/24 경로 없음’과 Agent#7 제목의 ‘현재500’은 최초 보고 당시 상태다. 이를 지금의 실패로 반복하지 않는다. 이번 검토는 같은 SHA의 10:12 실행 증거를 대조했으며 전체 테스트를 다시 실행하지 않았다.

RAG 최신 답글은 [PR4](https://github.com/team-onetruck/oneload-rag/pull/4)와 QA#3의 기준 논의로 이어진다. PR head는 **b6e3ad39d98125080109b5e5a2111d25bcc7beaf**다. 315701a 이후 변경된 검색 모듈3개와 평가 파일1개는 주석·docstring을 제외한 Python AST가 같다. 추가 지연 측정 스크립트는 실행하지 않았다. 이를 새 head의 전체 테스트·새 holdout·실제 모델 판정으로 기록하지 않는다. QA#3은 다른 작성자의 이슈여서 본인 작성18건 집계에는 포함하지 않는다.

## 닫힌 14건

| 이슈 | 원래 문제 | 현재 확인 |
|---|---|---|
| [Infra #1](https://github.com/team-onetruck/oneload-infra/issues/1) | public 저장소를 private로 설명 | 현재 README와 App/Backend visibility=public 일치, 해결 유지 |
| [Backend #2](https://github.com/team-onetruck/oneload-backend/issues/2) | 환급 완료 대화 뒤 facts 미갱신 | API26의 REFUNDED·미완료 환급0건 확인, 해결 유지 |
| [Agent #6](https://github.com/team-onetruck/oneload_agent/issues/6) | CI의 GH_TOKEN 배포 전달 실패 | 해당 dispatch 경로 제거·공용 배포 workflow 유지. 현재 다른 원인의 CI 실패는 아래에 분리 |
| [App #32](https://github.com/team-onetruck/oneload-app/issues/32) | 같은 GH_TOKEN 전달 실패 | 공용 배포 workflow 유지, 최신 CI verify/e2e/deploy 모두 success |
| [App #16](https://github.com/team-onetruck/oneload-app/issues/16) | Demo controls 사진 결과 설명 불일치 | 데모 패널 제거, README의 서버 응답 설명 일치 |
| [QA #4](https://github.com/team-onetruck/oneload-qa/issues/4) | mock 문자열로 HTTP 미연결 오판 | 소스 해시·호출 경로 검토 방식 유지, 최신 웹 소스도 검토 프로필과 동일 |
| [App #11](https://github.com/team-onetruck/oneload-app/issues/11) | README의 HTTP 채팅 설명 불일치 | 현재 단일 HTTP adapter와 README/구조 설명 일치 |
| [RAG #2](https://github.com/team-onetruck/oneload-rag/issues/2) | 연결 예제의 Agent Vision 누락 | 같은 Vision을 Agent/app에 전달, 직전 사진·전역 조립 API 통과 |
| [RAG #1](https://github.com/team-onetruck/oneload-rag/issues/1) | 필수 계약 테스트가 조용히 skip됨 | job env의 RAG_REQUIRE_CONTRACT 유지. 직전 강제 계약101건은 skip0이며 별도 지도 실패3건을 실제 실패로 보고 |
| [QA #2](https://github.com/team-onetruck/oneload-qa/issues/2) | 예외 클래스 정적 비교 오판 | 실제 발생 예외로 검사, Vision 장애 API503 확인 |
| [Agent #3](https://github.com/team-onetruck/oneload_agent/issues/3) | 삭제된 Backend 지도 경로 참조 | 현재 Data/--map-dir 해석 정상. 현재 지도 사본 내용 차이는 별도 원인 |
| [Agent #2](https://github.com/team-onetruck/oneload_agent/issues/2) | FAQ/handoff의 Vision 누락 | README/FAQ/handoff와 사진 질문 API15에서 수정 유지 |
| [Agent #1](https://github.com/team-onetruck/oneload_agent/issues/1) | Vision 장애 시500 | Backend 예외 선택·API503 AI_SERVICE_UNAVAILABLE 유지 |
| [QA #1](https://github.com/team-onetruck/oneload-qa/issues/1) | QA가 옛 지도 경로로 중단 | 현재 Data 지도로 표준 전체exit0·component21턴 완료 |

‘해결 유지’는 이번에 각 원인의 소스·문서·최신 답글과 동일 SHA의 기존 실행을 대조했다는 뜻이다. 14건의 모든 재현 절차·배포·실기기 검사를 새로 실행했다는 의미가 아니다.

## 새로 대조한 CI·버전

- [Agent CI40251210562](https://github.com/team-onetruck/oneload_agent/actions/runs/40251210562): test와 Backend tests는 success, **Contract check failure**, 뒤 E2E·deploy는 skipped다. 제한한 로그에서 실제 원인 **‘지도 파일 다름 → mocks/maps/’**을 확인했다. GH_TOKEN 미제공이나 옛 경로의 FileNotFoundError가 아니다. R2 지도 사본 동기화 문제로 별도 추적할 항목이다.
- [App CI40253863816](https://github.com/team-onetruck/oneload-app/actions/runs/40253863816): 최신 **1d0fc11**의 verify·e2e·deploy job success를 관찰했다. 운영 API 응답이나 서비스 품질을 직접 확인한 결과는 아니다.
- App1d0fc11은 Unity 실험 폴더·검사 workflow·관련 문서 추가이며, 웹 런타임/의존성 전체 해시는 10:12에 검사한 dace4c1과 같다. 생성 schema도 동일하다. **관찰 커밋은1d0fc11, 전체 실행 커밋은dace4c1로 구분**한다. R6가 Unity 빌드·Galaxy 실기기 검사를 했다고 표시하거나 현재 모바일웹 인수 범위를 확대하지 않는다.

이번 확인에서 유료 모델·임베딩·DB·배포 실행은 없었다. 원시 CI 로그·비밀값은 공개하지 않는다. 우선 정리할 항목은 Data#2 종료 검토, Agent#7과 App#41의 범위 분리, App#41 수정, RAG 품질 기준/평가이며, 실제 GitHub 상태 변경은 이번에 수행하지 않았다.
