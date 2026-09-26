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
    <div className="card p-6">
      <div className="mb-3 flex items-center justify-between text-xs text-white/50">
        <span className="uppercase tracking-widest">Pipeline stages</span>
        <span className="font-mono text-white/70">{LABELS[current] ?? current}</span>
      </div>
      <div className="mb-5 h-1.5 overflow-hidden rounded-full bg-white/5">
        <div
          className="h-full rounded-full"
          style={{
            width: `${pct}%`,
            background: "linear-gradient(90deg, var(--rose), var(--rose-soft))",
            transition: "width 240ms ease",
          }}
        />
      </div>
      <div className="mb-4 flex items-center justify-between text-xs text-white/50">
        <span>Processing</span><span className="font-mono text-lg font-bold text-white">{Math.round(pct)}%</span>
      </div>
      <ul className="grid gap-1.5 text-sm">
        {stages.map((s, i) => {
          const state = i < idx ? "done" : i === idx ? "active" : "todo";
          return (
            <li key={s} className="flex items-center gap-3">
              <span className={`dot ${state}`} />
              <span className={`font-mono text-xs ${state === "active" ? "text-rose" : state === "done" ? "text-emerald-300" : "text-white/40"}`}>
                {state === "done" ? "✓" : state === "active" ? "●" : "○"}
              </span>
              <span className={state === "active" ? "text-white" : state === "done" ? "text-white/70" : "text-white/40"}>
                {s}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
