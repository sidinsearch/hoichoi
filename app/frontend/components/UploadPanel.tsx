"use client";
import { useState } from "react";

type Props = {
  onAnalyze: (video: File, brandJson: File) => void;
  disabled?: boolean;
};

export default function UploadPanel({ onAnalyze, disabled }: Props) {
  const [video, setVideo] = useState<File | null>(null);
  const [brand, setBrand] = useState<File | null>(null);

  const ready = !!video && !!brand && !disabled;

  return (
    <div className="grid gap-4 rounded-2xl border border-white/10 bg-carbon p-6 md:grid-cols-2">
      <label className="block">
        <div className="mb-2 text-sm text-white/70">Bengali drama video</div>
        <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-white/15 bg-white/5 text-center text-xs text-white/50">
          {video ? (
            <span className="text-white/80">{video.name} · {(video.size / 1024 / 1024).toFixed(1)} MB</span>
          ) : (
            <span>Click to select .mp4 / .mov</span>
          )}
        </div>
        <input
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => setVideo(e.target.files?.[0] ?? null)}
        />
        <input
          type="file"
          accept="video/*"
          className="mt-2 block w-full text-xs text-white/60 file:rounded-md file:border-0 file:bg-rose file:px-3 file:py-1.5 file:text-white hover:file:bg-rose/80"
          onChange={(e) => setVideo(e.target.files?.[0] ?? null)}
        />
      </label>

      <label className="block">
        <div className="mb-2 text-sm text-white/70">Synthetic brand.json</div>
        <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-white/15 bg-white/5 text-center text-xs text-white/50">
          {brand ? (
            <span className="text-white/80">{brand.name}</span>
          ) : (
            <span>Click to select brand.json</span>
          )}
        </div>
        <input
          type="file"
          accept="application/json,.json"
          className="mt-2 block w-full text-xs text-white/60 file:rounded-md file:border-0 file:bg-rose file:px-3 file:py-1.5 file:text-white hover:file:bg-rose/80"
          onChange={(e) => setBrand(e.target.files?.[0] ?? null)}
        />
      </label>

      <div className="md:col-span-2">
        <button
          disabled={!ready}
          onClick={() => ready && video && brand && onAnalyze(video, brand)}
          className={`w-full rounded-xl py-3 text-sm font-semibold tracking-wide transition ${
            ready
              ? "bg-rose text-white hover:bg-rose/90"
              : "cursor-not-allowed bg-white/10 text-white/40"
          }`}
        >
          {disabled ? "Analyzing..." : "Analyze Video"}
        </button>
      </div>
    </div>
  );
}
