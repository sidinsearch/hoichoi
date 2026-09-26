"use client";

import { useEffect, useState } from "react";
import { useRef } from "react";

import Header from "@/components/Header";
import Hero from "@/components/Hero";
import HowItWorks from "@/components/HowItWorks";
import FeatureGrid from "@/components/FeatureGrid";
import UploadPanel from "@/components/UploadPanel";
import ResultsPanel from "@/components/ResultsPanel";
import ArtifactCards from "@/components/ArtifactCards";
import VideoPlayer from "@/components/VideoPlayer";
import BreakDetails from "@/components/BreakDetails";
import ProgressPanel from "@/components/ProgressPanel";
import TranscriptPanel from "@/components/TranscriptPanel";
import Footer from "@/components/Footer";
import type { BreakInfo } from "@/lib/playback";

const STAGES = [
  "uploading",
  "extracting_audio",
  "transcribing_bengali",
  "detecting_shots",
  "analyzing_visual_context",
  "building_scenes",
  "finding_break_candidates",
  "applying_safety_rules",
  "matching_brands",
  "generating_outputs",
  "ready",
];

type Status = "idle" | "queued" | "processing" | "completed" | "failed";

export default function Page() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [stage, setStage] = useState<string | undefined>(undefined);
  const [progress, setProgress] = useState<number>(0);
  const [breaks, setBreaks] = useState<BreakInfo[]>([]);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [scenes, setScenes] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastTriggeredBreak, setLastTriggeredBreak] = useState<BreakInfo | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const analyze = async (video: File, brandJson: File) => {
    setStatus("queued");
    setStage("uploading");
    setProgress(2);
    setBreaks([]);
    setError(null);
    setScenes([]);
    setVideoUrl(null);

    const fd = new FormData();
    fd.append("video", video);
    fd.append("brand_json", brandJson);

    try {
      const r = await fetch("/api/analyze", { method: "POST", body: fd });
      if (!r.ok) {
        const t = await r.text();
        throw new Error(`Upload failed: ${r.status} ${t}`);
      }
      const { job_id } = await r.json();
      setJobId(job_id);
      poll(job_id);
    } catch (e: any) {
      setError(e?.message ?? "Unknown error");
      setStatus("failed");
    }
  };

  const poll = async (id: string) => {
    const ctrl = new AbortController();
    abortRef.current?.abort();
    abortRef.current = ctrl;
    const url = `/api/jobs/${id}`;
    const tick = async () => {
      try {
        const r = await fetch(url, { signal: ctrl.signal });
        if (!r.ok) {
          setError(`Polling failed: ${r.status}`);
          setStatus("failed");
          return;
        }
        const s = await r.json();
        setStatus(s.status);
        setStage(s.stage);
        setProgress(s.progress ?? 0);
        if (s.status === "completed" || s.status === "failed") {
          if (s.status === "failed") setError(s.error || "Job failed");
          // Pull artifacts
          try {
            const pb = await fetch(`/api/jobs/${id}/playback`);
            if (pb.ok) {
              const p = await pb.json();
              setBreaks(p.breaks ?? []);
              setVideoUrl(p.video_url ?? `/api/jobs/${id}/video`);
            }
            const sc = await fetch(`/api/jobs/${id}/scenes`);
            if (sc.ok) {
              const sd = await sc.json();
              setScenes(sd.scenes ?? []);
            }
          } catch {}
          return;
        }
        setTimeout(tick, 1500);
      } catch (e: any) {
        if (e?.name !== "AbortError") {
          setError("Lost connection to backend");
          setStatus("failed");
        }
      }
    };
    tick();
  };

  useEffect(() => () => abortRef.current?.abort(), []);

  const isLoading = status === "queued" || status === "processing";

  const artifacts = jobId
    ? [
        { key: "scenes", label: "scenes.json", href: `/api/jobs/${jobId}/scenes` },
        { key: "debug", label: "debug.json", href: `/api/jobs/${jobId}/debug` },
        { key: "vmap", label: "vmap.xml", href: `/api/jobs/${jobId}/vmap` },
      ]
    : [];

  return (
    <>
      <Header />
      <main>
        <Hero />
        <FeatureGrid />
        <HowItWorks />

        <section id="demo" className="mx-auto max-w-7xl px-6 pb-20">
          <div className="mb-8">
            <h2 className="text-3xl font-bold tracking-tight">Demo</h2>
            <p className="mt-2 text-sm text-white/60">
              Upload a Bengali drama + the synthetic brand catalogue. The pipeline
              will run end-to-end and stream live progress.
            </p>
          </div>

          <div className="grid gap-8 lg:grid-cols-[1.4fr_1fr]">
            <div className="grid gap-6">
              <UploadPanel onAnalyze={analyze} disabled={isLoading} loading={isLoading} />
              {jobId && (
                <ResultsPanel
                  status={status}
                  stage={stage}
                  progress={progress}
                  summary={
                    status === "completed"
                      ? {
                          scenes: scenes.length,
                          candidates: breaks.length,
                          accepted: breaks.length,
                          rejected: 0,
                        }
                      : undefined
                  }
                />
              )}
              {(isLoading) && <ProgressPanel stages={STAGES} current={stage} />}
              {error && (
                <div className="card border border-rose/30 bg-rose/10 p-4 text-sm text-rose">
                  <span className="font-semibold">Error:</span> {error}
                </div>
              )}
              {status === "completed" && videoUrl && (
                <>
                  <VideoPlayer
                    src={videoUrl}
                    breaks={breaks}
                    onBreakTriggered={(b) => setLastTriggeredBreak(b)}
                  />
                  <BreakDetails breaks={breaks} scenes={scenes} />
                  <TranscriptPanel scenes={scenes} breaks={breaks} />
                </>
              )}
            </div>

            <aside className="grid gap-6 lg:sticky lg:top-24 lg:h-fit">
              <div className="card p-5">
                <div className="text-[11px] uppercase tracking-widest text-white/40">Connection</div>
                <div className="mt-1 flex items-center gap-2 text-sm">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span className="text-white/80">Backend online</span>
                </div>
                <div className="mt-3 text-xs text-white/40">
                  POST /api/analyze · GET /api/jobs/{`{id}`}
                </div>
              </div>

              <div id="artifacts" className="grid gap-4">
                <div className="text-[11px] uppercase tracking-widest text-white/40">Artifacts</div>
                <ArtifactCards artifacts={artifacts} />
              </div>

              {lastTriggeredBreak && (
                <div className="card p-5">
                  <div className="text-[11px] uppercase tracking-widest text-rose">Now playing</div>
                  <div className="mt-1 text-lg font-bold">{lastTriggeredBreak.display_name}</div>
                  <div className="text-sm text-white/60">{lastTriggeredBreak.category}</div>
                  <p className="mt-3 rounded-md bg-white/5 p-3 text-xs italic text-white/70">
                    "{lastTriggeredBreak.context_summary}"
                  </p>
                </div>
              )}
            </aside>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
