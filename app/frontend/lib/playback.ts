// Pure player state machine. No React, no DOM — pure transitions.

export type BreakInfo = {
  id: string;
  timestamp_sec: number;
  duration_sec: number;
  brand_id: string;
  display_name: string;
  category: string;
  context_summary: string;
};

export type PlayerPhase =
  | { kind: "playing"; currentTime: number }
  | { kind: "ad"; break: BreakInfo; breakId: string; remainingSec: number; totalSec: number }
  | { kind: "ended" };

/** Returns the phase that should be active given the player's current time and break state. */
export function nextPhase(
  currentTime: number,
  breaks: BreakInfo[],
  consumed: Set<string>,
  activeAd: BreakInfo | null,
  adElapsed: number
): PlayerPhase {
  if (activeAd) {
    const remaining = activeAd.duration_sec - adElapsed;
    if (remaining <= 0) {
      consumed.add(activeAd.id);
      return { kind: "playing", currentTime };
    }
    return { kind: "ad", break: activeAd, breakId: activeAd.id, remainingSec: remaining, totalSec: activeAd.duration_sec };
  }

  // Look for a break in the next 0.2s window (handles browser timeupdate granularity)
  const due = breaks.find(
    (b) => !consumed.has(b.id) && currentTime >= b.timestamp_sec - 0.2
  );
  if (due) {
    return {
      kind: "ad",
      break: due,
      breakId: due.id,
      remainingSec: due.duration_sec,
      totalSec: due.duration_sec,
    };
  }
  return { kind: "playing", currentTime };
}

/** Click handler for the timeline — seek to before the break. */
export function seekBeforeBreak(target: number): number {
  return Math.max(0, target - 1.0);
}
