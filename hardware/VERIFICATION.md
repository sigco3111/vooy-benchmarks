# VERIFICATION — 실행한 검증, 로그, 한계, 실물 인수 테스트

이 문서는 실제로 실행한 것과 실행하지 못한 것을 구분한다. 실물 제작이나 테스트는 하지 않았다.

## A. 이 세션에서 실제로 실행한 검증

| # | 검증 | 도구 | 결과 | 로그/근거 |
|---|---|---|---|---|
| A1 | 파이코 2 데이터시트/핀맵 확인 | web_search, web_fetch | 부분 확인. pip-assets 데이터시트 검색 요약에서 51×21 mm, Ø2.1 홀, 3V3_EN/VSYS/VBUS 역할 확인. 원문 PDF 전문은 도구로 열람 실패 | 검색 결과 요약 |
| A2 | Pico SDK pico2 보드 기본 핀 | web_search | I2C0 SDA=GP4, SCL=GP5; UART0 TX=GP0, RX=GP1; LED=GP25 (pico2.h 요약) | github pico-sdk pico2.h 요약 |
| A3 | Pico SDK 최신 태그 | web_search | 2.2.0 (2025-07-29) 확인, 2.3.1 존재 확인 | GitHub releases 요약 |
| A4 | Adafruit 938 OLED 사양 | web_fetch | SSD1306, 128×64, 3.3 V, I2C 0x3C/0x3D, PCB 35.6×33×6.2, 홀 30.5×28 Ø2.5, 전류 약 40 mA(최대) | adafruit.com/product/938 요약 |
| A5 | obs-websocket 이벤트·요청 이름 | web_search | RecordStateChanged(outputActive, outputState, outputPath), GetRecordStatus(outputActive, outputPaused, outputTimecode, outputDuration), StartRecord, StopRecord(outputPath), Hello/Identify rpcVersion, eventSubscriptions 비트: Scenes 1<<2, Outputs 1<<6 | 커뮤니티 문서·DeepWiki 요약. 공식 protocol.md 원문은 fetch 결과가 잘려 직접 확인 못 함 |
| A6 | 케이스 배치 간섭 계산 | codemode (JS 계산) | 기판 위치, 간섭 항목 전부 통과 (DIMENSIONS.md 8절) | codemode 출력 `checks` 15개 모두 true |
| A7 | 미리보기 상태 로직 시험 (펌웨어 규칙을 JS로 옮긴 것) | codemode | REC 시작 6 s 시점 REC 2 경과 6 s, 장면 전환, 정지, 3 s 무응답 NO LINK, 재연결 등 7개 기대값 모두 통과 | codemode 출력 `checks` 7개 true (시뮬레이션 로직의 시험이며 펌웨어 실행이 아님) |
| A8 | 글꼴 테이블 생성 검증 | codemode | 글리프 64개, 모든 행 7줄 5열 형식 일치 | `bad=[]`, 줄 수 64 |

## B. 실행하지 않음 — 미검증 (도구 없음 또는 범위 밖)

| # | 항목 | 이유 | 상태 |
|---|---|---|---|
| B1 | firmware C 컴파일 (arm-none-eabi-gcc, pico-sdk 2.2.0) | 이 세션에 C 컴파일러·SDK 실행 도구 없음 | **미검증** |
| B2 | host/obs_bridge.py 단위 시험 (pytest) | Python 실행 도구 없음 | **미검증** |
| B3 | obsws-python API 이름 호환 (get_record_status, start_record, EventClient 콜백 속성 name/data) | 라이브러리 설치와 OBS 연결 불가 | **미검증** |
| B4 | OpenSCAD 렌더링, STL 생성, CGAL 간섭 검사 | OpenSCAD 실행 도구 없음 | **미검증** |
| B5 | preview/index.html 브라우저 동작, 1920×1080 캡처 | 브라우저 실행 도구 없음. JS 구문은 실행 전 미확인 | **미검증** |
| B6 | Pico 2 공식 STEP 파일로 홀 간격 확인 | 공식 STEP 다운로드 불가(검색 요약만 확인) | **미검증** |
| B7 | 키 스위치, LED, 저항 데이터시트 | 구매 제품 미정, 데이터시트 URL 미확보 | **미검증** |
| B8 | USB bMaxPower 설정과 전류 실측 | 실물 없음 | **미검증** |
| B9 | 실물 맞춤, 나사 체결, 버튼 촉감 | 실물 없음 | **미검증** |

