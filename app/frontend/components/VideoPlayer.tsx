"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import type { BreakInfo } from "@/lib/playback";
import { nextPhase, seekBeforeBreak } from "@/lib/playback";

type Props = {
  src: string;
  breaks: BreakInfo[];
  onBreakTriggered?: (b: BreakInfo) => void;
};

export default function VideoPlayer({ src, breaks, onBreakTriggered }: Props) {
  const ref = useRef<HTMLVideoElement>(null);
  const consumed = useRef<Set<string>>(new Set());
  const [phase, setPhase] = useState<"playing" | "ad" | "ended">("playing");
  const [activeAd, setActiveAd] = useState<BreakInfo | null>(null);
  const [remaining, setRemaining] = useState<number>(0);
  const [now, setNow] = useState<number>(0);
  const intervalRef = useRef<number | null>(null);

  // Reset consumed break set if the video src changes (new job).
  useEffect(() => {
    consumed.current = new Set();
  }, [src]);

  const tickAd = useCallback(() => {
    setRemaining((s) => {
      const next = Math.max(0, s - 1);
      if (next === 0) {
        if (intervalRef.current) {
          window.clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        setPhase("playing");
        setActiveAd(null);
        // Resume episode after a tick so React state settles
        setTimeout(() => ref.current?.play().catch(() => undefined), 50);
      }
      return next;
    });
  }, []);

  // Hook: when entering "ad" phase, pause video + start countdown
  useEffect(() => {
    if (phase === "ad" && activeAd) {
      const v = ref.current;
      if (v) {
        v.pause();
        v.currentTime = activeAd.timestamp_sec; // anchor
      }
      setRemaining(activeAd.duration_sec);
      consumed.current.add(activeAd.id);
      onBreakTriggered?.(activeAd);
      if (intervalRef.current) window.clearInterval(intervalRef.current);
      intervalRef.current = window.setInterval(tickAd, 1000);
      return () => {
        if (intervalRef.current) {
          window.clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    }
  }, [phase, activeAd, tickAd, onBreakTriggered]);

  // timeupdate → check whether we crossed a break boundary
  const onTime = useCallback(() => {
    const v = ref.current;
    if (!v) return;
    setNow(v.currentTime);
    if (phase !== "playing") return;

    const next = nextPhase(v.currentTime, breaks, consumed.current, activeAd, remaining);
    if (next.kind === "ad") {
      setActiveAd(next.break);
      setPhase("ad");
    } else if (next.kind === "ended") {
      setPhase("ended");
    }
  }, [breaks, phase, activeAd, remaining]);

  const handleSeek = (ts: number) => {
    const v = ref.current;
    if (!v) return;
    v.currentTime = ts;
  };

  const seekToBreak = (b: BreakInfo) => {
    handleSeek(seekBeforeBreak(b.timestamp_sec));
  };

  return (
    <div className="rounded-2xl border border-white/10 bg-carbon p-4">
      <div className="relative overflow-hidden rounded-xl bg-black">
        <video
          ref={ref}
          src={src}
          controls
          className="w-full max-h-[60vh]"
          onTimeUpdate={onTime}
          onEnded={() => setPhase("ended")}
          preload="metadata"
        />
        {phase === "ad" && activeAd && (
          <div className="ad-overlay absolute inset-0 z-30 flex flex-col items-center justify-center text-center text-white">
            <div className="mb-4 text-xs tracking-[0.4em] text-rose">ADVERTISEMENT</div>
            <div className="text-4xl font-bold tracking-tight md:text-6xl">{activeAd.display_name}</div>
            <div className="mt-2 text-sm text-white/70 md:text-base">{activeAd.category}</div>
            <div className="mt-8 inline-flex h-24 w-24 items-center justify-center rounded-full border border-white/20 text-3xl font-mono">
              {remaining}s
            </div>
            <div className="mt-4 max-w-md text-xs text-white/50">
              <span className="opacity-70">Contextually selected for:</span>{" "}
              <span className="text-white/80">{activeAd.context_summary || "scene match"}</span>
            </div>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="relative mt-4 h-2 rounded-full bg-white/10">
        <div
          className="absolute left-0 top-0 h-full rounded-full bg-rose"
          style={{ width: `${Math.min(100, (now / (ref.current?.duration || 1)) * 100)}%` }}
        />
        {breaks.map((b) => (
          <button
            key={b.id}
            title={`${b.display_name} @ ${b.timestamp_sec.toFixed(1)}s`}
            className="absolute top-0 z-10 h-full w-1.5 -translate-x-1/2 rounded-full bg-amber-400 hover:bg-amber-200"
            style={{ left: `${Math.min(100, (b.timestamp_sec / (ref.current?.duration || 1)) * 100)}%` }}
            onClick={() => seekToBreak(b)}
          />
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-white/60">
        <span>{now.toFixed(1)}s</span>
        <span>{breaks.length} ad break{breaks.length === 1 ? "" : "s"} planned</span>
      </div>
    </div>
  );
}
