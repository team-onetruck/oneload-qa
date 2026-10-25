# 열린 이슈별 재검증 — 2026-10-25

mootwo0202 작성 열린 이슈6건, QA 저장소 열린 이슈1건, 개인 소유 저장소 검색을 대조해 중복 제외 **7건**을 확인했다. 여섯 개발 저장소의 원격 main은 이전 QA 때와 같으며 사용자 원본 checkout은 변경하지 않았다.

[구조화 증거](../reports/open-issue-review-20261025.json) · [인수인계](handoff.md) · [버전 관찰](../repos.lock.json)

## 이슈별 판정

| 이슈 | 재검증 결과 | 처리·남은 조건 |
|---|---|---|
| [Infra #1](https://github.com/team-onetruck/oneload-infra/issues/1) | **해결 확인**. Backend·App public 표기, 공개 runner 설명과 Backend CI 주석이 실제 visibility=public과 일치 | 완료 조건3개 체크, **completed로 종료**. 실제 runner 설정·배포 인수 판정은 아님 |
| [Agent #7](https://github.com/team-onetruck/oneload_agent/issues/7) | **부분 해결**. 과거 Backend500·새 intent/슬롯 유실은 새 다중 턴 API에서 재현되지 않음 | App#41의 계약 동기화가 남아 open 유지. 과거500을 현재 실패로 보고하지 않음 |
| [Data #2](https://github.com/team-onetruck/oneload-data/issues/2) | **미해결**. 실제 plan_route24조합 중19건 경로 없음 | 통행 방향·개찰구·유료구역 제약에 맞는 연결 보완 또는 지원 범위/실패 안내 필요 |
| [RAG #3](https://github.com/team-onetruck/oneload-rag/issues/3) | **부분 개선**. 최초 호텔 가격·실시간 좌석 예시는 차단되지만 노출v2 top3 17/20·범위밖 차단15/20 | 정상 누락3·오탐5로 기준 미달, open 유지. 임계값·gold 변경 없음 |
| [App #41](https://github.com/team-onetruck/oneload-app/issues/41) | **미해결**. intent3개·슬롯4개·MessageOut.plan·계획 API 생성 타입 누락 유지 | 현재 Backend OpenAPI로 재생성 후 소비 경계와 App 검사 필요. 새 재검증 댓글 기록 |
| [QA #3](https://github.com/team-onetruck/oneload-qa/issues/3) | **부분 완료**. Q10·근거 열20건 및 공식 검색 로컬 재검사 완료 | 로컬 검색 재검사 완료 체크. **검색 임계값 확정은 미완료**로 open 유지 |
| [개인 skala_git_example #1](https://github.com/mootwo0202/skala_git_example/issues/1) | 본문이 `This is a issue test.`인 연습용 이슈 | 제품 결함·완료 기준이 없어 변경·종료하지 않음 |

Data#2·RAG#3·Agent#7의 동일 버전 기존 검증 댓글은 유지했다. 상태·완료 체크가 바뀐 Infra#1·QA#3과 첫 재검증인 App#41에만 새 댓글을 남겼다. 모두 mootwo0202 작성임을 확인했다. [Infra 종료](https://github.com/team-onetruck/oneload-infra/issues/1#issuecomment-6395183721) · [QA 체크 갱신](https://github.com/team-onetruck/oneload-qa/issues/3#issuecomment-6395184334) · [App 계약 재확인](https://github.com/team-onetruck/oneload-app/issues/41#issuecomment-6395184541).

## 이번 실제 실행과 한계

QA 실행 커밋은 `f23d5f3`이다. App `12ba6c6`, Backend `9067553`, Agent `a732577`, Data `89ec570`, Infra `6cf4a65`, RAG `f99704d`를 확인했으며 상세 SHA·작업 트리 상태는 구조화 증거에 있다. Infra 검증 범위는 문서·메타데이터 비교다. 지도는 `2026-10-25.1`이다.

- QA48/48·Agent47/47·Backend71/71·Data 구조3/3 통과.
- component20/20시나리오·21/21턴 자동 검사 통과. 사람 검토21턴 대기·최종 품질점수null 유지.
- FakeLLM·일회용 DB의 모의검색 API27/27·공식 MemorySearch 주입 API28/28 통과. 구매·출구·탑승의 intent/슬롯 유지 API-20~25와 반납 facts API-26을 다시 확인했다. Backend#2는 해결 상태다.
- 실제 main.py 전역 app을 TestClient에서 조립한 모의 API7/7 통과. 공식 요금 문서·확인일, 빈 검색 거절, 공유 Vision, 키 없는 fallback 연결을 확인했다.
- 경로는5/24 연결이며 동일 위치2건을 포함한다. 나머지19건 실패로 **전체 exit1**이다. 환경·실행기 오류가 아니다.
- 노출 retrieval v2를 공식14문서·MemorySearch0.25/k3/상대0.5로 재실행했다. top1 14/20·top3 17/20·범위밖 빈 결과15/20이다. 정상 누락 H2-07·08·20, 오탐 H2-23·24·25·29·36 유지. 최초 호텔·실시간 좌석 예시는 원문 조건0.35에서도 빈 결과다.
- App schema는 intent6개/슬롯2개로 Backend9개/6개와 다르며 기존 SHA와 동일하다. App 단위513건·빌드는 이번에 재실행하지 않았고 이전 동일 소스 증거를 새 통과로 집계하지 않았다.

기존 baseline·동결 평가셋은 보존하고 이번 재실행을 별도 증거로 추가했다. 실제 모델·임베딩0회, 운영 DB·배포 사용 없음이다. 배포 서버는 꺼진 상태이며 형제 RAG main의 로컬 공식 MemorySearch를 사용했다. 배포용 v0.3.0 설치 조합·pgvector·실제 AI 품질·휴대폰2D/거리뷰·현장 사진 인수는 미검증이다.

## 다음 작업과 재현

Data#2 경로 제약 확인·보완과 App#41 생성 타입 동기화가 우선이다. 반영된 main의 SHA를 고정해 경로·다중 턴 API를 다시 검사한다. RAG#3·Agent#5의 검색/답변 근거·인용 처리는 분리 평가한다. 기존 노출v2를 새 독립 holdout으로 재사용하거나 임계값·정답 기준을 완화하지 않는다. QA#3 임계값은 기준 충족 전까지 승인하지 않는다.

qa 폴더에서 새 출력 경로를 사용한다. 표준 전체 검사의 현재 예상 종료코드는 Data#2 때문에1이다.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENAI_API_KEY= .venv/bin/python scripts/run_checks.py --project-root .. --with-backend --output results/next-issue-check-001
PYTHONDONTWRITEBYTECODE=1 OPENAI_API_KEY= .venv/bin/python scripts/run_backend_tests.py --project-root .. --with-rag --rag-min-score 0.25 --output results/next-issue-rag-001
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/check_routes.py --project-root .. --output results/next-issue-routes-001.json
```

App 비교는 App#41 본문의 DB·모델 없는 재현 명령을 따른다. 노출v2 회귀는 다음처럼 질문·정답·임계값을 고정해 실행한다.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, 'scripts')
from rag_inputs import load_rag
from evaluate_retrieval import score
search, metadata = load_rag(Path('..').resolve(), 0.25)
data = json.loads(Path('eval/retrieval_holdout_v2.json').read_text())
print(json.dumps(score(data['cases'], search), ensure_ascii=False, indent=2))
PY
```
