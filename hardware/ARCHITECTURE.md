# ARCHITECTURE — 구성과 통신 구조

## 1. 선택 결과 요약 [확정]
| 항목 | 선택 | 이유 |
|---|---|---|
| 개발보드 | Raspberry Pi Pico 2 (RP2350, 무선 없음) | 제조사 공식 문서 있음, 40핀 2.54 mm, micro-USB, Pico SDK 공식 보드 설정 `pico2` 존재 |
| 디스플레이 | Adafruit 938 Monochrome 1.3" 128×64 OLED (SSD1306, I2C) | 제조사 제품 페이지에 SSD1306, 128×64, 3.3 V, I2C 주소 0x3C/0x3D 명시 |
| 스위치 | 6×6 mm THT 택트 스위치 2개 | 일반 부품, 데이터시트 출처는 BOM에 미확인으로 표기 |
| 표시등 | 5 mm 빨간 LED 1개 + 330 Ω 저항 | 촬영 중 빨간 표시 요구 |
| PC 통신 | USB CDC(가상 COM 포트), 줄 단위 텍스트 프로토콜 | 드라이버 없이 동작(Windows/macOS/Linux 기본 지원), 디버깅 쉬움 |
| OBS 제어 | 호스트 PC 브리지 앱(Python) → obs-websocket v5 (ws://127.0.0.1:4455) | OBS 공식 원격 제어 프로토콜, 녹화 상태 이벤트 제공 |

## 2. 블록 구조
```
[책상 컨트롤러]                          [촬영 PC]
 Pico 2 (펌웨어 firmware/)                host/obs_bridge.py
  ├ GP14 ← REC 버튼                         ├ USB CDC 시리얼 (pyserial)
  ├ GP13 ← SCENE 버튼                       │   ↑ BTN REC / BTN SCENE
  ├ GP15 → 330Ω → 빨간 LED                  │   ↓ ST <rec> <t> <obs> <scene>
  ├ GP4/GP5 (I2C0) → OLED 128×64            └ obs-websocket v5 (obsws-python)
  └ USB CDC ───────────────────────────────────→ OBS Studio (녹화/장면)
```

## 3. 줄 단위 프로토콜 (USB CDC, 115200 표기이나 CDC는 실제 속도 무관)
장치 → 호스트:
- `HELLO <fw_version>` : 부팅 후 2초마다, 호스트 ST 수신 전까지 반복.
- `BTN REC` : REC 버튼이 디바운스 후 한 번 눌렸을 때 1회.
- `BTN SCENE` : SCENE 버튼이 디바운스 후 한 번 눌렸을 때 1회.

호스트 → 장치:
- `ST <rec> <t_sec> <obs_ok> <scene>` : 1초마다 (하트비트 겸 상태).
  - `rec`: 0 STOPPED, 1 STARTING, 2 RECORDING, 3 STOPPING, 4 PAUSED
  - `t_sec`: 녹화 경과 초(정수). 녹화 중이 아니면 0.
  - `obs_ok`: 1 = OBS 연결 및 응답 정상, 0 = OBS 연결 없음
  - `scene`: 현재 프로그램 장면 이름. 공백은 `_`, 최대 15자.

## 4. 상태 동기화 규칙 [확정]
1. 버튼은 상태를 직접 바꾸지 않는다. 장치는 `BTN …`만 보낸다.
2. 호스트는 OBS의 `RecordStateChanged` 이벤트와 `GetRecordStatus` 응답으로만 rec를 갱신한다.
3. 장치는 rec 값이 바뀔 때까지 PEND 표시. 3 s 안에 바뀌지 않으면 화면에 TIMEOUT 표시 후 실제 상태 유지.
4. 호스트 ST가 3 s 없으면 장치는 화면에 NO LINK를 표시하고 LED는 1 Hz 점멸(알 수 없음 표시).
5. `obs_ok = 0`이면 장치는 화면에 NO OBS, 버튼을 누르면 NO OBS 짧게 표시하고 명령은 호스트에서 무시한다.

## 5. 호스트 브리지 처리 규칙 [확정]
- 연결/재연결: OBS 연결 실패 시 백오프 1→2→4→8 s. 시리얼 포트 끊김도 같은 방식.
- 디바운스/중복: `CommandGate`가 같은 버튼 명령을 400 ms 안에 두 번 받으면 두 번째를 버린다. rec가 STARTING/STOPPING이면 명령을 버린다.
- 재연결 후: `GetRecordStatus`, `GetSceneList`로 장치에 즉시 ST를 보낸다.
- 이벤트 구독: `EventSubscription.Outputs | EventSubscription.Scenes` (값 (1<<6)|(1<<2) = 68). 공식 protocol.md의 비트 값 확인됨(웹 요약 기준).
- 인증: OBS 설정 비밀번호는 환경변수 `OBS_WS_PASSWORD`로만 전달. 파일에 쓰지 않는다.

## 6. 펌웨어 구조
- `main.c`: 메인 루프, 버튼 디바운스, 시리얼 라인 파싱, LED 상태기계, 화면 갱신.
- `oled.c/h`: SSD1306 최소 드라이버(I2C0, 0x3C 기본, 페이지 쓰기, 5×7 폰트 확대).
- `font5x7.h`: 화면에 쓰는 글자만 담은 5×7 비트맵.
- `config.h`: 핀 번호, 타이밍 상수, 펌웨어 버전.

## 7. 상태 기계 요약
| rec | 화면 | LED |
|---|---|---|
| 0 STOPPED | IDLE | 꺼짐 |
| 1 STARTING | PEND/REC… | 5 Hz 점멸 |
| 2 RECORDING | LIVE + 시간 | 켜짐 |
| 3 STOPPING | PEND/STOP… | 5 Hz 점멸 |
| 4 PAUSED | PAUSE + 시간 | 1 Hz 점멸 |
| 링크 없음 | NO LINK | 1 Hz 점멸 |

## 8. 기계 구조 연결
- 케이스 상판: OLED 창, 버튼 캡 구멍 2개, LED 구멍 1개.
- 바닥 트레이: Pico 2 스탠드오프 4개, OLED 스탠드오프 4개, 키패드 기판 스탠드오프 2개, USB 개구부 1개.
- 세부 치수는 enclosure/case.scad와 enclosure/DIMENSIONS.md 참조.

## 9. 범위 밖 (의도적으로 제외)
- 무선/Wi-Fi/블루투스, 배터리 충전, 상용 AC 전원.
- OBS 원격 장치 다중 연결, 스트리밍 제어(녹화만 제어).
