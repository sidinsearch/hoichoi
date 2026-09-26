"use client";

type Item = { k: string; v: string };

export default function FeatureGrid() {
  const items: Item[] = [
    { k: "Fast", v: "tiny Whisper int8 + lexical scene fusion. 3-5 minute E2E on a CPU laptop." },
    { k: "Safe", v: "Hard rules in Python: no mid-sentence, no active dialogue, negative-context hard-blocks." },
    { k: "Data-driven", v: "Brand I? Just add to brand.json. Zero Python changes." },
    { k: "Honest", v: "Every accepted/rejected break carries its reasons in debug.json." },
    { k: "Reversible", v: "Source video is never modified. Decisions render as a virtual black-screen overlay." },
    { k: "Standards", v: "Generates a well-formed VMAP 1.0 manifest with proper AdBreak timeOffset." },
  ];
  return (
    <section id="work" className="mx-auto max-w-7xl px-6 py-20">
      <h2 className="text-3xl font-bold tracking-tight">Built to a checklist, not a vibe</h2>
      <p className="mt-3 max-w-2xl text-sm text-white/60">
        Each claim above maps to a deterministic rule or a documented test. See
        <code className="mx-1 rounded bg-white/10 px-1 text-xs">tests/</code> and
        <code className="mx-1 rounded bg-white/10 px-1 text-xs">docs/MODEL_REGISTRY.md</code>.
      </p>
      <div className="mt-10 grid gap-3 md:grid-cols-3">
        {items.map((it) => (
          <div key={it.k} className="card p-5">
            <div className="text-rose">●</div>
            <div className="mt-2 text-lg font-semibold">{it.k}</div>
            <div className="mt-1 text-sm text-white/60">{it.v}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
