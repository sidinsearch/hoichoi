"use client";
import { useEffect, useState } from "react";

type Brand = { brand_id?: string; name?: string; brand_name?: string; category?: string; target_contexts?: string[]; negative_contexts?: string[] };
type Props = { disabled?: boolean; onChange: (f: File | null) => void };

export default function BrandPicker({ disabled, onChange }: Props) {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [open, setOpen] = useState(false);
  const [err, setErr] = useState("");
  useEffect(() => {
    fetch("/api/resources/brands.json")
      .then(r => r.json())
      .then(d => setBrands(Array.isArray(d) ? d : d.brands ?? []))
      .catch(() => setErr("Could not load default catalogue"));
  }, []);

  const choose = (next: File | null) => { setErr(""); setFile(next); onChange(next); };

  return (
    <section className="card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <div className="section-kicker">Brand catalogue</div>
          <h3 className="mt-1 text-base font-semibold text-[var(--text-0)]">Use default or upload custom</h3>
          <p className="mt-0.5 text-xs text-[var(--text-2)]">Brand rules are pure data — no code changes needed.</p>
        </div>
        <span className={file ? "badge-rose text-[.7rem] font-semibold px-3 py-1 rounded-full border" : "proof-pill"}>
          {file ? "custom JSON" : `${brands.length || 8} default brands`}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setOpen(v => !v)}
          className="btn-ghost rounded-lg px-4 py-2 text-sm"
        >
          {open ? "Hide catalogue" : "View default catalogue"}
        </button>
        <label className="btn-ghost cursor-pointer rounded-lg px-4 py-2 text-sm">
          {file ? `✓ ${file.name}` : "Upload custom JSON"}
          <input type="file" accept="application/json,.json" className="sr-only" disabled={disabled} onChange={e => choose(e.target.files?.[0] ?? null)} />
        </label>
        {file && (
          <button type="button" disabled={disabled} onClick={() => choose(null)} className="rounded-lg px-3 py-2 text-xs text-[var(--text-2)] hover:text-[var(--text-0)] transition-colors">
            ✕ Clear
          </button>
        )}
      </div>

      {err && <p className="mt-3 text-xs" style={{ color: "var(--rose)" }}>{err}</p>}

      {open && brands.length > 0 && (
        <div className="mt-4 grid max-h-60 gap-2 overflow-auto border-t border-white/8 pt-3 sm:grid-cols-2">
          {brands.map((b, i) => (
            <div key={b.brand_id ?? i} className="rounded-lg border border-white/6 bg-[var(--bg-2)] px-3 py-2.5">
              <div className="text-sm font-semibold text-[var(--text-0)]">{b.name ?? b.brand_name ?? `Brand ${i + 1}`}</div>
              <div className="mt-0.5 text-[.72rem] text-[var(--text-2)]">{b.category ?? "catalogue entry"}</div>
              {b.target_contexts && b.target_contexts.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {b.target_contexts.slice(0, 3).map(t => <span key={t} className="chip">{t}</span>)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
