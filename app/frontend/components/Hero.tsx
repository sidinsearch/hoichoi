"use client";

export default function Hero() {
  return (
    <section className="hero-bg relative overflow-hidden border-b border-white/5">
      <div className="mx-auto max-w-7xl px-6 pb-16 pt-20 md:pt-28">
        <div className="grid items-center gap-10 md:grid-cols-[1.2fr_1fr]">
          <div>
            <span className="chip mb-6 inline-flex">
              <span className="h-1.5 w-1.5 rounded-full bg-rose pulse" />
              Live demo · no GPU required
            </span>
            <h1 className="text-5xl font-bold leading-[1.05] tracking-tight md:text-6xl">
              <span className="glow-text">Understand the story.</span>
              <br />
              <span className="text-white/90">Pick the right moment.</span>
              <br />
              <span className="text-white/60">Place a brand that fits.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-white/60">
              A semantic pipeline that turns a long-form Bengali drama into a clean
              ad-break schedule — without ever modifying the source video. Where to
              cut, whether to cut, and what to show. Driven by ASR + vision + audio
              signals. Anchored by deterministic safety rules.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a href="#demo" className="btn-primary rounded-xl px-5 py-3 text-sm">
                Run the demo
              </a>
              <a href="#how" className="btn-ghost rounded-xl px-5 py-3 text-sm">
                How it works
              </a>
              <div className="ml-1 flex items-center gap-2 text-xs text-white/40">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                v0.1.0 · backend online
              </div>
            </div>
          </div>

          <div className="card relative p-6 shadow-2xl">
            <div className="absolute -top-px left-6 right-6 h-px bg-gradient-to-r from-transparent via-rose to-transparent" />
            <div className="mb-4 flex items-center justify-between">
              <div className="text-xs uppercase tracking-widest text-white/40">Pipeline at a glance</div>
              <span className="chip text-emerald-300">no chat LLM</span>
            </div>
            <ol className="grid gap-3 text-sm">
              {[
                ["01", "ASR (bn)", "faster-whisper"],
                ["02", "Shots", "PySceneDetect"],
                ["03", "Keyframes", "ffmpeg + VLM (optional)"],
                ["04", "Scenes", "multimodal fusion"],
                ["05", "Breaks", "deterministic rules"],
                ["06", "Brands", "MiniLM + hard blocks"],
                ["07", "VMAP", "scene-bound ad schedule"],
              ].map(([k, name, sub]) => (
                <li key={k} className="flex items-center justify-between rounded-lg bg-white/[0.03] px-3 py-2">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-[11px] text-rose">{k}</span>
                    <span className="font-medium text-white">{name}</span>
                  </div>
                  <span className="text-xs text-white/40">{sub}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </section>
  );
}
