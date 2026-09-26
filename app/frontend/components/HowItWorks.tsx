"use client";

type Item = { k: string; v: string };

export default function HowItWorks() {
  const items: Item[] = [
    {
      k: "Where to cut",
      v: "End of semantic scene + completed sentence + dialogue pause + ≥ 1.5 s silence.",
    },
    {
      k: "Whether to cut",
      v: "Minimum 120 s gap · 4 breaks/hour cap · 15 % ad-load ceiling · emotional climax rejected.",
    },
    {
      k: "What to show",
      v: "MiniLM similarity against brand target_contexts — minus any brand whose negative_contexts match the scene.",
    },
  ];
  return (
    <section id="how" className="mx-auto max-w-7xl px-6 py-20">
      <div className="mb-10 flex items-end justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Three decisions, one pipeline</h2>
        <a href="#demo" className="text-sm text-rose hover:underline">Skip to demo →</a>
      </div>
      <div className="grid gap-5 md:grid-cols-3">
        {items.map((it, i) => (
          <div key={it.k} className="card p-6">
            <div className="text-xs uppercase tracking-widest text-rose">0{i + 1}</div>
            <h3 className="mt-2 text-xl font-bold">{it.k}</h3>
            <p className="mt-3 text-sm leading-relaxed text-white/60">{it.v}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
