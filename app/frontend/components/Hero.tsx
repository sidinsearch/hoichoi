"use client";

export default function Hero() {
  return (
    <section className="hero-shell">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 pb-14 pt-14 lg:grid-cols-[minmax(0,1.05fr)_420px] lg:items-end lg:pt-20">
        <div>
          <div className="eyebrow"><span className="status-live" /> Hackathon demo · context-aware ad intelligence</div>
          <h1 className="hero-title mt-5 max-w-4xl">Place ads at the moment<br /><span>the story can carry them.</span></h1>
          <p className="hero-copy mt-5 max-w-2xl">Analyze long-form video, find safe scene boundaries, match a brand from data, and preview the result without changing the source file.</p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <a href="#demo" className="btn-primary rounded-lg px-5 py-3 text-sm">Open analysis workspace <span aria-hidden>→</span></a>
            <a href="#how" className="btn-ghost rounded-lg px-5 py-3 text-sm">Read the method</a>
          </div>
        </div>
        <div className="hero-proof">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <span className="eyebrow">Decision contract</span>
            <span className="proof-pill">deterministic</span>
          </div>
          <div className="grid grid-cols-3 gap-4 pt-5">
            <div><div className="proof-value">120s</div><div className="proof-label">minimum gap</div></div>
            <div><div className="proof-value">15%</div><div className="proof-label">ad-load ceiling</div></div>
            <div><div className="proof-value">4/h</div><div className="proof-label">break cap</div></div>
          </div>
          <p className="mt-5 text-xs leading-5 text-white/45">Cloud models describe audio and bounded frames. Local rules make the final placement decision.</p>
        </div>
      </div>
    </section>
  );
}
