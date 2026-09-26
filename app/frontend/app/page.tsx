"use client";

import { useEffect, useState } from "react";
import UploadPanel from "@/components/UploadPanel";
import ResultsPanel from "@/components/ResultsPanel";
import ArtifactCards from "@/components/ArtifactCards";
import VideoPlayer from "@/components/VideoPlayer";
import BreakDetails from "@/components/BreakDetails";
import ProgressPanel from "@/components/ProgressPanel";
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

export default function Page() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [stage, setStage] = useState<string | undefined>(undefined);
  const [progress, setProgress] = useState<number>(0);
  const [breaks, setBreaks] = useState<BreakInfo[]>([]);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [scenes, setScenes] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

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
    const r = await fetch("/api/analyze", { method: "POST", body: fd });
    if (!r.ok) {
      const t = await r.text();
      setError(`Upload failed: ${r.status} ${t}`);
      setStatus("failed");
      return;
    }
    const { job_id } = await r.json();
    setJobId(job_id);
    poll(job_id);
  };

  const poll = async (id: string) => {
    const url = `/api/jobs/${id}`;
    let ticker = 0;
    while (ticker < 1200) {
      const r = await fetch(url);
      if (!r.ok) {
        setError(`Polling failed: ${r.status}`);
        return;
      }
      const s = await r.json();
      setStatus(s.status);
      setStage(s.stage);
      setProgress(s.progress ?? 0);
      if (s.status === "completed" || s.status === "failed") {
        if (s.status === "failed") setError(s.error || "Job failed");
        break;
      }
      await new Promise((res) => setTimeout(res, 1500));
      ticker += 1;
    }
    // Once completed, fetch playback
    try {
      const pb = await fetch(`/api/jobs/${id}/playback`);
      if (pb.ok) {
        const p = await pb.json();
        setBreaks(p.breaks ?? []);
        setVideoUrl(p.video_url ?? `/api/jobs/${id}/video`);
      }
      const sc = await fetch(`/api/jobs/${id}/scenes`);
      if (sc.ok) {
        const s = await sc.json();
        setScenes(s.scenes ?? []);
      }
    } catch (e) {
      // ignore
    }
  };

  const artifacts = jobId
    ? [
        { key: "scenes", label: "scenes.json", href: `/api/jobs/${jobId}/scenes` },
        { key: "debug", label: "debug.json", href: `/api/jobs/${jobId}/debug` },
        { key: "vmap", label: "vmap.xml", href: `/api/jobs/${jobId}/vmap` },
      ]
    : [];

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            hoichoi <span className="text-rose">·</span> Context-Aware Ad Intelligence
          </h1>
          <p className="mt-1 text-sm text-white/50">
            Semantic scenes → safe breaks → brand-safe placement. Source video is never modified.
          </p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/60">
          Hackathon'26 — Problem 1
        </span>
      </header>

      <section className="grid gap-8">
        <UploadPanel onAnalyze={analyze} disabled={status === "queued" || status === "processing"} />

        <ResultsPanel
          jobId={jobId}
          videoUrl={videoUrl}
          breaks={breaks}
          status={status}
          stage={stage}
          progress={progress}
        />

        {(status === "processing" || status === "queued") && (
          <ProgressPanel stages={STAGES} current={stage} />
        )}

        {error && (
          <div className="rounded-lg border border-rose/50 bg-rose/10 p-4 text-sm text-rose">
            {error}
          </div>
        )}

        {status === "completed" && videoUrl && (
          <section className="grid gap-6">
            <VideoPlayer src={videoUrl} breaks={breaks} />
            <BreakDetails breaks={breaks} />
            {scenes.length > 0 && (
              <div className="rounded-2xl border border-white/10 bg-carbon p-4">
                <div className="mb-2 text-xs uppercase tracking-widest text-white/40">
                  Scenes ({scenes.length})
                </div>
                <ul className="grid gap-1 text-xs">
                  {scenes.slice(0, 25).map((sc: any) => (
                    <li key={sc.scene_id} className="font-mono text-white/70">
                      {sc.scene_id} · {sc.start_sec.toFixed(1)}s → {sc.end_sec.toFixed(1)}s ·{" "}
                      {sc.context?.activities?.join(", ") || "no activity"}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        <ArtifactCards artifacts={artifacts} />
      </section>

      <footer className="mt-16 text-center text-xs text-white/30">
        hoichoi Hackathon'26 · built end-to-end with multimodal AI · brands are data, never code
      </footer>
    </main>
  );
}
