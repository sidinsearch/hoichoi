"use client";

export default function Footer() {
  return (
    <footer className="border-t border-white/5">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 py-10 text-xs text-white/40">
        <div>
          hoichoi Hackathon'26 · Problem 1 · Built end-to-end with multimodal AI
        </div>
        <div className="flex items-center gap-4">
          <span>Bengali ASR: faster-whisper</span>
          <span className="h-1 w-1 rounded-full bg-white/20" />
          <span>Brands are data, never code</span>
        </div>
      </div>
    </footer>
  );
}
