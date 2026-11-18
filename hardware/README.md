# USB OBS 촬영 데스크 컨트롤러 — 프로토타입 (hardware/)

설계 파일과 소스 일체. 실물 제작·테스트는 아직 하지 않았다. 검증 상태는 VERIFICATION.md 참조.

## 폴더
| 경로 | 내용 |
|---|---|
| REQUIREMENTS.md | 요구사항과 판정 기준 |
| ARCHITECTURE.md | 부품 선택, 통신 구조, 상태 동기화 규칙 |
| BOM.csv | 부품 목록과 공식 출처 링크 |
| WIRING.md | 핀 연결 배선표 |
| POWER_BUDGET.md | 전원 예산과 USB 전류 요구 |
| diagrams/wiring.svg | 핀 연결 배선도 (전기 CAD 아님) |
| firmware/ | Pico 2 펌웨어 소스와 CMake 설정 |
| host/ | OBS 연결 브리지 앱(Python), 시험, 실행 안내 |
| enclosure/ | OpenSCAD 케이스 원본과 치수 문서 (STL은 미생성) |
| preview/index.html | 로컬 미리보기 (시뮬레이션) |
| VERIFICATION.md | 실행한 검증과 한계, 실물 인수 테스트 목록 |

## 1. 조립 절차 (프로토타입, 미검증)
1. Pico 2 헤더 납땜 또는 소켓 장착 (BOM의 H1). 무선 모델 Pico 2 W는 사용하지 않는다.
2. OLED를 4개 M2 스탠드오프 위에 고정한다. 주소 점퍼 기본 0x3C.
3. 키패드 기판(SW1, SW2, D1, R1)을 만든다. 저항 R1은 LED 애노드 쪽이다.
4. WIRING.md 표대로 배선한다. 특히 3V3(pin 36)과 GND(pin 38), GP4/GP5(I2C), GP13/14(버튼), GP15(LED).
5. 키패드 기판을 2개 스탠드오프 위에 올린다.
6. enclosure/case.scad에서 `part="tray"`, `part="lid"`를 STL로 출력한다(미검증 절차).
7. 트레이에 Pico, OLED, 키패드를 넣고 상판을 M2.5 2개로 고정한다.

## 2. 펌웨어 빌드와 플래시
```
export PICO_SDK_PATH=/path/to/pico-sdk        # tag 2.2.0 (pico_sdk_version.txt)
cd firmware
cmake -S . -B build -DPICO_BOARD=pico2
cmake --build build -j
```
결과물: `build/usb_obs_controller.uf2`.
플래시: BOOTSEL 버튼을 누른 채 USB 연결 → 드라이브로 나타나면 UF2 파일을 복사.

> 이 세션에서는 컴파일하지 않았다(미검증). 컴파일 오류가 나면 VERIFICATION.md의 "미검증" 목록을 먼저 본다.

## 3. 호스트 브리지 실행
host/README.md 참조. 요약:
```
cd host
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
OBS_WS_PASSWORD='...' python obs_bridge.py      # 비밀번호는 환경변수로만
```
인증정보는 파일에 넣지 않는다.

## 4. 케이스 출력
```
openscad -D 'part="tray"' -o tray.stl enclosure/case.scad
openscad -D 'part="lid"'  -o lid.stl  enclosure/case.scad
```
치수 가정과 미해결 항목은 enclosure/DIMENSIONS.md 참조. 출력 전 실제 Pico 2와 OLED를 대고 맞춤 확인한다.

## 5. 미리보기
`preview/index.html`을 브라우저로 연다. 외부 라이브러리 없이 동작한다. 시뮬레이션이다(실제 OBS나 USB 통신 없음).

## 6. 주의
- OBS WebSocket 비밀번호는 OBS 설정에서 확인하고 환경변수로만 전달한다.
- VSYS나 외부 5 V를 Pico에 동시에 연결하지 않는다.
- 키패드 기판과 Pico가 가까워 납땜 쇼트 주의.
