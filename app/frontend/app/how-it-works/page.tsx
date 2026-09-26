import Header from "@/components/Header";
import Footer from "@/components/Footer";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How it works · hoichoi Ad Intelligence",
  description: "Hybrid pipeline: local deterministic logic + hosted specialist models for context-aware Bengali video ad placement.",
};

const STEPS = [
  {
    num: "01",
    icon: "🎞",
    color: "rgba(240,180,41,.12)",
    title: "Prepare locally",
    body: "FFmpeg probes the video and extracts a mono 16 kHz audio track. PySceneDetect's ContentDetector identifies shot boundaries frame-by-frame on CPU — no GPU needed. Representative keyframes are resized to ≤720 p before any cloud call.",
  },
  {
    num: "02",
    icon: "🎙",
    color: "rgba(99,102,241,.12)",
    title: "Transcribe & Translate",
    body: "Audio is split into 5-minute chunks locally. Groq Whisper Large-v3-Turbo transcribes each chunk. If Groq is unavailable, local faster-whisper takes over deterministically. Bengali transcripts are automatically translated to English to maximize brand-context matching accuracy.",
  },
  {
    num: "03",
    icon: "🔍",
    color: "rgba(52,211,153,.12)",
    title: "Understand visually",
    body: "A resilient multi-tier fallback chain (Gemini 3.5 → OpenAI gpt-4o-mini → Local VLM → Pixel Analysis) extracts visual context. If an API quota trips, the system instantly latches to the next provider. The deterministic Pixel fallback ensures it never crashes and never hallucinates.",
  },
  {
    num: "04",
    icon: "⚖️",
    color: "rgba(240,90,115,.12)",
    title: "Apply hard rules",
    body: "Local Python enforces: no mid-sentence cuts, no active dialogue, no emotional climax, ≥120 s gap between breaks, ≤4 breaks/hour, ≤15 % total ad load. These constraints are deterministic — the cloud models cannot override them.",
  },
  {
    num: "05",
    icon: "🏷",
    color: "rgba(139,92,246,.12)",
    title: "Match brands",
    body: "MiniLM-L6 embeddings score each candidate against every brand's target_contexts. Any brand whose negative_contexts match the scene is hard-blocked. The brand catalogue is pure data (brands.json) — adding a new brand requires zero code changes.",
  },
  {
    num: "06",
    icon: "▶️",
    color: "rgba(148,163,184,.07)",
    title: "Deliver",
    body: "The source video is never modified. scenes.json, debug.json, vmap.xml, and playback.json are written to disk. The Next.js player loads playback.json, pauses at each accepted timestamp, renders a virtual black-screen ad card, and resumes automatically.",
  },
];

const OUTPUTS = [
  { icon: "📋", name: "scenes.json",   bg: "rgba(99,102,241,.10)",  desc: "Every semantic scene: shot list, transcript slice, visual context, score." },
  { icon: "🐛", name: "debug.json",    bg: "rgba(240,180,41,.10)",  desc: "Every break candidate with accept/reject reason and all intermediate scores." },
  { icon: "📺", name: "vmap.xml",      bg: "rgba(240,90,115,.10)",  desc: "VMAP 1.0 manifest — drop into any VAST-compatible video player." },
  { icon: "🎮", name: "playback.json", bg: "rgba(52,211,153,.10)",  desc: "Browser-side state machine: break timestamps, brand cards, countdown data." },
  { icon: "📝", name: "transcript.json", bg: "rgba(148,163,184,.08)", desc: "Full timestamped transcript from the ASR provider." },
];

const STATS = [
  { value: "221 s", label: "23-min episode (real)" },
  { value: "≤4", label: "breaks per hour" },
  { value: "15 %", label: "max ad load" },
];

