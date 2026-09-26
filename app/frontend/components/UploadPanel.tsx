"use client";
import { useRef, useState } from "react";

type Props = { onAnalyze: (video: File, language: string) => void; disabled?: boolean; loading?: boolean };
const LANGS = [["bn","Bengali"],["auto","Auto-detect"],["hi","Hindi"],["en","English"],["ta","Tamil"],["te","Telugu"],["mr","Marathi"],["kn","Kannada"],["ml","Malayalam"],["ur","Urdu"]];
function fmtBytes(b: number) { return b < 1024*1024 ? `${(b/1024).toFixed(1)} KB` : `${(b/1024/1024).toFixed(1)} MB`; }

export default function UploadPanel({ onAnalyze, disabled, loading }: Props) {
  const [video, setVideo] = useState<File | null>(null);
  const [language, setLanguage] = useState("bn");
  const ref = useRef<HTMLInputElement>(null);
  const ready = !!video && !disabled;
  return (
    <section className="card p-5">
      <div className="section-kicker mb-4">Custom video</div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => !disabled && ref.current?.click()}
        onKeyDown={e => e.key === "Enter" && ref.current?.click()}
        className={`flex min-h-[90px] cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed transition-colors ${
          video ? "border-[var(--rose)] bg-[var(--rose-dim)]" : "border-white/10 hover:border-white/20 hover:bg-white/[.03]"
        } ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
      >
        <input ref={ref} type="file" accept="video/*" className="sr-only" onChange={e => setVideo(e.target.files?.[0] ?? null)} />
        {video ? (
          <>
            <span className="text-lg">🎬</span>
            <span className="max-w-[220px] truncate text-sm font-semibold text-[var(--text-0)]">{video.name}</span>
            <span className="text-xs text-[var(--text-2)]">{fmtBytes(video.size)} · click to change</span>
          </>
        ) : (
          <>
            <span className="text-2xl opacity-40">📁</span>
            <span className="text-sm text-[var(--text-1)]">Click to choose a video</span>
            <span className="text-xs text-[var(--text-2)]">MP4, MOV, MKV, WebM</span>
          </>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-white/8 pt-4">
        <label className="flex items-center gap-2 text-xs text-[var(--text-2)]">
          Language
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            disabled={disabled}
            className="field-select"
            style={{ width: "auto" }}
          >
            {LANGS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <button
          type="button"
          disabled={!ready}
          onClick={() => video && onAnalyze(video, language)}
          className="btn-primary rounded-lg px-5 py-2.5 text-sm"
        >
          {loading ? "Analyzing…" : "Analyze upload"}
        </button>
      </div>
    </section>
  );
}
