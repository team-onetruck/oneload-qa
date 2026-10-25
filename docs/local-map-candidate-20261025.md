# 미커밋 서울역 지도 후보 테스트 — 2026-10-25

사용자가 보존을 요청한 Data 로컬 브랜치 `map/line14-expansion-20261025`를 **읽기만 하여** 검사했다. 기반 HEAD는 `89ec570`이지만 변경 내용은 커밋에 들어 있지 않다. 실제 검증 입력은 지도 `2026-10-25.2`, SHA256 `e89bc42c287f9db1e9d61a968ac3b9dc567688d68cfe05e92e3185de54d6aedc`와 구조화 증거의 파일별 해시로 식별한다.

[구조화 증거](../reports/local-map-candidate-20261025.json) · [다른 역할에 전달할 이슈 초안](local-map-candidate-issue-drafts-20261025.md) · [인수인계](handoff.md)

Data와 나머지 개발 저장소의 코드·브랜치·작업 트리는 변경하지 않았다. 사용자 원본7개 저장소의 비무시 파일 전체 해시·HEAD·브랜치·상태가 검사 전후 같다. 실제 GitHub 이슈·댓글·상태도 변경하지 않았다. 이 작업의 공유 대상은 QA 문서와 검증 증거뿐이며 Data 커밋·push·병합은 하지 않는다.

## 실제 결과

| 검사 | 결과와 범위 |
|---|---|
| Data 생성 일치 `build_map.py --check`·스키마/참조 `validate.py` | 모두 통과. 생성 결과 재현도 일치 |
| 빌드 검사 음성 대조군 | 중복 노드·중복 일반 간선·노드 단절·휠체어 단절·오래된 JSON의5가지 잘못된 입력 모두 검출 |
| 구조 비교 | 노드12→39, 간선12→102, **POI6→40**, landmark20→40, 파노라마6개 동일. 기존 노드/POI/landmark/파노라마 ID 삭제0 |
| 기본 QA 실행 | QA48/48·Agent47/47·Backend71/71·Data구조3/3·component20시나리오/21턴 통과, **전체 exit0** |
| 새 지도 API | 모의검색27/27·공식 MemorySearch주입28/28·실제 전역app모의API7/7 통과 |
| 출구·반납기 경로 | 새 지도78/78 연결. 기존 main은5/24 연결·19건 실패로 별도 유지 |
| 실제 Backend 전체 노드 경로 | 39×39=1,521/1,521 연결, 동일 위치 포함 |
| 지정 휠체어9개 지점 | 81/81 연결, 반환 경로에 계단·에스컬레이터0. 전체 노드 쌍은641/1,521이며 나머지 모든 출구의 접근성을 보장하지 않음 |
| Agent CI 계약 검사 | **exit1**, `mocks/maps`와 후보 지도 불일치. 사본은 수정하지 않음 |
| 새 목적지 목록 선택 API | 40/40 통과 |
| 출구16개×한국어/영어 자연어 API | **30/32**. FakeLLM에서9-1번이 한국어1번·영어9번으로 선택됨 |
| R3 POI 고정40문항 | 후보32/40. 기존 main은 원본 별칭22/40·R3 별칭 추가40/40, 후보는 R3 추가 후에도32/40 |
| R3 합성 위치24문항의 현재 지도 매처 | 양성 top1/top3 13/20 유지, 범위밖 차단 **4/4→3/4**. L24 회귀 |
| 생성 SVG | XML 유효·기존 미리보기와 재생성 결과 일치. 현장 도면 검증은 아님 |

Agent·Backend 단위 검사는 고정 fixture 지도를 사용한다. 새 지도 호환은 별도의 현재 지도 API/경로 검사로 확인했다. component 사람 검토21턴·최종 품질점수null은 그대로다. 기존 baseline·질문·정답·임계값은 변경하지 않았다.

## 확인한 미완료·검토 사항

