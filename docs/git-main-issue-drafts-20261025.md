# 현재 Git 조합 이슈 초안 — 미등록

실제 GitHub 이슈·댓글·PR 상태를 변경하지 않았다. [전체 검토](git-main-review-20261025.md) · [구조화 실행 증거](../reports/git-main-review-20261025.json)를 따른다. 다른 역할의 코드는 수정하지 않는다.

## RAG: 현재 Data main과 별칭/위치 카드의 버전 불일치로 전체 테스트2건 실패

확인 조합은 RAG `f99704d`, Data `89ec570`(지도2026-10-25.1), Agent `a732577`, Backend `2ebd94d`다. 실제 RAG 전체 검사는99통과·2실패·skip0이다. MCP6건과 FakeEmbedder pgvector7건은 통과했다.

실패 항목:

- `tests/test_poi.py::test_aliases_match_the_map`: `poi/seoul-station.aliases.yaml`의 map_version2026-10-23.1.
- `tests/test_localization.py::test_cards_and_cases_match_the_map`: `localization/seoul-station.landmarks.yaml`의 map_version2026-10-23.1.

최신 Data main은2026-10-25.1이므로 두 항목 모두 버전 검사에서 실패한다. 범위밖 검색 오탐인 기존 RAG#3과 구분되는 교차 저장소 메타데이터 문제다. 기존 RAG CI의10월23일 성공과 현재 조합의 재실행 실패를 구분한다.

담당자는 매핑의 POI/노드·근거가 실제 현재 지도와 맞는지 확인한 뒤 버전/평가 자료를 갱신하고, 전체 회귀와 주변 저장소 조합을 재검사해야 한다. QA가 숫자만 바꿔 통과시키거나 정답을 자동 교체하지 않았다. Data PR#3을 적용할 계획이라면 그 PR 지도와 main 지도를 별도 버전/해시로 다뤄야 한다.

두 실패는 DB·모델 호출 없이도 재현된다. 아래의 `PROJECT`는 깨끗한 main6개 복사본의 부모이며 현재 QA 폴더에서 실행한다.

```sh
PROJECT="$PWD/results/git-main-review-20261025-001/project"
PYTHONDONTWRITEBYTECODE=1 OPENAI_API_KEY= RAG_REQUIRE_CONTRACT=1 \
RAG_DATA_DIR="$PROJECT/oneload-data" RAG_BACKEND_DIR="$PROJECT/oneload-backend" RAG_AGENT_DIR="$PROJECT/oneload_agent" \
PYTHONPATH="$PROJECT/oneload-rag/src:$PROJECT/oneload-backend:$PROJECT/oneload_agent" \
.venv/bin/python -m pytest -q -p no:cacheprovider \
"$PROJECT/oneload-rag/tests/test_poi.py::test_aliases_match_the_map" \
"$PROJECT/oneload-rag/tests/test_localization.py::test_cards_and_cases_match_the_map"
```

## 기존 이슈에 연결할 현재 근거

| 추적 항목 | 이번 재현·남은 행동 |
|---|---|
| Data#2 | main 경로19/24 실패. PR#3은78/78 연결되지만 미병합. 실제 통행 방향·개찰구·현장 인수는 별도 |
| App#41 / Agent#7 | Backend500/슬롯은 통과. App 생성 intent3개·slot4개·plan/steps 계약 누락 유지 |
| Agent#5 | 공식 문서2개를 고정 주입하고 FakeLLM이[1]만 인용하면 출처는2개 유지. 인용 출처 필터 구현/회귀 필요. 실제 모델 품질 측정 아님 |
| RAG#3 / QA#3 | 노출v2 top3 17/20·범위밖 빈 결과15/20. 임계값/품질 미승인 유지 |
| Data#1 | 원본 POI22/40, 제안 별칭 덧붙임40/40. main에 추가 별칭이 반영됐다고 집계하지 않음 |
| Agent PR#10 | 중복 후보3사례→0 확인. 단위72통과·L05/L06은2xfail. 미병합이므로 main 해결로 표시하지 않음 |

이 항목들은 기존 이슈/PR을 참고하는 기록이며 중복 이슈를 만들지 않았다. DataPR 지도와 최신 Backend 조합에서 무료 구역870쌍의 불필요한 개찰구 통과0건·L24 차단 복구를 확인했다. 이전 로컬e89bc42c 지도에 대한 초안은 과거 입력 조합의 기록으로 보존한다. PR 지도에서는 POI32/40 기대 범위·환승 안내 문구·9-1번 출구 처리·목적지 분류 표시와 담당 역할 간 사본 동기화가 남는다.