## C. 설계 판단 결과 요약
- 보드: Raspberry Pi Pico 2 (non-W). 무선 없음.
- 디스플레이: Adafruit 938 OLED 128×64 SSD1306, I2C.
- 통신: USB CDC 줄 단위 텍스트 + Python 브리지 → obs-websocket v5.
- 표시 상태는 OBS 보고 기준. 버튼만으로 상태를 바꾸지 않는다.
- 펌웨어 3 s 무응답 NO LINK, 명령 PEND 3 s 시간 초과.

## D. 알려진 설계 결함과 미해결 (정직하게 기록)
1. 케이스 상판 고정 보스는 오른쪽 2곳뿐이다. 왼쪽은 Pico 배치 때문에 자리가 없다(DIMENSIONS.md 6절).
2. OLED 마운팅 홀은 PCB 가장자리에서 약 1.3 mm 떨어진다(홀 간격 [S] 값 기준). 실물 확인 필요. (이전 판의 "0.05 mm" 기록은 계산 오류로 정정)
3. firmware에서 `hello_sent_once` 변수가 실질적으로 쓰이지 않는다(경고 가능성). 컴파일 후 정리.
4. host의 `OUTPUT_STATE` 매핑은 OBS_WEBSOCKET_OUTPUT_* 이름을 가정한다. 실제 이벤트 문자열은 실행 시 확인 필요.
5. obs_bridge.py의 `ui_order_names`는 sceneIndex 0이 목록 아래쪽이라는 가정에 의존한다(B3과 함께 확인).
6. 장면 전환은 `NextScene` 가상 요청으로 표기되어 있으며 실제로는 `_run_obs_command`에서 `set_current_program_scene`을 호출한다.
7. preview의 `ledOn` 등 로직은 펌웨어와 같은 규칙이지만 완전히 같은 코드는 아니다.
8. BOM의 스위치, LED, 저항, 나사류는 공식 출처 URL이 없다(미확인으로 표기).
9. 전원 예산은 추정치다. 최악 추정 약 95 mA로 목표 200 mA 아래이지만 실측 전까지 미검증이다.

## E. 실제 기기 인수 테스트 목록 (실물 제작 후)
1. 부품 수령 확인: BOM과 실물 규격(스위치 높이, LED 색, OLED 주소 점퍼) 대조.
2. 저항 측정: 3V3–GND, VBUS–GND 단락이 없는지 확인.
3. 플래시: BOOTSEL로 UF2 복사, 부팅 후 OLED에 "NO LINK" 표시.
4. 전류: USB 파워미터로 부팅 직후, 녹화 중, 전체 점등 상태 측정(POWER_BUDGET.md 5절). 150 mA 초과 시 재검토.
5. 버튼: REC와 SCENE 각각 누름 시 시리얼 로그에 `BTN REC`, `BTN SCENE`이 한 번씩 나오는지 확인(디바운스 20 ms, 잠금 250 ms).
6. 연타: 0.3 s 간격 연타 시 한 번만 전송되는지(잠금과 PEND 동작).
7. OBS 연결: 호스트 실행 후 OBS를 켜면 1, 2, 4, 8 s 백오프로 재시도하고 연결 후 화면이 OK로 바뀌는지.
8. 녹화 동기화: OBS 단축키로 녹화를 시작/정지해도 LED와 화면 시간이 OBS 상태를 따라가는지.
9. 장면 전환: SCENE 버튼 한 번에 OBS 장면 목록의 다음 장면으로 바뀌고 화면 장면 이름이 갱신되는지.
10. 링크 단절: 호스트 종료 시 3 s 안에 NO LINK로 바뀌고 LED가 1 Hz로 깜빡이는지.
11. 재연결: 호스트 재실행 후 ST 수신으로 화면이 정상 상태로 돌아오는지.
12. OBS 비밀번호: 잘못된 비밀번호일 때 호스트 로그에 실패가 남고 파일에 비밀번호가 없는지.
13. 케이스: 트레이 출력 후 Pico, OLED, 키패드 맞춤과 USB 플러그 삽입, 상판 체결.
14. 버튼 캡 작동과 LED 위치, OLED 창에 글자가 잘리지 않는지.
15. 미리보기와 실물 비교: 미리보기 시간 슬라이더의 상태와 실제 장치 상태가 같은 순서인지.
