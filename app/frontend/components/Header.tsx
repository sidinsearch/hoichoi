"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  const isHIW = pathname === "/how-it-works";
  return (
    <header className={`sticky top-0 z-40 transition-all duration-300 ${scrolled ? "bg-[rgba(7,9,13,.85)] border-b border-white/[.08] backdrop-blur-[18px]" : ""}`}>
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <a href="/" className="flex items-center gap-3 min-h-0" aria-label="hoichoi home">
          <div className="brand-mark grid place-items-center">
            <svg viewBox="0 0 24 24" width="17" height="17" fill="currentColor" aria-hidden>
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          <div>
            <div className="text-[.88rem] font-bold tracking-tight leading-tight">
              hoichoi <span className="text-[var(--rose)]">·</span> Ad Intelligence
            </div>
            <div className="text-[.62rem] uppercase tracking-widest text-[var(--text-2)] leading-tight mt-0.5">
              Hackathon&apos;26 — Problem 1
            </div>
          </div>
        </a>
        <nav className="hidden items-center gap-6 md:flex" aria-label="Primary">
          <a href="/how-it-works" className={`nav-link text-sm${isHIW ? " !text-[var(--text-0)]" : ""}`} aria-current={isHIW ? "page" : undefined}>How it works</a>
          <a href={isHIW ? "/#demo" : "#demo"} className="nav-link text-sm">Demo</a>
          <a href="https://github.com/sidinsearch/hoichoi" target="_blank" rel="noreferrer" className="btn-ghost rounded-lg px-4 py-2 text-xs">GitHub ↗</a>
        </nav>
        <div className="flex items-center gap-2 md:hidden">
          <a href="/how-it-works" className="btn-ghost rounded-lg px-3 py-2 text-xs">How it works</a>
          <a href="https://github.com/sidinsearch/hoichoi" target="_blank" rel="noreferrer" className="btn-ghost rounded-lg px-3 py-2 text-xs">GitHub</a>
        </div>
      </div>
    </header>
  );
}
