"use client";

type Artifact = { key: string; label: string; href: string; tone?: "rose" | "amber" | "emerald" };

type Props = {
  artifacts: Artifact[];
};

const ICON: Record<string, JSX.Element> = {
  scenes: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16v4H4zM4 10h16v4H4zM4 16h10v4H4z"/></svg>
  ),
  debug: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2 4 5v7c0 5 3.5 9.7 8 10 4.5-.3 8-5 8-10V5z"/></svg>
  ),
  vmap: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h18v18H3z M3 9h18 M9 3v18"/></svg>
  ),
  playback: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
  ),
  transcript: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16v2H4zm0 5h16v2H4zm0 5h11v2H4z"/></svg>
  ),
};

export default function ArtifactCards({ artifacts }: Props) {
  if (!artifacts.length) return null;
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {artifacts.map((a) => (
        <div key={a.key} className="card relative overflow-hidden p-5">
          <div className="absolute -top-px left-5 right-5 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-white/5 text-rose">
              {ICON[a.key] ?? ICON.debug}
            </span>
            <div>
              <div className="text-[11px] uppercase tracking-widest text-white/40">Artifact</div>
              <div className="font-semibold">{a.label}</div>
            </div>
          </div>
          <div className="mt-5 flex gap-2">
            <a href={a.href} target="_blank" rel="noreferrer" className="btn-ghost rounded-md px-3 py-1.5 text-xs">View</a>
            <a href={a.href} download className="btn-primary rounded-md px-3 py-1.5 text-xs">Download</a>
          </div>
        </div>
      ))}
    </div>
  );
}
