"use client";

type Props = {
  status: string;
  stage?: string;
  progress?: number;
  summary?: { scenes: number; candidates: number; accepted: number; rejected: number };
};

function Stat({ label, value, accent }: { label: string; value: string | number; accent?: string }) {
  return (
    <div className="card min-w-0 overflow-hidden px-4 py-3">
      <div className="truncate text-[10px] uppercase tracking-[.14em] text-white/40">{label}</div>
      <div className={`mt-1 truncate text-xl font-bold leading-tight ${accent ?? "text-white"}`} title={String(value)}>{value}</div>
    </div>
  );
}

export default function ResultsPanel(props: Props) {
  const { status, stage, progress, summary } = props;
  const done = status === "completed";
  const failed = status === "failed";
  return (
    <div className="grid grid-cols-2 gap-3">
      <Stat label="Status" value={status.toUpperCase()} accent={failed ? "text-rose" : done ? "text-emerald-400" : "text-amber-300"} />
      <Stat label="Progress" value={progress != null ? `${Math.round(progress)}%` : "—"} />
      <Stat label="Scenes" value={summary?.scenes ?? "—"} />
      <Stat label="Accepted" value={summary?.accepted ?? "—"} accent={(summary?.accepted ?? 0) > 0 ? "text-emerald-400" : undefined} />
      {stage && (
        <div className="col-span-2 card px-4 py-3">
          <div className="mb-1 text-xs uppercase tracking-widest text-white/40">Current stage</div>
          <div className="font-mono text-sm text-white/80">{stage}</div>
        </div>
      )}
    </div>
  );
}