export default function HowItWorksPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-5xl px-6 pb-24 pt-16 lg:px-10">

        {/* Hero */}
        <div className="mb-16 max-w-3xl">
          <div className="section-kicker mb-5">How it works</div>
          <h1 className="page-title">Context first.<br /><em>Placement second.</em></h1>
          <p className="mt-6 text-[1rem] leading-7 text-[var(--text-1)]">
            hoichoi is a hybrid pipeline. Local deterministic logic does the heavy lifting — media preparation, safety rules, and final timing decisions. Hosted specialist models (Groq, Gemini) contribute only context: transcripts and visual scene tags. The pipeline never uses a general-purpose chat LLM for placement.
          </p>
          {/* Stats */}
          <div className="mt-8 grid grid-cols-3 gap-3">
            {STATS.map(s => (
              <div key={s.label} className="rounded-xl border border-white/8 bg-[var(--bg-2)] p-4 text-center">
                <div className="font-mono text-xl font-bold text-[var(--text-0)]">{s.value}</div>
                <div className="mt-1 text-[.68rem] uppercase tracking-wide text-[var(--text-2)]">{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Steps grid */}
        <div className="section-kicker mb-6">Pipeline stages</div>
        <div className="hiw-grid">
          {STEPS.map(s => (
            <div key={s.num} className="hiw-card">
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-xl" style={{ background: s.color }}>{s.icon}</div>
                <span className="hiw-num">{s.num}</span>
              </div>
              <div className="hiw-title">{s.title}</div>
              <p className="hiw-body">{s.body}</p>
            </div>
          ))}
        </div>

        {/* Architecture */}
        <div className="mt-16">
          <div className="section-kicker mb-4">Architecture</div>
          <h2 className="text-xl font-bold mb-6">Hybrid boundary</h2>
          <div className="arch-pre">{`video.mp4 + brands.json
         │
         ▼
┌──────────────────────────────────────┐
│  LOCAL (this machine, no GPU)        │
│  FFmpeg · PySceneDetect · VAD        │
│  5-min audio chunking                │
│  MiniLM embeddings                   │
│  Hard rule enforcement               │
└──────────────┬───────────────────────┘
               │  bounded windows only
       ┌───────┴──────────┐
       ▼                  ▼
 Groq / Local       Gemini / OpenAI
 Whisper ASR        or Pixel Fallback
       │                  │
       └───────┬──────────┘
               ▼
  transcript + scene tags
               │
               ▼
┌──────────────────────────────────────┐
│  LOCAL deterministic decision        │
│  safety filter → brand match → VMAP  │
└──────────────────────────────────────┘`}</div>
          <p className="mt-4 text-sm text-[var(--text-1)] leading-6">
            The cloud models <strong>describe</strong> content. Local Python <strong>decides</strong> placement. Providers can fail or be swapped without changing ad-timing logic.
          </p>
        </div>

        {/* Outputs */}
        <div className="mt-16">
          <div className="section-kicker mb-4">Output files</div>
          <h2 className="text-xl font-bold mb-2">What every run produces</h2>
          <p className="text-sm text-[var(--text-1)] mb-6">All files land in <code>data/jobs/&lt;job_id&gt;/</code> and are downloadable from the demo UI.</p>
          <div className="card p-2">
            {OUTPUTS.map((o, i) => (
              <div key={o.name} className={`flex items-start gap-4 px-4 py-4 rounded-xl${i > 0 ? " border-t border-white/5 mt-1" : ""}`}>
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-xl" style={{ background: o.bg }}>{o.icon}</div>
                <div>
                  <div className="font-mono text-sm font-semibold text-[var(--text-0)]">{o.name}</div>
                  <div className="mt-1 text-[.8rem] text-[var(--text-1)] leading-5">{o.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-14 flex flex-wrap items-center gap-4 border-t border-white/8 pt-10">
          <a href="/#demo" className="btn-primary rounded-lg px-6 py-3 text-sm">Try the demo →</a>
          <a href="https://github.com/sidinsearch/hoichoi" target="_blank" rel="noreferrer" className="btn-ghost rounded-lg px-5 py-3 text-sm">View on GitHub ↗</a>
        </div>
      </main>
      <Footer />
    </>
  );
}
