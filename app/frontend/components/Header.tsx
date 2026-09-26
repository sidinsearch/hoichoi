"use client";
import { useEffect, useState } from "react";

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <header
      className={`sticky top-0 z-40 transition-all duration-300 ${
        scrolled ? "backdrop-blur-md bg-black/40 border-b border-white/5" : ""
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="brand-mark">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden>
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          <div>
            <div className="text-base font-bold tracking-tight">
              hoichoi <span className="text-rose">·</span> Ad Intelligence
            </div>
            <div className="text-[11px] uppercase tracking-widest text-white/40">
              Hackathon'26 — Problem 1
            </div>
          </div>
        </div>
        <nav className="hidden items-center gap-7 text-sm md:flex">
          <a href="#work" className="nav-link">How it works</a>
          <a href="#demo" className="nav-link">Demo</a>
          <a href="#artifacts" className="nav-link">Artifacts</a>
          <a
            href="https://github.com/sidinsearch/hoichoi"
            target="_blank" rel="noreferrer"
            className="btn-ghost rounded-md px-3 py-1.5 text-xs"
          >
            GitHub ↗
          </a>
        </nav>
      </div>
    </header>
  );
}