1. **Agent 사본 동기화:** Data를 나중에 반영하더라도 현재 Agent의 CI 호환 검사는 실패한다. 단위47개 통과로 이 실패를 대체하지 않는다.
2. **합성 위치 L24:** `시청역`, `City Hall`을 넣으면 기존에는 빈 후보, 새 지도에서는 `line1-platform`을 반환한다. 새 방향 표지 `City Hall`이 다른 역 이름과 겹친다. 실제 사진 정확도를 측정한 결과는 아니며 고정된 합성 음성 사례의 회귀다.
3. **9-1번 출구:** 목록으로 직접 선택하면 정상이다. FakeLLM 자연어에서는 한국어1번·영어9번으로 잘못 선택됨을 HTTP API까지 재현했다. 실제 모델이 같은 오류를 낸다고 판정하지 않는다.
4. **무료 구역 경로:** KTX맞이방→반납기 경로가 무료 구역에서 출발·도착하면서 `line1-gates-east → line1-concourse → line1-gates`로 유료 개찰구에 들어갔다 나온다. 해당 두 지점의 무료 구역만으로 이뤄진 경로는 없다. 실제 통행 가능 여부·무료 연결·카드/개찰구 제약을 담당자가 확인해야 한다. 실제 요금 부과를 측정한 것은 아니다.
5. **환승 중 표 구매 문구:** 직통 승강장→4호선 승강장8단계 경로와 실제 로컬 화면에서 “일반열차 표는 한 층 더 내려가 B3에서 사요.”가 나타난다. 사용자 요청이 표 구매가 아닌 환승인 경우의 안내를 분리할 필요가 있다.
6. **R3 POI 기대값:** 불일치8건 중5건은 기존 정답이 빈 목록인데 새 POI가 추가된 사례이고,3건은 환급기2문항·ticket machine1문항에서 후보가 늘어난 사례다. 전부 오답으로 단정하거나 정답을 자동 교체하지 않는다. 범위 확대와 복수 후보 확인 동작을 R3와 검토해야 한다. 사전/특징 카드의 지도 버전 불일치는 기존 main에서도 발생하던 항목이다.
7. **목적지 분류 표시:** 새 목록에서 `metro_platform`, `metro_tickets`, `help`, `transfer` 같은 내부 분류 키가 그대로 보인다. 기존에도 일부 유형에 있던 표시 문제의 노출 범위가 늘었다.

위 항목은 [이슈 초안](local-map-candidate-issue-drafts-20261025.md)으로만 남겼다. 다른 역할의 코드·평가 기대값은 수정하지 않았다. 기본 QA exit0과 별개로 **이 후보의 전체 인수·반영 승인은 보류**한다. main의 Data#2는 open 상태이며 후보 검증을 main 해결·병합·배포로 옮겨 적지 않는다.

## 로컬 화면·환경

기존 사용자의8000·5173 서버와 `hangil-newmap-pg`를 유지했다. QA가 별도18961·18962 포트와 새 일회용 DB로 FakeLLM·공식 로컬 MemorySearch 서버를 만들어 검사한 뒤 모두 정리했다. jsonschema4.26.0은 QA의 무시된 가상환경에만 추가했고 pip check는 통과했다.

브라우저에서 목적지40개·수동 위치39개를 표시하고 직통 승강장→4호선 경로8단계/468m, 다음 단계 이동, 사진 없는 구간의 안내를 확인했다. [경로 화면](../reports/local-map-candidate-20261025/browser-route.png) · [사진 없음 처리](../reports/local-map-candidate-20261025/browser-streetview.png) · [예시 거리뷰 로딩](../reports/local-map-candidate-20261025/browser-example-pano.png).

예시 파노라마 파일은HTTP200이고 “예시 사진·서울역 아님”을 표시했지만, 이번 브라우저에서는 `Loading...`이 남아 **파노라마 렌더 완료는 미확인(PARTIAL)**이다. 지도 변경에 따른 신규 결함으로 단정하지 않는다. 물리 휴대폰·카메라·센서·실제 AI·실제 현장 사진·OSM 위치 정확도·유료구역/접근성의 현장 검증은 하지 않았다. 실제 모델/임베딩0회, 운영 DB·배포 사용 없음이다.

## 재현

현재 QA checkout에서 `PROJECT`를 사용자의7개 원본 저장소 부모 폴더로 지정한다. Data 작업 트리의 위 해시가 같아야 같은 후보 검사다. 새 출력 경로를 사용하며 **dirty 후보를 검사할 때 `--reports reports`로 main baseline을 덮어쓰지 않는다.**

```sh
QA_PYTHON="$PWD/.venv/bin/python"
PROJECT=/absolute/path/to/mp_project
PYTHONDONTWRITEBYTECODE=1 "$QA_PYTHON" "$PROJECT/oneload-data/tools/build_map.py" --check
PYTHONDONTWRITEBYTECODE=1 "$QA_PYTHON" "$PROJECT/oneload-data/tools/validate.py"
PYTHONDONTWRITEBYTECODE=1 OPENAI_API_KEY= "$QA_PYTHON" scripts/run_checks.py --project-root "$PROJECT" --with-backend --output results/next-candidate-full-001
PYTHONDONTWRITEBYTECODE=1 OPENAI_API_KEY= "$QA_PYTHON" scripts/run_backend_tests.py --project-root "$PROJECT" --with-rag --rag-min-score 0.25 --output results/next-candidate-rag-001
```

`build_map.py`의 쓰기 모드·OSM 가져오기·Data/Agent 사본 교체·기존 DB를 향한 raw Backend pytest는 실행하지 않는다. 다음 수정은 해당 역할에 위 초안을 전달해 진행하고, 반영된 버전에서 같은 검사를 다시 수행한다.
