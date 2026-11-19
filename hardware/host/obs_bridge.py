#!/usr/bin/env python3
"""USB OBS desk controller - host bridge.

Connects the controller (USB CDC serial) to OBS Studio (obs-websocket v5).

Rules implemented here (see ARCHITECTURE.md section 4-5):
  - Buttons never change state locally. Only OBS events / GetRecordStatus change `rec`.
  - CommandGate: drops duplicate commands within DUP_WINDOW_S and any command while
    OBS reports STARTING / STOPPING.
  - Reconnect with backoff 1, 2, 4, 8 s for both OBS and the serial port.
  - After every (re)connect, the bridge resyncs with GetRecordStatus and GetSceneList
    and sends an ST line at once.
  - Sends "ST <rec> <t_sec> <obs_ok> <scene>" every second (heartbeat).

Credentials: never stored in this file. OBS_WS_PASSWORD env var (optional, empty if OBS has no password).
Other settings: OBS_WS_HOST (default 127.0.0.1), OBS_WS_PORT (default 4455), SERIAL_PORT (default auto-find first
CDC device, or set explicitly e.g. COM5 or /dev/ttyACM0).

Dependencies: pyserial, obsws-python (>=1.7 for the ReqClient/EventClient API used here).
"""
from __future__ import annotations

import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from queue import Empty, Queue
from typing import Callable, Optional

DUP_WINDOW_S = 0.4          # same command within 400 ms is a duplicate
HEARTBEAT_S = 1.0           # ST line period
BACKOFF = (1.0, 2.0, 4.0, 8.0)

# OBS record states (obs-websocket v5 OBS_WEBSOCKET_OUTPUT_*). Mapped to controller rec codes.
REC_STOPPED, REC_STARTING, REC_RECORDING, REC_STOPPING, REC_PAUSED = 0, 1, 2, 3, 4
OUTPUT_STATE_TO_REC = {
    "OBS_WEBSOCKET_OUTPUT_STOPPED": REC_STOPPED,
    "OBS_WEBSOCKET_OUTPUT_STARTING": REC_STARTING,
    "OBS_WEBSOCKET_OUTPUT_STARTED": REC_RECORDING,
    "OBS_WEBSOCKET_OUTPUT_STOPPING": REC_STOPPING,
    "OBS_WEBSOCKET_OUTPUT_PAUSED": REC_PAUSED,
    "OBS_WEBSOCKET_OUTPUT_RESUMED": REC_RECORDING,
}
# RecordStateChanged eventData fields per obs-websocket protocol: outputActive, outputState, outputPath.
EVENT_SUBSCRIPTIONS = (1 << 2) | (1 << 6)   # Scenes | Outputs (values from obs-websocket protocol docs)

log = logging.getLogger("obs_bridge")


class CommandGate:
    """Drops duplicate and out-of-state button commands. Pure logic, unit-tested in tests/."""

    def __init__(self, dup_window_s: float = DUP_WINDOW_S, clock: Callable[[], float] = time.monotonic):
        self.dup_window_s = dup_window_s
        self.clock = clock
        self._last: dict[str, float] = {}

    def allow(self, cmd: str, rec: int) -> Optional[str]:
        """Return the OBS request to send, or None to drop. cmd is 'BTN REC' or 'BTN SCENE'."""
        now = self.clock()
        if rec in (REC_STARTING, REC_STOPPING):
            return None                        # transition in progress: ignore
        last = self._last.get(cmd)
        if last is not None and (now - last) < self.dup_window_s:
            return None                        # duplicate within window
        self._last[cmd] = now
        if cmd == "BTN REC":
            return "StopRecord" if rec in (REC_RECORDING, REC_PAUSED) else "StartRecord"
        if cmd == "BTN SCENE":
            return "NextScene"
        return None


