"use client";

import { useEffect, useState } from "react";

type Resource = { name: string; kind: "video" | "brand_json"; size: number; url: string };
type Props = { disabled?: boolean; language: string; onLanguageChange: (language: string) => void; onAnalyze: (videoName: string, language: string) => void };

function size(n: number) { return `${(n / 1024 / 1024).toFixed(1)} MB`; }

export default function ResourcePicker({ disabled, language, onLanguageChange, onAnalyze }: Props) {
  const [items, setItems] = useState<Resource[]>([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { fetch("/api/resources").then(r => r.json()).then(d => setItems(d.resources ?? [])).finally(() => setLoading(false)); }, []);
  const videos = items.filter(i => i.kind === "video");
  const brand = items.find(i => i.kind === "brand_json");
  return <div className="card p-5">
    <div className="flex items-start justify-between gap-4">
      <div><div className="text-[11px] uppercase tracking-widest text-rose">Judge-ready library</div><h3 className="mt-1 text-lg font-semibold">Analyze a bundled resource</h3><p className="mt-1 text-xs text-white/45">No upload wait. Videos stay local and are excluded from Git.</p></div>
      <div className="rounded-full bg-emerald-400/10 px-3 py-1 text-[11px] text-emerald-300">{loading ? "Loading" : `${videos.length} videos`}</div>
    </div>
    <div className="mt-4 flex flex-col gap-3 sm:flex-row">
      <select value={selected} onChange={e => setSelected(e.target.value)} disabled={disabled || loading} className="min-w-0 flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-3 text-sm text-white outline-none">
        <option value="">Choose a resource video</option>{videos.map(v => <option key={v.name} value={v.name}>{v.name} · {size(v.size)}</option>)}
      </select>
      <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 text-xs text-white/50">Language<select value={language} onChange={e => onLanguageChange(e.target.value)} disabled={disabled} className="bg-transparent py-3 text-white outline-none"><option value="bn">Bengali</option><option value="auto">Auto-detect</option><option value="hi">Hindi</option><option value="en">English</option><option value="ta">Tamil</option><option value="te">Telugu</option></select></label><button disabled={!selected || disabled || !brand} onClick={() => onAnalyze(selected, language)} className="btn-primary rounded-lg px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40">Analyze selected</button>
    </div>
    {brand && <div className="mt-3 text-xs text-white/40">Brand catalogue: <span className="text-white/70">{brand.name}</span> · available to the pipeline</div>}
  </div>;
}
