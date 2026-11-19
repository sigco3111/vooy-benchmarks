# host — 브리지 앱 실행 안내

## 요구
- Python 3.10 이상
- OBS Studio 28 이상 (obs-websocket v5 내장). 설정 > WebSocket 서버 설정에서 "WebSocket 서버 활성화" 체크, 포트 4455.
- 비밀번호를 설정했다면 환경변수로만 전달한다. 파일에 쓰지 않는다.

## 설치
```
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 실행 (macOS/Linux 예)
```
export OBS_WS_PASSWORD='여기에 비밀번호'     # 설정하지 않았다면 생략
export SERIAL_PORT=/dev/ttyACM0            # 생략하면 Pico 또는 VID 2E8A 장치를 찾는다
python obs_bridge.py
```
Windows PowerShell 예:
```
$env:OBS_WS_PASSWORD = "여기에 비밀번호"
$env:SERIAL_PORT = "COM5"
python obs_bridge.py
```

## 동작 요약
- 컨트롤러가 연결되면 1초마다 ST 줄을 보낸다.
- OBS가 꺼져 있으면 obs_ok=0을 보내고, 1 → 2 → 4 → 8 s로 재시도한다.
- 버튼 명령은 400 ms 안의 중복과 STARTING/STOPPING 중 명령을 버린다.

## 한계 (미검증)
- 이 파일은 실행하지 않았다. obsws-python API 이름(`get_record_status`, `start_record` 등)과
  이벤트 객체 속성(`name`, `data`)은 라이브러리 버전에 따라 다를 수 있으므로 실행 전 확인이 필요하다.
- 장면 전환은 OBS 목록을 역순으로 정렬한 뒤 다음 장면을 고른다(OBS 장면 목록 표시 순서 확인 필요).
