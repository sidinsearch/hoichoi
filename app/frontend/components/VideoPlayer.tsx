"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import type { BreakInfo } from "@/lib/playback";
import { nextPhase, seekBeforeBreak } from "@/lib/playback";

type Props = {
  src: string;
  breaks: BreakInfo[];
  onBreakTriggered?: (b: BreakInfo) => void;
};

function formatTs(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  return [h, m, sec].map((n) => String(n).padStart(2, "0")).join(":");
}

export default function VideoPlayer({ src, breaks, onBreakTriggered }: Props) {
  const ref = useRef<HTMLVideoElement>(null);
  const consumed = useRef<Set<string>>(new Set());
  const [phase, setPhase] = useState<"playing" | "ad" | "ended" | "loading">("loading");
  const [activeAd, setActiveAd] = useState<BreakInfo | null>(null);
  const [remaining, setRemaining] = useState<number>(0);
  const [now, setNow] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const intervalRef = useRef<number | null>(null);
  const adIdRef = useRef<string | null>(null);
  const adStartedAtRef = useRef<number | null>(null);
  const adResumeTimeRef = useRef<number | null>(null);
  const lastTimeRef = useRef(0);
  const [, forceAdTick] = useState(0);

  useEffect(() => {
    consumed.current = new Set();
    adIdRef.current = null;
    adStartedAtRef.current = null;
    adResumeTimeRef.current = null;
    if (intervalRef.current) window.clearInterval(intervalRef.current);
    intervalRef.current = null;
  }, [src]);

  const tickAd = useCallback(() => {
    setRemaining((s) => {
      const next = Math.max(0, s - 1);
      if (next === 0) {
        if (intervalRef.current) {
          window.clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        // adResumeTimeRef is a ref so always has the live value even in stale closure
        const resumeAt = adResumeTimeRef.current;
        const video = ref.current;
        if (video && resumeAt !== null) {
          video.currentTime = resumeAt;
          video.play().catch(() => undefined);
        } else if (video) {
          video.play().catch(() => undefined);
        }
        adResumeTimeRef.current = null;
        adIdRef.current = null;
        setPhase("playing");
        setActiveAd(null);
      }
      return next;
    });
  }, []);

  useEffect(() => {
    if (phase !== "ad" || !activeAd || adIdRef.current === activeAd.id) return;
    const v = ref.current;
    if (v) {
      v.pause();
      v.currentTime = activeAd.timestamp_sec;
    }
    adIdRef.current = activeAd.id;
    adStartedAtRef.current = Date.now();
    adResumeTimeRef.current = activeAd.timestamp_sec;
    setRemaining(activeAd.duration_sec);
    consumed.current.add(activeAd.id);
    onBreakTriggered?.(activeAd);
    if (intervalRef.current) window.clearInterval(intervalRef.current);
    intervalRef.current = window.setInterval(() => {
      forceAdTick((n) => n + 1);
      tickAd();
    }, 1000);
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [phase, activeAd, tickAd, onBreakTriggered]);

  const onTime = useCallback(() => {
    const v = ref.current;
    if (!v) return;
    setNow(v.currentTime);
    if (phase !== "playing") return;
    // Scrubbing backwards re-arms breaks ahead of the playhead so the demo can
    // be replayed without reloading the page.
    if (v.currentTime < lastTimeRef.current - 1) {
      for (const b of breaks) {
        if (b.timestamp_sec > v.currentTime) consumed.current.delete(b.id);
      }
    }
    lastTimeRef.current = v.currentTime;
    const next = nextPhase(v.currentTime, breaks, consumed.current, activeAd, remaining);
    if (next.kind === "ad") {
      setActiveAd(next.break);
      setPhase("ad");
    } else if (next.kind === "ended") {
      setPhase("ended");
    }
  }, [breaks, phase, activeAd, remaining]);

  const seekToBreak = (b: BreakInfo) => {
    const v = ref.current;
    if (!v) return;
    v.currentTime = seekBeforeBreak(b.timestamp_sec);
  };

  const pct = duration > 0 ? Math.min(100, (now / duration) * 100) : 0;

  return (
    <div className="card overflow-hidden p-3">
      <div className="relative overflow-hidden rounded-xl bg-black">
        <video
          ref={ref}
          src={src}
          controls
          playsInline
          className="w-full max-h-[62vh] bg-black"
          onTimeUpdate={onTime}
          onLoadedMetadata={(e) => {
            setDuration((e.target as HTMLVideoElement).duration || 0);
            setPhase("playing");
          }}
          onEnded={() => setPhase("ended")}
          preload="metadata"
        />

        {phase === "loading" && (
          <div className="absolute inset-0 z-20 grid place-items-center bg-black/60 backdrop-blur">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/15 border-t-rose" />
          </div>
        )}

        {phase === "ad" && activeAd && (
          <div className="ad-overlay absolute inset-0 z-30 grid place-items-center">
            <div className="w-full max-w-xl px-8 text-center text-white">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-[11px] uppercase tracking-[0.3em] text-white/70">
                <span className="h-1.5 w-1.5 rounded-full bg-rose pulse" />
                Advertisement
              </div>
              <h2 className="text-5xl font-bold leading-none tracking-tight md:text-6xl">
                {activeAd.display_name}
              </h2>
              <div className="mt-3 text-sm text-white/60 md:text-base">
                {activeAd.category}
              </div>
              <div className="mt-10 grid place-items-center">
                <div
                  className="grid h-28 w-28 place-items-center rounded-full border-2 border-white/15 font-mono text-4xl"
                  style={{ fontVariantNumeric: "tabular-nums" }}
                >
                  {remaining}s
                </div>
              </div>
              <div className="mt-8 max-w-md text-xs text-white/50">
                <span className="opacity-70">Selected for:</span>{" "}
                <span className="text-white/80">
                  {activeAd.context_summary || "scene match"}
                </span>
              </div>
              <div className="mx-auto mt-8 h-1 w-40 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full bg-rose"
                  style={{
                    width: `${Math.round(
                      ((activeAd.duration_sec - remaining) /
                        activeAd.duration_sec) * 100
                    )}%`,
                    transition: "width 1s linear",
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {phase === "ended" && (
          <div className="absolute inset-0 z-20 grid place-items-center bg-black/70 text-center">
            <div>
              <div className="text-3xl font-bold">Episode complete</div>
              <div className="mt-2 text-sm text-white/50">
                {breaks.length} virtual ad break{breaks.length === 1 ? "" : "s"} delivered
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="mt-4 px-2">
        <div className="timeline">
          <div className="timeline-fill" style={{ width: `${pct}%` }} />
          {breaks.map((b) => {
            const left = duration > 0 ? (b.timestamp_sec / duration) * 100 : 0;
            return (
              <button
                key={b.id}
                title={`${b.display_name} @ ${formatTs(b.timestamp_sec)}`}
                className="timeline-marker"
                style={{ left: `${Math.min(100, Math.max(0, left))}%` }}
                onClick={() => seekToBreak(b)}
                aria-label={`Seek to break for ${b.display_name}`}
              />
            );
          })}
        </div>
        <div className="mt-3 flex items-center justify-between font-mono text-xs text-white/50">
          <span>{formatTs(now)}</span>
          <span className="text-white/40">
            {breaks.length} break{breaks.length === 1 ? "" : "s"} scheduled
          </span>
          <span>{formatTs(duration)}</span>
        </div>
      </div>
    </div>
  );
}
