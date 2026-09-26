"use client";

type Artifact = { key: string; label: string; href: string };

type Props = {
  artifacts: Artifact[];
};

export default function ArtifactCards({ artifacts }: Props) {
  if (!artifacts.length) return null;
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {artifacts.map((a) => (
        <div
          key={a.key}
          className="brand-card rounded-xl border border-white/10 p-4 text-sm text-white shadow"
        >
          <div className="text-xs uppercase tracking-widest text-white/50">{a.label}</div>
          <div className="mt-3 flex gap-2">
            <a
              href={a.href}
              target="_blank"
              rel="noreferrer"
              className="rounded-md bg-white/10 px-3 py-1.5 text-xs text-white hover:bg-white/20"
            >
              View
            </a>
            <a
              href={a.href}
              download
              className="rounded-md bg-rose px-3 py-1.5 text-xs text-white hover:bg-rose/80"
            >
              Download
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
