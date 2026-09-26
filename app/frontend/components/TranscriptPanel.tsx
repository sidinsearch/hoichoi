"use client";

import type { BreakInfo } from "@/lib/playback";

type Scene = any;

type Props = {
  scenes: Scene[];
  breaks: BreakInfo[];
};

export default function TranscriptPanel({ scenes, breaks }: Props) {
  if (!scenes?.length) return null;
  return (
    <div className="card p-6">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-widest text-white/40">Detected scenes</div>
          <div className="mt-1 text-2xl font-bold">{scenes.length}</div>
        </div>
        <span className="chip">{new Set(scenes.map((s) => s.context?.setting).filter(Boolean)).size} unique settings</span>
      </div>
      <div className="grid gap-2">
        {scenes.slice(0, 20).map((s) => (
          <div key={s.scene_id} className="flex items-center gap-3 rounded-lg bg-white/[0.03] px-3 py-2 text-sm">
            <span className="font-mono text-xs text-rose">{s.scene_id}</span>
            <span className="font-mono text-xs text-white/40">
              {Math.round(s.start_sec)}s → {Math.round(s.end_sec)}s
            </span>
            <span className="ml-auto truncate text-xs text-white/60">
              {s.context?.activities?.slice(0, 3).join(", ") || "no clear activity"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
