"use client";

const items = [
  ["Where", "Completed scene, sentence, and dialogue pause."],
  ["Whether", "Hard safety, pacing, and ad-load rules."],
  ["What", "Data-driven brand match with negative blocks."],
];

export default function HowItWorks() {
  return <section id="how" className="mx-auto max-w-7xl px-6 py-10">
    <div className="section-kicker">How placement works</div>
    <div className="mt-4 grid gap-3 md:grid-cols-3">
      {items.map(([title, text]) => <div key={title} className="flex gap-3 border-t border-white/10 py-4"><span className="font-mono text-xs text-amber">{title}</span><p className="text-sm text-white/55">{text}</p></div>)}
    </div>
  </section>;
}
