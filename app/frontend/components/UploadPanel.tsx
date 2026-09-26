"use client";

import { useRef, useState } from "react";

type Props = {
  onAnalyze: (video: File, brandJson: File) => void;
  disabled?: boolean;
  loading?: boolean;
};

function fmtBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

export default function UploadPanel({ onAnalyze, disabled, loading }: Props) {
  const [video, setVideo] = useState<File | null>(null);
  const [brand, setBrand] = useState<File | null>(null);
  const videoRef = useRef<HTMLInputElement>(null);
  const brandRef = useRef<HTMLInputElement>(null);

  const ready = !!video && !!brand && !disabled;

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <button
        type="button"
        onClick={() => videoRef.current?.click()}
        className={`group card relative flex h-44 flex-col items-center justify-center gap-3 p-6 text-center transition ${
          video ? "ring-2 ring-rose/40" : "hover:bg-white/[0.03]"
        }`}
      >
        <div className="grid h-12 w-12 place-items-center rounded-xl bg-rose/10 text-rose">
          {video ? "✓" : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 6v12l11-6z" />
            </svg>
          )}
        </div>
        <div>
          <div className="font-semibold">
            {video ? video.name : "Bengali drama video"}
          </div>
          <div className="mt-1 text-xs text-white/40">
            {video ? fmtBytes(video.size) : "MP4 · MOV · WebM"}
          </div>
        </div>
        <input
          ref={videoRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => setVideo(e.target.files?.[0] ?? null)}
        />
      </button>

      <button
        type="button"
        onClick={() => brandRef.current?.click()}
        className={`group card relative flex h-44 flex-col items-center justify-center gap-3 p-6 text-center transition ${
          brand ? "ring-2 ring-rose/40" : "hover:bg-white/[0.03]"
        }`}
      >
        <div className="grid h-12 w-12 place-items-center rounded-xl bg-purple-500/10 text-purple-300">
          {brand ? "✓" : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M5 4h11l3 3v13H5z" />
            </svg>
          )}
        </div>
        <div>
          <div className="font-semibold">
            {brand ? brand.name : "Synthetic brand.json"}
          </div>
          <div className="mt-1 text-xs text-white/40">
            {brand ? `${fmtBytes(brand.size)} · ${brand.name}` : "8 demo brands, or add Brand I"}
          </div>
        </div>
        <input
          ref={brandRef}
          type="file"
          accept="application/json,.json"
          className="hidden"
          onChange={(e) => setBrand(e.target.files?.[0] ?? null)}
        />
      </button>

      <div className="md:col-span-2 flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs text-white/40">
          Source video is never permanently edited. Decisions render as a virtual
          black-screen ad card.
        </div>
        <button
          disabled={!ready}
          onClick={() => ready && video && brand && onAnalyze(video, brand)}
          className={`rounded-xl px-6 py-3 text-sm font-semibold tracking-wide transition ${
            ready
              ? "btn-primary"
              : "cursor-not-allowed bg-white/5 text-white/30"
          }`}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Analyzing…
            </span>
          ) : (
            "Analyze Video"
          )}
        </button>
      </div>
    </div>
  );
}
