"use client";

import type { BreakInfo } from "@/lib/playback";

type Props = {
  jobId: string | null;
  videoUrl: string | null;
  breaks: BreakInfo[];
  status: string;
  stage?: string;
  progress?: number;
};

export default function ResultsPanel({ jobId, videoUrl, breaks, status, stage, progress }: Props) {
  if (!jobId) {
    return (
      <div className="rounded-2xl border border-white/10 bg-carbon p-6 text-sm text-white/60">
        Upload a video and brand catalogue to start analysis.
      </div>
    );
  }
  return (
    <div className="grid gap-4 rounded-2xl border border-white/10 bg-carbon p-6 md:grid-cols-4">
      <Stat label="Status" value={status} />
      <Stat label="Progress" value={progress != null ? `${Math.round(progress)}%` : "—"} />
      <Stat label="Scenes" value={status === "completed" ? "✓" : "…"} />
      <Stat label="Accepted breaks" value={String(breaks.length)} />
      {stage && (
        <div className="md:col-span-4 mt-2">
          <div className="mb-1 text-xs text-white/50">Current stage</div>
          <div className="rounded-lg bg-black/40 px-3 py-2 font-mono text-xs text-white/80">
            {stage}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-widest text-white/40">{label}</div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}
