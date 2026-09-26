"use client";

import { useRef, useState } from "react";

type Props = { onAnalyze: (video: File, language: string) => void; disabled?: boolean; loading?: boolean };
const languages = [["bn", "Bengali"], ["auto", "Auto-detect"], ["hi", "Hindi"], ["en", "English"], ["ta", "Tamil"], ["te", "Telugu"], ["mr", "Marathi"], ["gu", "Gujarati"], ["kn", "Kannada"], ["ml", "Malayalam"], ["ur", "Urdu"]];
function fmtBytes(b: number) { return b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`; }

export default function UploadPanel({ onAnalyze, disabled, loading }: Props) {
  const [video, setVideo] = useState<File | null>(null);
  const [language, setLanguage] = useState("bn");
  const videoRef = useRef<HTMLInputElement>(null);
  const ready = Boolean(video) && !disabled;
  return <section className="card p-5">
    <div className="section-kicker">Custom video</div>
    <div className="mt-1 flex flex-wrap items-center justify-between gap-3">
      <div><h3 className="text-lg font-semibold">Upload your own video</h3><p className="mt-1 text-xs text-white/45">MP4, MOV, MKV, or WebM. The selected brand catalogue will be used.</p></div>
      <button type="button" onClick={() => videoRef.current?.click()} disabled={disabled} className="btn-ghost rounded-lg px-4 py-2 text-sm">{video ? "Choose another" : "Choose video"}</button>
      <input ref={videoRef} type="file" accept="video/*" className="sr-only" onChange={e => setVideo(e.target.files?.[0] ?? null)} />
    </div>
    {video && <div className="mt-4 flex items-center justify-between rounded-lg bg-white/[.04] px-3 py-3 text-sm"><span className="truncate text-white/80">{video.name}</span><span className="ml-3 shrink-0 text-xs text-white/40">{fmtBytes(video.size)}</span></div>}
    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-4">
      <label className="flex items-center gap-3 text-xs text-white/50">Language<select value={language} onChange={e => setLanguage(e.target.value)} disabled={disabled} className="rounded-md border border-white/10 bg-white/5 px-2 py-2 text-white outline-none">{languages.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <button type="button" disabled={!ready} onClick={() => video && onAnalyze(video, language)} className="btn-primary rounded-lg px-5 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40">{loading ? "Analyzing…" : "Analyze upload"}</button>
    </div>
  </section>;
}
