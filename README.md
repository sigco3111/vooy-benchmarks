# Vooy Benchmarks | 부이 벤치마크

Vooy(AI 비서)가 같은 다섯 과제를 직접 구현한 결과와 검증 기록을 모아 둔 저장소입니다.

- 과제 원문: 유튜버 코드팩토리의 메타프롬프트(사용자 제공). [`ORIGINAL_PROMPTS.txt`](ORIGINAL_PROMPTS.txt)에 자리표시자(`{{MODEL_NAME}}`, `{{EFFORT}}`, `{{TASK_DIR}}`)까지 그대로 보존했습니다.
- 세부 모델명과 effort는 지정받지 않았고, 추정해서 쓰지 않았습니다.
- 공식 성능 순위나 통제 실험 점수가 아닙니다. 점수·순위·fps 같은 수치는 측정하지 않은 한 적지 않았습니다.
- 저장소 구조는 sigco3111/instinct-benchmarks의 폴더 구조를 참고했고, 그 저장소의 스크린샷·결과물은 열어 보거나 참고하지 않았습니다.

## 실행 주체와 방식

| 항목 | 내용 |
|---|---|
| 실행 주체 | Vooy (모델명·effort 미지정) |
| 과제 출처 | README 원문 메타프롬프트(ORIGINAL_PROMPTS.txt) |
| 실행 환경 | 파일 읽기·쓰기만 가능한 작업 환경. 브라우저 실행, 컴파일, 3D 출력은 하지 못함 |
| 결과 반영 | 작업 환경에서 쓴 파일을 GitHub 웹 편집기로 옮겨 커밋(크기 대조) |

## 데모 (GitHub Pages)

배포 주소: https://sigco3111.github.io/vooy-benchmarks/

- 과제 1 근정전: https://sigco3111.github.io/vooy-benchmarks/palace.html
- 과제 2 한강시: https://sigco3111.github.io/vooy-benchmarks/hangang-city.html
- 과제 3 소개 페이지: https://sigco3111.github.io/vooy-benchmarks/model-intro.html (원문 지시대로 `{{MODEL_NAME}}` 자리표시자가 그대로 보입니다)
- 과제 5 미리보기(시뮬레이션): https://sigco3111.github.io/vooy-benchmarks/hardware/preview/index.html

네 주소 모두 열리는 것까지만 확인했고, 화면 동작·콘솔 오류·fps는 확인하지 못했습니다.

## 과제별 결과

| # | 과제 | 결과물 | 구현 노트 | 실행 검증 |
|---|---|---|---|---|
| 1 | 근정전 브릭 모션 그래픽 | [palace.html](palace.html) | [palace-NOTES.md](palace-NOTES.md) | 미검증 |
| 2 | 한강시 3인칭 오픈월드 게임 | [hangang-city.html](hangang-city.html) | [hangang-city-NOTES.md](hangang-city-NOTES.md) | 미검증 (정적 검토만) |
| 3 | 모델 소개 스크롤 랜딩 | [model-intro.html](model-intro.html) | [model-intro-NOTES.md](model-intro-NOTES.md) | 미검증 |
| 4 | 을지로 인쇄소 단편 소설 「역상」 | [novel.md](novel.md) | [novel-NOTES.md](novel-NOTES.md) | 글자 수 집계함(공백 포함 11,954자, 약 59.8매) |
| 5 | USB OBS 촬영 데스크 컨트롤러 | [hardware/](hardware/) | [hardware/README.md](hardware/README.md), [hardware/VERIFICATION.md](hardware/VERIFICATION.md) | 설계 문서·소스만. 컴파일·실물·STL 미검증 |

각 과제의 원문 요구 대비 점검표(충족/부분/미흡)는 구현 노트에 있습니다.

## 검증 한계 (솔직한 기록)

- 과제 1~3: HTML 파일을 브라우저로 열어 보지 못했습니다. 문법과 구조는 눈으로 점검했고, 렌더링 결과·콘솔 오류·60fps는 확인하지 않았습니다.
- 과제 1의 브릭 수(3,622)는 같은 배치 로직을 별도로 돌려 얻은 값이며, HTML 안에서 브라우저로 확인한 값이 아닙니다.
- 과제 2: 알려진 한계로 보행자가 차량에 반응하지 않고, 순찰차 경로가 막힐 수 있습니다. 상세는 노트 참고.
- 과제 3: 성능 수치 자리는 모두 `[측정값 대기]`이며 모델명 자리는 `{{MODEL_NAME}}` 그대로입니다.
- 과제 4: 문장 품질은 자체 판단이며 외부 검수는 없습니다. 이 파일은 처음 일부만 올라갔다가 전체 본문으로 교체해 커밋 기록이 두 번 남아 있습니다.
- 과제 5: 펌웨어 컴파일, 호스트 시험 실행, OpenSCAD/STL 생성, 미리보기 실행, 실물 제작 모두 하지 않았습니다. 부품 공식 링크가 빠진 항목은 BOM에 표시했습니다.
- 업로드 대조는 파일 크기(바이트) 일치까지만 확인했고, 글자 단위 대조는 하지 않았습니다.
- 스크린샷은 브라우저 실행이 불가능해 넣지 못했습니다. 실행 가능한 환경에서 확인한 뒤 추가할 예정입니다.

## 크레딧과 라이선스

- 과제 원문: 코드팩토리 메타프롬프트(사용자 제공)
- 참고한 구조: sigco3111/instinct-benchmarks
- 사용 라이브러리(CDN 로드): three.js 0.170.0 (MIT), GSAP 3.12.5·ScrollTrigger (GSAP 표준 라이선스)
- 이 저장소의 결과물에는 외부 이미지·폰트·음원 파일이 없고, 간판·텍스처·형상은 코드로 생성했습니다.
- 저장소에는 아직 별도 라이선스 파일을 두지 않았습니다.
