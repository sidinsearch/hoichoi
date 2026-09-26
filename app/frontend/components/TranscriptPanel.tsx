"use client";

import type { BreakInfo } from "@/lib/playback";

type Scene = any;
type Props = { scenes: Scene[]; breaks: BreakInfo[] };

function label(s: Scene) {
  const activities = s.context?.activities?.filter(Boolean)?.slice(0, 3) ?? [];
  const setting = s.context?.setting && s.context.setting !== "unknown" ? s.context.setting : "Visual context unavailable";
  return activities.length ? activities.join(", ") : setting;
}

export default function TranscriptPanel({ scenes }: Props) {
  if (!scenes?.length) return null;
  const settings = new Set(scenes.map(s => s.context?.setting).filter(Boolean)).size;
  return (
    <section className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 px-5 py-4">
        <div>
          <div className="section-kicker">Scene detection</div>
          <h3 className="mt-1 text-lg font-semibold">{scenes.length} scenes detected</h3>
        </div>
        <span className="chip">{settings} unique settings</span>
      </div>
      <div className="max-h-[420px] overflow-y-auto p-3">
        <div className="grid gap-2 sm:grid-cols-2">
          {scenes.map((s, i) => (
            <div key={s.scene_id ?? i} className="min-w-0 rounded-lg border border-white/6 bg-[var(--bg-2)] px-3 py-2.5">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[.68rem] font-semibold text-[var(--rose-soft)]">{s.scene_id ?? `scene_${String(i + 1).padStart(3, "0")}`}</span>
                <span className="shrink-0 font-mono text-[.68rem] text-[var(--text-2)]">{Math.round(s.start_sec)}s → {Math.round(s.end_sec)}s</span>
              </div>
              <div className="mt-1.5 truncate text-xs text-[var(--text-1)]" title={label(s)}>{label(s)}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
