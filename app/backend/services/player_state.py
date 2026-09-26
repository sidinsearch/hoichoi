"""Player state machine — pure Python mirror of app/frontend/lib/playback.ts.

We keep this tiny module so the test suite can verify transitions without
spinning up Node. The TypeScript module is the runtime source-of-truth.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Set


@dataclass
class BreakInfo:
    id: str
    timestamp_sec: float
    duration_sec: int
    brand_id: str = ""
    display_name: str = ""
    category: str = ""


def next_phase(current_time: float,
               breaks: list,
               consumed: Set[str],
               active_ad: Optional[BreakInfo],
               ad_elapsed: float) -> str:
    """Returns one of: 'ad', 'playing', 'ended'."""
    if active_ad is not None:
        if active_ad.duration_sec - ad_elapsed <= 0:
            consumed.add(active_ad.id)
            return "playing"
        return "ad"
    for b in breaks:
        if b.id in consumed:
            continue
        if current_time >= b.timestamp_sec - 0.2:
            return "ad"
    return "playing"
