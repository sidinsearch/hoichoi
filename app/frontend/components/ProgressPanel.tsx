"use client";

type Props = { stages: string[]; current?: string };

export default function ProgressPanel({ stages, current }: Props) {
  if (!current) return null;
  const idx = Math.max(0, stages.indexOf(current));
  const pct = Math.round(((idx + 1) / stages.length) * 100);
  return (
    <div className="card p-6">
      <div className="mb-3 flex items-center justify-between text-xs text-white/50">
        <span className="uppercase tracking-widest">Pipeline stages</span>
        <span className="font-mono text-white/70">{stages[idx] ?? "starting"}</span>
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
