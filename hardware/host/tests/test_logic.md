# host 로직 시험 목록 (수동 실행 가이드)

Python 실행 환경이 이 작업 세션에서 없어서, 아래 시험은 **실행하지 않았다(미검증)**.
실행 방법: `python -m pytest host/tests` 로 돌릴 수 있도록 pytest 형식 예시를 test_obs_bridge.py에 둔다.

| 시험 | 기대 결과 |
|---|---|
| CommandGate: REC 두 번 0.1 s 간격 | 첫 번째만 허용 |
| CommandGate: rec=STARTING 상태에서 BTN REC | None (무시) |
| CommandGate: rec=RECORDING 에서 BTN REC | StopRecord |
| CommandGate: rec=STOPPED 에서 BTN SCENE | NextScene |
| next_scene: 목록 끝 다음은 처음으로 | 순환 |
| next_scene: 현재 장면이 목록에 없음 | 목록 첫 번째 |
| apply_output_state: STARTED → STOPPING → STOPPED | rec 2 → 3 → 0, 경과 초 0으로 리셋 |
| apply_output_state: PAUSED → RESUMED | 경과 누적 유지 |
| parse_serial_line: "BTN REC", "HELLO 0.1.0" | 각각 명령/HELLO |
| parse_serial_line: 잡음 문자열 | None |
