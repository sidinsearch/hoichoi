"use client";

import type { BreakInfo } from "@/lib/playback";
import { useState } from "react";

type Props = { breaks: BreakInfo[]; scenes?: any[] };

export default function BreakDetails({ breaks }: Props) {
  const [selected, setSelected] = useState<BreakInfo | null>(breaks[0] ?? null);
  if (!breaks.length) {
    return (
      <div className="rounded-2xl border border-white/10 bg-carbon p-6 text-sm text-white/60">
        No accepted breaks yet.
      </div>
    );
  }
  return (
    <div className="grid gap-4 rounded-2xl border border-white/10 bg-carbon p-4 md:grid-cols-[200px_1fr]">
      <ul className="max-h-72 overflow-y-auto pr-1">
        {breaks.map((b) => (
          <li key={b.id}>
            <button
              onClick={() => setSelected(b)}
              className={`mb-1 w-full rounded-md px-2 py-2 text-left text-xs transition ${
                selected?.id === b.id
                  ? "bg-rose text-white"
                  : "bg-white/5 text-white/70 hover:bg-white/10"
              }`}
            >
              <div className="font-semibold">{b.display_name}</div>
              <div className="opacity-70">
                @ {formatTs(b.timestamp_sec)} · {b.duration_sec}s
              </div>
            </button>
          </li>
        ))}
      </ul>

      {selected && (
        <div className="text-sm text-white/80">
          <div className="text-xs uppercase tracking-widest text-white/40">Selected break</div>
          <h3 className="mt-1 text-2xl font-bold">{selected.display_name}</h3>
          <div className="text-white/60">{selected.category}</div>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-xs">
            <Pair k="Timestamp" v={formatTs(selected.timestamp_sec)} />
            <Pair k="Duration" v={`${selected.duration_sec}s`} />
            <Pair k="Break ID" v={selected.id} />
            <Pair k="Brand ID" v={selected.brand_id} />
          </dl>
          {selected.context_summary && (
            <p className="mt-4 rounded-md bg-black/30 p-3 text-xs italic text-white/70">
              "{selected.context_summary}"
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Pair({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-white/40">{k}</dt>
      <dd className="font-mono">{v}</dd>
    </div>
  );
}

function formatTs(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  return [h, m, sec].map((n) => String(n).padStart(2, "0")).join(":");
}
