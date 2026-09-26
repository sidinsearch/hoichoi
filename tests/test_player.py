"""Player state machine — backed by a pure-Python mirror (kept in sync with TS)."""

from __future__ import annotations

from app.backend.services.player_state import BreakInfo, next_phase


def test_break_triggered_at_timestamp():
    breaks = [BreakInfo(id="break_001", timestamp_sec=10.0, duration_sec=5)]
    consumed: set = set()
    p = next_phase(10.0, breaks, consumed, active_ad=None, ad_elapsed=0)
    assert p == "ad"


def test_consumed_break_not_re_triggered():
    breaks = [BreakInfo(id="break_001", timestamp_sec=10.0, duration_sec=5)]
    consumed = {"break_001"}
    p = next_phase(10.0, breaks, consumed, active_ad=None, ad_elapsed=0)
    assert p == "playing"


def test_active_ad_counts_down_then_completes():
    breaks = [BreakInfo(id="break_001", timestamp_sec=10.0, duration_sec=5)]
    consumed: set = set()
    active = BreakInfo(id="break_001", timestamp_sec=10.0, duration_sec=5)
    # mid-way through
    assert next_phase(15.0, breaks, consumed, active_ad=active, ad_elapsed=3) == "ad"
    # at completion
    assert next_phase(15.0, breaks, consumed, active_ad=active, ad_elapsed=5) == "playing"
