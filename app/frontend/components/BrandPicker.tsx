"use client";

import { useEffect, useState } from "react";

type Brand = { brand_id?: string; name?: string; brand_name?: string; category?: string; target_contexts?: string[]; negative_contexts?: string[]; };
type Props = { disabled?: boolean; onChange: (file: File | null) => void };

export default function BrandPicker({ disabled, onChange }: Props) {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { fetch("/api/resources/brands.json").then(r => r.json()).then(d => setBrands(Array.isArray(d) ? d : d.brands ?? [])).catch(() => setError("Could not load the default catalogue")); }, []);
  const choose = (next: File | null) => { setError(""); setFile(next); onChange(next); };
  return <section className="card p-5">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><div className="section-kicker">Brand catalogue</div><h3 className="mt-1 text-lg font-semibold">Use the default or bring your own</h3><p className="mt-1 text-xs text-white/45">Brand rules are read as data. Nothing is hard-coded into the UI.</p></div>
      <span className="proof-pill">{file ? "custom JSON" : `${brands.length || 8} default brands`}</span>
    </div>
    <div className="mt-4 flex flex-wrap gap-3">
      <button type="button" disabled={disabled} onClick={() => setOpen(v => !v)} className="btn-ghost rounded-lg px-4 py-2 text-sm">{open ? "Hide catalogue" : "View default catalogue"}</button>
      <label className="btn-ghost cursor-pointer rounded-lg px-4 py-2 text-sm">{file ? file.name : "Upload custom JSON"}<input type="file" accept="application/json,.json" className="sr-only" disabled={disabled} onChange={e => choose(e.target.files?.[0] ?? null)} /></label>
      {file && <button type="button" disabled={disabled} onClick={() => choose(null)} className="rounded-lg px-3 py-2 text-sm text-white/50 hover:text-white">Clear</button>}
    </div>
    {error && <p className="mt-3 text-xs text-rose">{error}</p>}
    {open && <div className="mt-4 grid max-h-56 gap-2 overflow-auto border-t border-white/10 pt-3 sm:grid-cols-2">{brands.map((b, i) => <div key={b.brand_id ?? i} className="rounded-lg bg-white/[.035] px-3 py-2"><div className="text-sm font-medium">{b.name ?? b.brand_name ?? `Brand ${i + 1}`}</div><div className="mt-1 text-xs text-white/40">{b.category ?? "catalogue entry"}</div></div>)}</div>}
  </section>;
}
