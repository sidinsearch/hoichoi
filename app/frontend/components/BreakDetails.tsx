"use client";

import type { BreakInfo } from "@/lib/playback";
import { useState } from "react";

type Scene = { scene_id: string; start_sec: number; end_sec: number; context: { activities: string[] } };

function formatTs(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  return [h, m, sec].map((n) => String(n).padStart(2, "0")).join(":");
}

type Props = {
  breaks: BreakInfo[];
  scenes?: Scene[];
};

export default function BreakDetails({ breaks, scenes }: Props) {
  const [selected, setSelected] = useState<BreakInfo | null>(breaks[0] ?? null);
  if (!breaks.length) {
    return (
      <div className="card p-6 text-sm text-white/60">
        No accepted breaks yet — try a longer video or bump{" "}
        <code className="rounded bg-white/10 px-1">MAX_BREAKS_PER_HOUR</code>.
      </div>
    );
  }
  return (
    <div className="grid gap-4 md:grid-cols-[260px_1fr]">
      <ul className="card max-h-96 overflow-y-auto p-2">
        {breaks.map((b) => (
          <li key={b.id}>
            <button
              onClick={() => setSelected(b)}
              className={`mb-1 w-full rounded-lg px-3 py-2 text-left text-sm transition ${
                selected?.id === b.id
                  ? "bg-rose/15 ring-1 ring-rose/40 text-white"
                  : "text-white/70 hover:bg-white/5"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold">{b.display_name}</span>
                <span className="font-mono text-xs text-white/40">{b.duration_sec}s</span>
              </div>
              <div className="mt-0.5 flex items-center justify-between text-xs text-white/40">
                <span>{b.category}</span>
                <span className="font-mono">{formatTs(b.timestamp_sec)}</span>
              </div>
            </button>
          </li>
        ))}
      </ul>

      {selected && (
        <div className="card p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-[11px] uppercase tracking-widest text-rose">Selected break</div>
              <h3 className="mt-1 text-2xl font-bold tracking-tight">{selected.display_name}</h3>
              <div className="mt-1 text-sm text-white/60">{selected.category}</div>
            </div>
            <span className="chip brand">{selected.brand_id}</span>
          </div>

          <dl className="mt-5 grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
            <Pair k="Timestamp" v={formatTs(selected.timestamp_sec)} />
            <Pair k="Duration" v={`${selected.duration_sec}s`} />
            <Pair k="Break ID" v={selected.id} />
            <Pair k="Brand ID" v={selected.brand_id} />
            <Pair k="Source episode" v="original, unmodified" />
            <Pair k="Ad mode" v="virtual black-screen" />
          </dl>

          {selected.context_summary && (
            <blockquote className="mt-5 rounded-lg border-l-2 border-rose/60 bg-rose/[0.06] p-3 text-sm italic text-white/80">
              "{selected.context_summary}"
            </blockquote>
          )}

          {scenes && scenes.length > 0 && (
            <div className="mt-6">
              <div className="text-[11px] uppercase tracking-widest text-white/40">Detected scenes</div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {scenes.slice(0, 16).map((s) => (
                  <span key={s.scene_id} className="chip">
                    {s.scene_id}
                    <span className="font-mono text-white/40">
                      {formatTs(s.start_sec)}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Pair({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-widest text-white/40">{k}</dt>
      <dd className="mt-0.5 font-mono text-white">{v}</dd>
    </div>
  );
}
