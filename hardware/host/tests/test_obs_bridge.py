"""Unit tests for pure logic in host/obs_bridge.py.

Run:  cd host && python -m pytest tests -q
Status: NOT EXECUTED in the authoring session (no Python runtime was available). See VERIFICATION.md.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import obs_bridge as ob  # noqa: E402


class FakeClock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def test_gate_drops_duplicate_within_window():
    clk = FakeClock()
    g = ob.CommandGate(dup_window_s=0.4, clock=clk)
    assert g.allow("BTN REC", ob.REC_STOPPED) == "StartRecord"
    clk.t += 0.1
    assert g.allow("BTN REC", ob.REC_STOPPED) is None


def test_gate_allows_after_window():
    clk = FakeClock()
    g = ob.CommandGate(dup_window_s=0.4, clock=clk)
    assert g.allow("BTN REC", ob.REC_STOPPED) == "StartRecord"
    clk.t += 0.5
    assert g.allow("BTN REC", ob.REC_RECORDING) == "StopRecord"


def test_gate_ignores_during_transition():
    g = ob.CommandGate(clock=FakeClock())
    assert g.allow("BTN REC", ob.REC_STARTING) is None
    assert g.allow("BTN REC", ob.REC_STOPPING) is None


def test_gate_paused_counts_as_recording_for_stop():
    clk = FakeClock()
    g = ob.CommandGate(clock=clk)
    assert g.allow("BTN REC", ob.REC_PAUSED) == "StopRecord"


def test_scene_command():
    clk = FakeClock()
    g = ob.CommandGate(clock=clk)
    assert g.allow("BTN SCENE", ob.REC_RECORDING) == "NextScene"


def test_next_scene_wraps_and_handles_unknown():
    assert ob.next_scene(["A", "B", "C"], "C") == "A"
    assert ob.next_scene(["A", "B", "C"], "A") == "B"
    assert ob.next_scene(["A", "B"], "Z") == "A"
    assert ob.next_scene([], "A") is None


def test_ui_order_uses_scene_index_descending():
    entries = [
        {"sceneName": "Low", "sceneIndex": 0},
        {"sceneName": "Top", "sceneIndex": 2},
        {"sceneName": "Mid", "sceneIndex": 1},
    ]
    assert ob.ui_order_names(entries) == ["Top", "Mid", "Low"]


def test_output_state_start_stop_resets_elapsed():
    st = ob.State()
    ob.apply_output_state(st, "OBS_WEBSOCKET_OUTPUT_STARTED", 10.0)
    assert st.rec == ob.REC_RECORDING
    assert st.elapsed(15.0) == 5
    ob.apply_output_state(st, "OBS_WEBSOCKET_OUTPUT_STOPPING", 16.0)
    assert st.rec == ob.REC_STOPPING
    ob.apply_output_state(st, "OBS_WEBSOCKET_OUTPUT_STOPPED", 17.0)
    assert st.rec == ob.REC_STOPPED
    assert st.elapsed(18.0) == 0


def test_pause_keeps_accumulated_time():
    st = ob.State()
    ob.apply_output_state(st, "OBS_WEBSOCKET_OUTPUT_STARTED", 0.0)
    ob.apply_output_state(st, "OBS_WEBSOCKET_OUTPUT_PAUSED", 10.0)
    assert st.rec == ob.REC_PAUSED
    assert st.elapsed(50.0) == 10
    ob.apply_output_state(st, "OBS_WEBSOCKET_OUTPUT_RESUMED", 50.0)
    assert st.rec == ob.REC_RECORDING
    assert st.elapsed(53.0) == 13


def test_record_status_sync():
    st = ob.State()
    ob.apply_record_status(st, True, False, 5.0)
    assert st.rec == ob.REC_RECORDING
    ob.apply_record_status(st, False, False, 9.0)
    assert st.rec == ob.REC_STOPPED


def test_st_line_format_and_scene_sanitize():
    st = ob.State(rec=ob.REC_RECORDING, rec_started_at=0.0, obs_ok=True, scene="Main Cam Long Name Here")
    line = st.st_line(7.2)
    parts = line.split(" ")
    assert parts[0] == "ST"
    assert parts[1] == "2"
    assert parts[2] == "7"
    assert parts[3] == "1"
    assert len(parts[4]) <= 15 and " " not in parts[4]


def test_parse_serial_lines():
    assert ob.parse_serial_line("BTN REC\r\n") == "BTN REC"
    assert ob.parse_serial_line("BTN SCENE") == "BTN SCENE"
    assert ob.parse_serial_line("HELLO 0.1.0") == "HELLO"
    assert ob.parse_serial_line("garbage") is None
