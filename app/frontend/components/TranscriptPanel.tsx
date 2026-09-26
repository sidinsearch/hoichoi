"use client";

import type { BreakInfo } from "@/lib/playback";

type Scene = any;
type Props = { scenes: Scene[]; breaks: BreakInfo[]; transcript?: Line[] };

function label(s: Scene) {
  const activities = s.context?.activities?.filter(Boolean)?.slice(0, 3) ?? [];
  const setting = s.context?.setting && s.context.setting !== "unknown" ? s.context.setting : "Visual context unavailable";
  return activities.length ? activities.join(", ") : setting;
}

type Line = { start: number; end: number; text: string; text_en?: string | null };

function TranscriptList({ lines }: { lines: Line[] }) {
  if (!lines.length) return null;
  return (
    <div className="max-h-[320px] overflow-y-auto border-t border-white/8 p-3">
      <ol className="grid gap-1.5">
        {lines.map((l, i) => (
          <li key={`${l.start}-${i}`} className="flex gap-3 rounded-md px-2 py-1.5 odd:bg-white/[.02]">
            <span className="w-14 shrink-0 text-right font-mono text-[.65rem] text-[var(--text-2)]">{formatStamp(l.start)}</span>
            <span className="min-w-0 text-xs leading-relaxed text-[var(--text-1)]">
              {l.text_en || l.text || <span className="italic text-[var(--text-2)]">no speech detected</span>}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function formatStamp(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function TranscriptPanel({ scenes, transcript = [] }: Props) {
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
      {transcript.length > 0 && (
        <>
          <div className="flex items-center justify-between gap-3 px-5 py-3">
            <div className="section-kicker">Transcript (English)</div>
            <span className="chip">{transcript.length} lines</span>
          </div>
          <TranscriptList lines={transcript} />
        </>
      )}
    </section>
  );
}
