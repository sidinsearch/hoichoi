"use client";

import { useState } from "react";

type Props = { stages: string[]; current?: string };

export default function ProgressPanel({ stages, current }: Props) {
  if (!current) return null;
  const idx = Math.max(0, stages.indexOf(current));
  const pct = Math.round(((idx + 1) / stages.length) * 100);
  return (
    <div className="rounded-2xl border border-white/10 bg-carbon p-6">
      <div className="mb-3 flex items-center justify-between text-xs text-white/60">
        <span>Live pipeline progress</span>
        <span className="font-mono">{pct}%</span>
      </div>
      <div className="mb-4 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full bg-rose transition-all" style={{ width: `${pct}%` }} />
      </div>
      <ul className="grid gap-1 text-xs">
        {stages.map((s, i) => (
          <li
            key={s}
            className={`flex items-center gap-2 ${
              i < idx
                ? "text-emerald-400"
                : i === idx
                ? "text-rose"
                : "text-white/40"
            }`}
          >
            <span className="font-mono">{i < idx ? "✓" : i === idx ? "●" : "○"}</span>
            <span>{s}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
