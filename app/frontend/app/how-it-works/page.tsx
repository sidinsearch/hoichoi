import Header from "@/components/Header";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "How it works · hoichoi" };

const steps = [
  ["01", "Prepare", "FFmpeg extracts audio and representative frames locally. PySceneDetect identifies shot boundaries."],
  ["02", "Understand", "Groq Whisper or the configured fallback transcribes audio. Gemini sees only small bounded scene windows."],
  ["03", "Decide", "Local Python rules reject unsafe moments, enforce pacing, match brands, and generate final timestamps."],
  ["04", "Deliver", "The original video stays unchanged. The player pauses at accepted breaks and renders a virtual ad card."],
];

export default function HowItWorksPage() {
  return <><Header /><main className="mx-auto max-w-4xl px-6 py-16"><div className="section-kicker">How it works</div><h1 className="mt-4 text-4xl font-semibold tracking-tight">Context first. Placement second.</h1><p className="mt-4 max-w-2xl text-base leading-7 text-white/55">hoichoi combines hosted specialist models with local deterministic logic. Models describe the content; Python makes the decision.</p><div className="mt-12 grid gap-4">{steps.map(([number, title, body]) => <article key={number} className="method-card grid gap-4 sm:grid-cols-[64px_150px_1fr] sm:items-start"><span className="font-mono text-sm text-amber">{number}</span><h2 className="text-lg font-semibold">{title}</h2><p className="text-sm leading-6 text-white/50">{body}</p></article>)}</div><div className="mt-12 border-t border-white/10 pt-8"><div className="section-kicker">Outputs</div><p className="mt-3 text-sm leading-6 text-white/55">Every completed run produces <code>scenes.json</code>, <code>debug.json</code>, <code>vmap.xml</code>, <code>playback.json</code>, and a timestamped transcript.</p><a href="/" className="mt-6 inline-flex btn-primary rounded-lg px-5 py-3 text-sm">Back to demo →</a></div></main></>;
}