@dataclass
class State:
    rec: int = REC_STOPPED
    rec_started_at: Optional[float] = None     # monotonic time when RECORDING began (for t_sec)
    paused_elapsed: float = 0.0
    obs_ok: bool = False
    scene: str = ""
    scenes: list[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def elapsed(self, now: float) -> int:
        if self.rec == REC_RECORDING and self.rec_started_at is not None:
            return int(self.paused_elapsed + (now - self.rec_started_at))
        if self.rec == REC_PAUSED:
            return int(self.paused_elapsed)
        return 0

    def st_line(self, now: float) -> str:
        with self.lock:
            scene = (self.scene or "-").replace(" ", "_")[:15]
            return f"ST {self.rec} {self.elapsed(now)} {1 if self.obs_ok else 0} {scene}"


def sanitize_scene(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


def ui_order_names(scene_entries: list[dict]) -> list[str]:
    """Scene names in the OBS UI order (top to bottom).

    obs-websocket reports sceneIndex with 0 at the bottom of the list, so the UI order is
    descending sceneIndex. Sorting by sceneIndex avoids depending on the array order."""
    ordered = sorted(scene_entries, key=lambda s: s.get("sceneIndex", 0), reverse=True)
    return [sanitize_scene(s["sceneName"]) for s in ordered]


def next_scene(scenes: list[str], current: str) -> Optional[str]:
    """Next scene in OBS list order, wrapping. None if there are no scenes."""
    if not scenes:
        return None
    try:
        i = scenes.index(current)
    except ValueError:
        return scenes[0]
    return scenes[(i + 1) % len(scenes)]


def apply_record_status(state: State, output_active: bool, output_paused: bool, now: float) -> None:
    with state.lock:
        if output_paused:
            state.rec = REC_PAUSED
        elif output_active:
            state.rec = REC_RECORDING
        else:
            state.rec = REC_STOPPED
            state.rec_started_at = None
            state.paused_elapsed = 0.0
            return
        if state.rec_started_at is None:
            state.rec_started_at = now


def apply_output_state(state: State, output_state: str, now: float) -> None:
    rec = OUTPUT_STATE_TO_REC.get(output_state)
    if rec is None:
        return
    with state.lock:
        if rec == REC_RECORDING and state.rec == REC_PAUSED:
            state.rec = REC_RECORDING                      # resume: keep accumulated time
            state.rec_started_at = now
            return
        if rec == REC_PAUSED and state.rec == REC_RECORDING and state.rec_started_at is not None:
            state.paused_elapsed += now - state.rec_started_at
            state.rec_started_at = None
        if rec in (REC_STARTING, REC_STOPPING):
            state.rec = rec
            return
        if rec == REC_RECORDING and state.rec_started_at is None:
            state.rec_started_at = now
            state.paused_elapsed = 0.0
        if rec == REC_STOPPED:
            state.rec_started_at = None
            state.paused_elapsed = 0.0
        state.rec = rec


def parse_serial_line(line: str) -> Optional[str]:
    """Device -> host lines. Returns the command name or None."""
    line = line.strip()
    if line in ("BTN REC", "BTN SCENE"):
        return line
    if line.startswith("HELLO "):
        return "HELLO"
    return None


class Bridge:
    def __init__(self, obs_host: str, obs_port: int, obs_password: str, serial_port: Optional[str]):
        self.obs_host = obs_host
        self.obs_port = obs_port
        self.obs_password = obs_password
        self.serial_port = serial_port
        self.state = State()
        self.gate = CommandGate()
        self.cmd_q: "Queue[str]" = Queue()
        self.stop = threading.Event()
        self.ser = None
        self.obs = None
        self.events = None

    # ---- OBS side -------------------------------------------------------
    def _connect_obs(self) -> None:
        import obsws_python as obsws  # imported here so the file can be read without the package

        self.events = obsws.EventClient(host=self.obs_host, port=self.obs_port,
                                        password=self.obs_password, timeout=5,
                                        subs=EVENT_SUBSCRIPTIONS)
        self.obs = obsws.ReqClient(host=self.obs_host, port=self.obs_port,
                                   password=self.obs_password, timeout=5)
        self.events.callback.register(self._on_event)
        self.resync()

    def resync(self) -> None:
        now = time.monotonic()
        st = self.obs.get_record_status()
        apply_record_status(self.state, bool(st.output_active), bool(st.output_paused), now)
        scenes = self.obs.get_scene_list()
        with self.state.lock:
            self.state.scenes = ui_order_names(scenes.scenes)
            self.state.scene = sanitize_scene(scenes.current_program_scene_name)
            self.state.obs_ok = True

    def _on_event(self, event) -> None:
        name = getattr(event, "name", None) or getattr(event, "event_type", "")
        data = getattr(event, "data", None) or getattr(event, "event_data", {}) or {}
        now = time.monotonic()
        if name == "RecordStateChanged":
            apply_output_state(self.state, data.get("outputState", ""), now)
        elif name == "CurrentProgramSceneChanged":
            with self.state.lock:
                self.state.scene = sanitize_scene(data.get("sceneName", self.state.scene))
        elif name == "SceneListChanged":
            with self.state.lock:
                self.state.scenes = ui_order_names(data.get("scenes", []))

    def _run_obs_command(self, req: str) -> None:
        try:
            if req == "StartRecord":
                self.obs.start_record()
            elif req == "StopRecord":
                self.obs.stop_record()
            elif req == "NextScene":
                with self.state.lock:
                    target = next_scene(self.state.scenes, self.state.scene)
                if target:
                    self.obs.set_current_program_scene(target)
        except Exception as exc:  # noqa: BLE001 - report and keep running
            log.warning("OBS request %s failed: %s", req, exc)

    def _obs_loop(self) -> None:
        backoff_i = 0
        while not self.stop.is_set():
            try:
                if self.obs is None:
                    self._connect_obs()
                backoff_i = 0
                last_ping = time.monotonic()
                while not self.stop.is_set():
                    try:
                        cmd = self.cmd_q.get(timeout=0.2)
                    except Empty:
                        # Idle: a cheap request detects a dropped OBS connection (raises -> reconnect).
                        if time.monotonic() - last_ping >= 2.0:
                            self.obs.get_version()
                            last_ping = time.monotonic()
                        continue
                    with self.state.lock:
                        rec = self.state.rec
                    req = self.gate.allow(cmd, rec)
                    if req:
                        self._run_obs_command(req)
            except Exception as exc:  # noqa: BLE001
                with self.state.lock:
                    self.state.obs_ok = False
                    self.state.rec = REC_STOPPED
                    self.state.rec_started_at = None
                    self.state.paused_elapsed = 0.0
                self._drop_obs()
                delay = BACKOFF[min(backoff_i, len(BACKOFF) - 1)]
                backoff_i += 1
                log.warning("OBS not available (%s); retry in %.0fs", exc, delay)
                self.stop.wait(delay)

    def _drop_obs(self) -> None:
        for c in (self.events, self.obs):
            try:
                if c is not None:
                    c.disconnect()
            except Exception:  # noqa: BLE001
                pass
        self.events = None
        self.obs = None

    # ---- serial side ----------------------------------------------------
    def _open_serial(self):
        import serial
        from serial.tools import list_ports

        port = self.serial_port
        if not port:
            cands = [p.device for p in list_ports.comports() if "Pico" in (p.description or "") or
                     (p.vid == 0x2E8A)]
            if not cands:
                raise OSError("controller not found; set SERIAL_PORT")
            port = cands[0]
        return serial.Serial(port, 115200, timeout=0.2, write_timeout=1)

    def _serial_loop(self) -> None:
        backoff_i = 0
        while not self.stop.is_set():
            try:
                if self.ser is None:
                    self.ser = self._open_serial()
                    log.info("serial open: %s", self.ser.port)
                backoff_i = 0
                last_hb = 0.0
                while not self.stop.is_set():
                    raw = self.ser.readline()
                    if raw:
                        msg = parse_serial_line(raw.decode("ascii", "replace"))
                        if msg == "BTN REC" or msg == "BTN SCENE":
                            self.cmd_q.put(msg)
                    now = time.monotonic()
                    if now - last_hb >= HEARTBEAT_S:
                        self.ser.write((self.state.st_line(now) + "\n").encode("ascii"))
                        last_hb = now
            except Exception as exc:  # noqa: BLE001
                log.warning("serial error (%s); reconnect", exc)
                try:
                    if self.ser is not None:
                        self.ser.close()
                except Exception:  # noqa: BLE001
                    pass
                self.ser = None
                delay = BACKOFF[min(backoff_i, len(BACKOFF) - 1)]
                backoff_i += 1
                self.stop.wait(delay)

    def run(self) -> None:
        t1 = threading.Thread(target=self._obs_loop, name="obs", daemon=True)
        t2 = threading.Thread(target=self._serial_loop, name="serial", daemon=True)
        t1.start()
        t2.start()
        try:
            while t1.is_alive() and t2.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop.set()
            self._drop_obs()


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(message)s")
    bridge = Bridge(
        obs_host=os.environ.get("OBS_WS_HOST", "127.0.0.1"),
        obs_port=int(os.environ.get("OBS_WS_PORT", "4455")),
        obs_password=os.environ.get("OBS_WS_PASSWORD", ""),
        serial_port=os.environ.get("SERIAL_PORT") or None,
    )
    bridge.run()


if __name__ == "__main__":
    main()
