"use client";
import { useEffect, useState } from "react";

type Resource = { name: string; kind: "video" | "brand_json"; size: number; url: string };
type Props = { disabled?: boolean; language: string; onLanguageChange: (l: string) => void; onAnalyze: (name: string, lang: string) => void };
function fmtMB(n: number) { return `${(n / 1024 / 1024).toFixed(1)} MB`; }

const LANGS = [["bn","Bengali"],["auto","Auto-detect"],["hi","Hindi"],["en","English"],["ta","Tamil"],["te","Telugu"],["mr","Marathi"],["kn","Kannada"],["ml","Malayalam"],["ur","Urdu"]];

export default function ResourcePicker({ disabled, language, onLanguageChange, onAnalyze }: Props) {
  const [items, setItems] = useState<Resource[]>([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    fetch("/api/resources").then(r => r.json()).then(d => setItems(d.resources ?? [])).finally(() => setLoading(false));
  }, []);
  const videos = items.filter(i => i.kind === "video");
  const hasBrand = items.some(i => i.kind === "brand_json");
  const ready = !!selected && !disabled && hasBrand;

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="section-kicker" style={{ color: "var(--rose-soft)" }}>Library</div>
          <h3 className="mt-1 text-base font-semibold text-[var(--text-0)]">Analyze a bundled video</h3>
          <p className="mt-0.5 text-xs text-[var(--text-2)]">Videos stay local — no re-upload needed.</p>
        </div>
        <span className="proof-pill shrink-0">
          {loading ? "Loading…" : `${videos.length} videos`}
        </span>
      </div>

      <div className="grid gap-3">
        <select
          value={selected}
          onChange={e => setSelected(e.target.value)}
          disabled={disabled || loading}
          className="field-select w-full"
        >
          <option value="">— Choose a video —</option>
          {videos.map(v => (
            <option key={v.name} value={v.name}>{v.name.replace(/_/g, " ").replace(/\.mp4$/i, "")} · {fmtMB(v.size)}</option>
          ))}
        </select>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-[var(--text-2)] shrink-0">
            Language
          </label>
          <select
            value={language}
            onChange={e => onLanguageChange(e.target.value)}
            disabled={disabled}
            className="field-select flex-1"
          >
            {LANGS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
          <button
            disabled={!ready}
            onClick={() => onAnalyze(selected, language)}
            className="btn-primary rounded-lg px-5 py-2.5 text-sm shrink-0"
          >
            Analyze →
          </button>
        </div>
      </div>

      {hasBrand && (
        <p className="mt-3 text-[.72rem] text-[var(--text-2)]">
          Brand catalogue: <span className="text-[var(--text-1)]">brands.json</span> — override in the brand panel above
        </p>
      )}
    </div>
  );
}
