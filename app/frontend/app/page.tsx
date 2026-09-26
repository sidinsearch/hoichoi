"use client";

import { useEffect, useState } from "react";
import { useRef } from "react";

import Header from "@/components/Header";
import UploadPanel from "@/components/UploadPanel";
import ResourcePicker from "@/components/ResourcePicker";
import BrandPicker from "@/components/BrandPicker";
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
  "transcribing_audio",
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
  const [language, setLanguage] = useState("bn");
  const [brandFile, setBrandFile] = useState<File | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const resetAnalysis = () => { setStatus("queued"); setStage("uploading"); setProgress(2); setBreaks([]); setError(null); setScenes([]); setVideoUrl(null); };

  const analyzeResource = async (resourceName: string, selectedLanguage = language) => {
    resetAnalysis();
    const fd = new FormData();
    fd.append("resource_name", resourceName); fd.append("brand_name", "brands.json"); fd.append("language", selectedLanguage);
    if (brandFile) fd.append("brand_json", brandFile);
    try {
      const r = await fetch("/api/analyze-resource", { method: "POST", body: fd });
      if (!r.ok) throw new Error(`Resource analysis failed: ${r.status}`);
      const { job_id } = await r.json(); setJobId(job_id); poll(job_id);
    } catch (e: any) { setError(e?.message ?? "Resource analysis failed"); setStatus("failed"); }
  };

  const analyze = async (video: File, language: string) => {
    const fd = new FormData();
    fd.append("video", video);
    if (brandFile) fd.append("brand_json", brandFile); else {
      const defaultBrand = await fetch("/api/resources/brands.json").then(r => r.blob());
      fd.append("brand_json", new File([defaultBrand], "brands.json", { type: "application/json" }));
    }
    fd.append("language", language);

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
        { key: "playback", label: "playback.json", href: `/api/jobs/${jobId}/playback` },
        { key: "transcript", label: "transcript.json", href: `/api/jobs/${jobId}/transcript` },
      ]
    : [];

  return (
    <>
      <Header />
      <main className="app-shell">
        <section id="demo" className="mx-auto max-w-6xl px-6 pb-24 pt-16 lg:px-10">
          <div className="demo-heading mb-12 mx-auto text-center">
            <div className="section-kicker justify-center flex items-center"><span className="status-live" />Live demo · deterministic ad placement</div>
            <h1 className="mt-4">Turn long-form video into <br /><em>safe ad moments.</em></h1>
            <p className="mt-5 max-w-2xl mx-auto">Select a bundled episode or upload your own. The system analyzes scenes, applies safety rules, matches brands, and gives you a playable result.</p>
          </div>
          <div className="workspace">
            <div className="workspace-column">
              <div className="panel-topline"><span className="panel-number">01 / INPUT</span></div>
              <BrandPicker disabled={isLoading} onChange={setBrandFile} />
              <ResourcePicker onAnalyze={analyzeResource} language={language} onLanguageChange={setLanguage} disabled={isLoading} />
              <div className="flex items-center gap-3 px-1 text-[10px] uppercase tracking-[.2em] text-[var(--text-2)]"><span className="h-px flex-1 bg-white/10" />or upload<span className="h-px flex-1 bg-white/10" /></div>
              <UploadPanel onAnalyze={analyze} disabled={isLoading} loading={isLoading} />
            </div>
            <div className="workspace-column workspace-results">
              <div className="panel-topline"><span className="panel-number">02 / RESULTS</span></div>
              {jobId && <ResultsPanel status={status} stage={stage} progress={progress} summary={status === "completed" ? { scenes: scenes.length, candidates: breaks.length, accepted: breaks.length, rejected: 0 } : undefined} />}
              {isLoading && <ProgressPanel stages={STAGES} current={stage} />}
              {error && <div className="card border border-rose/30 bg-rose/10 p-4 text-sm text-rose"><span className="font-semibold">Error:</span> {error}</div>}
              {status === "completed" && videoUrl && <><VideoPlayer src={videoUrl} breaks={breaks} onBreakTriggered={b => setLastTriggeredBreak(b)} /><BreakDetails breaks={breaks} scenes={scenes} /><TranscriptPanel scenes={scenes} breaks={breaks} /></>}
              {lastTriggeredBreak && <div className="card p-5"><div className="section-kicker">Now playing</div><div className="mt-1 text-lg font-semibold">{lastTriggeredBreak.display_name}</div><p className="mt-2 text-sm text-white/55">{lastTriggeredBreak.context_summary}</p></div>}
              {jobId && <div id="artifacts" className="grid gap-3"><div className="section-kicker">Generated files</div><ArtifactCards artifacts={artifacts} /></div>}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
