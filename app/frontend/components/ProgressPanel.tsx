"use client";

type Props = { stages: string[]; current?: string; progress?: number };

const LABELS: Record<string, string> = {
  uploading: "Preparing video",
  extracting_audio: "Extracting audio",
  transcribing_audio: "Transcribing audio",
  detecting_shots: "Detecting scene cuts",
  analyzing_visual_context: "Analyzing visual context",
  building_scenes: "Building scenes",
  finding_break_candidates: "Finding safe break candidates",
  applying_safety_rules: "Applying safety rules",
  matching_brands: "Matching brands",
  generating_outputs: "Generating output files",
  ready: "Completed",
};

export default function ProgressPanel({ stages, current, progress = 0 }: Props) {
  if (!current) return null;
  const idx = Math.max(0, stages.indexOf(current));
  const pct = Math.max(0, Math.min(100, Math.round(progress)));
  return (
    <div className="card p-5">
      <div className="mb-4 flex items-end justify-between gap-3">
        <div>
          <div className="text-[10px] uppercase tracking-[.16em] text-white/40">Processing</div>
          <div className="mt-1 font-mono text-2xl font-bold leading-none text-white">{pct}%</div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-[.16em] text-white/40">Current step</div>
          <div className="mt-1 max-w-[190px] truncate text-xs text-rose" title={LABELS[current] ?? current}>{LABELS[current] ?? current}</div>
        </div>
      </div>
      <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-white/5">
        <div
          className="h-full rounded-full"
          style={{
            width: `${pct}%`,
            background: "linear-gradient(90deg, var(--rose), var(--rose-soft))",
            transition: "width 240ms ease",
          }}
        />
      </div>
      <ul className="grid gap-1.5 text-xs">
        {stages.map((s, i) => {
          const state = i < idx ? "done" : i === idx ? "active" : "todo";
          return (
            <li key={s} className="flex items-center gap-3">
              <span className={`dot ${state}`} />
              <span className={`font-mono text-xs ${state === "active" ? "text-rose" : state === "done" ? "text-emerald-300" : "text-white/40"}`}>
                {state === "done" ? "✓" : state === "active" ? "●" : "○"}
              </span>
              <span className={state === "active" ? "text-white" : state === "done" ? "text-white/70" : "text-white/40"}>
                {LABELS[s] ?? s}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
