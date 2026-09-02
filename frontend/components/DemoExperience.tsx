"use client";

import { useEffect, useMemo, useState } from "react";
import { AnalysisProgress } from "@/components/AnalysisProgress";
import { CostPerWearCard } from "@/components/CostPerWearCard";
import { FactorBreakdown } from "@/components/FactorBreakdown";
import { MethodologyDrawer } from "@/components/MethodologyDrawer";
import { OutfitCarousel } from "@/components/OutfitCarousel";
import { ProductSwitcher } from "@/components/ProductSwitcher";
import { RecommendationBadge } from "@/components/RecommendationBadge";
import { RetailerValuePanel } from "@/components/RetailerValuePanel";
import { RiskRing } from "@/components/RiskRing";
import { TryOnStage } from "@/components/TryOnStage";
import { WardrobeMatchList } from "@/components/WardrobeMatchList";
import {
  analyzeCandidate,
  getHealth,
  getTryOn,
  startTryOn,
  usePreparedFallback,
} from "@/lib/api";
import { assetSrc } from "@/lib/copy";
import type {
  AnalysisResult,
  CandidateProduct,
  DemoPayload,
  HealthResponse,
  TryOnJob,
} from "@/lib/types";

const LIVE_TIMEOUT_MS = 20_000;

type Props = {
  demo: DemoPayload;
};

export function DemoExperience({ demo }: Props) {
  const [selectedId, setSelectedId] = useState(demo.candidates[0]?.id ?? "jacket-a");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [analyses, setAnalyses] = useState<Record<string, AnalysisResult>>({});
  const [jobs, setJobs] = useState<Record<string, TryOnJob>>({});
  const [prepared, setPrepared] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);
  const [timedOut, setTimedOut] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [whyOpen, setWhyOpen] = useState(false);
  const [scenarioId, setScenarioId] = useState<string | null>(null);
  const [previousId, setPreviousId] = useState<string | null>(null);

  const candidate = useMemo(
    () => demo.candidates.find((item) => item.id === selectedId) as CandidateProduct,
    [demo.candidates, selectedId]
  );
  const analysis = analyses[selectedId];
  const job = jobs[selectedId] ?? null;
  const previous = previousId ? analyses[previousId] : undefined;

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    if (!busy) return;
    const timer = window.setInterval(() => {
      setStep((current) => (current < 3 ? current + 1 : current));
    }, 700);
    return () => window.clearInterval(timer);
  }, [busy]);

  async function pollTryOn(jobId: string, startedAt: number): Promise<TryOnJob> {
    let current = await getTryOn(jobId);
    while (current.status === "queued" || current.status === "processing") {
      if (Date.now() - startedAt > LIVE_TIMEOUT_MS) {
        setTimedOut(true);
        return current;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 400));
      current = await getTryOn(jobId);
    }
    return current;
  }

  async function runAnalysis() {
    setBusy(true);
    setError(null);
    setTimedOut(false);
    setStep(0);
    setScenarioId(null);
    setWhyOpen(false);
    try {
      const startedAt = Date.now();
      const [analysisResult, tryOnJob] = await Promise.all([
        analyzeCandidate(candidate.id),
        startTryOn(candidate.id, demo.shopper.id),
      ]);
      setAnalyses((current) => ({ ...current, [candidate.id]: analysisResult }));
      setJobs((current) => ({ ...current, [candidate.id]: tryOnJob }));
      if (tryOnJob.status === "failed") {
        setTimedOut(tryOnJob.error_category === "timeout");
        setStep(3);
        return;
      }
      const finished = await pollTryOn(tryOnJob.job_id, startedAt);
      setJobs((current) => ({ ...current, [candidate.id]: finished }));
      if (finished.provider === "demo") {
        setPrepared((current) => ({ ...current, [candidate.id]: true }));
      }
      if (finished.status === "failed") {
        setTimedOut(finished.error_category === "timeout");
      }
      setStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
      setJobs((current) => ({
        ...current,
        [candidate.id]: {
          job_id: current[candidate.id]?.job_id ?? `failed-${candidate.id}`,
          status: "failed",
          provider: "live",
          prepared_fallback_available: true,
          prepared_fallback_url: candidate.prepared_try_on_url,
          error_category: "network",
          error_message: "Live try-on is unavailable.",
        },
      }));
    } finally {
      setBusy(false);
    }
  }

  async function applyPrepared() {
    const currentJob = jobs[candidate.id];
    try {
      if (currentJob?.job_id && !currentJob.job_id.startsWith("failed-")) {
        const fallback = await usePreparedFallback(currentJob.job_id);
        setJobs((current) => ({ ...current, [candidate.id]: fallback }));
        setPrepared((current) => ({ ...current, [candidate.id]: true }));
        setTimedOut(false);
        return;
      }
    } catch {
      // Fall through to the labeled local asset.
    }
    setJobs((current) => ({
      ...current,
      [candidate.id]: {
        job_id: currentJob?.job_id ?? `demo-${candidate.id}`,
        status: "completed",
        provider: "demo",
        result_image_url: candidate.prepared_try_on_url,
        prepared_fallback_available: true,
        prepared_fallback_url: candidate.prepared_try_on_url,
      },
    }));
    setPrepared((current) => ({ ...current, [candidate.id]: true }));
    setTimedOut(false);
  }

  function selectProduct(id: string) {
    if (id === selectedId) return;
    setPreviousId(selectedId);
    setSelectedId(id);
    setScenarioId(null);
    setTimedOut(false);
    setError(null);
  }

  const scenarios =
    candidate.id === "jacket-b" ? candidate.scenario_assets : [];

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-[#EAEAEA] px-4 py-4 md:px-8">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-[#5C5C5C]">
              Product-page SDK
            </p>
            <h1 className="serif text-2xl text-[#111111]">WorthWearing</h1>
          </div>
          <p className="hidden max-w-md text-right text-sm text-[#5C5C5C] md:block">
            Virtual try-on shows whether it looks good. WorthWearing shows whether it
            deserves a place in your wardrobe.
          </p>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-8 px-4 py-6 lg:grid-cols-[3fr_2fr] md:px-8">
        <div className="flex flex-col gap-5">
          <TryOnStage
            shopper={demo.shopper}
            candidate={candidate}
            job={job}
            timedOut={timedOut}
            onUsePrepared={applyPrepared}
            usingPrepared={Boolean(prepared[candidate.id])}
            scenarios={scenarios}
            selectedScenarioId={scenarioId}
            onSelectScenario={setScenarioId}
            busy={busy}
          />
          <ProductSwitcher
            candidates={demo.candidates}
            selectedId={selectedId}
            onSelect={selectProduct}
            disabled={busy}
          />
          <button
            type="button"
            onClick={runAnalysis}
            disabled={busy}
            className="rounded-full bg-[#111111] px-5 py-3 text-sm text-white disabled:opacity-50"
            data-testid="try-with-wardrobe"
          >
            Try it with my wardrobe
          </button>
          <AnalysisProgress active={busy} stepIndex={step} />
          {error ? (
            <p className="rounded-2xl border border-[#EAEAEA] bg-[#FAFAFA] p-4 text-sm text-[#B42318]" role="alert">
              {error}
            </p>
          ) : null}
          <section>
            <p className="mb-2 text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
              {demo.shopper.name}’s closet · {demo.shopper.city}
            </p>
            <div className="flex gap-2 overflow-x-auto">
              {demo.closet.map((item) => (
                <figure key={item.id} className="w-16 shrink-0">
                  <img
                    src={assetSrc(item.image_url)}
                    alt={item.name}
                    className="h-16 w-16 rounded-xl border border-[#EAEAEA] object-cover bg-[#FAFAFA]"
                  />
                  <figcaption className="mt-1 line-clamp-2 text-[10px] text-[#5C5C5C]">
                    {item.name}
                  </figcaption>
                </figure>
              ))}
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-5">
          {analysis ? (
            <>
              <RecommendationBadge
                recommendation={analysis.recommendation}
                label={analysis.recommendation_label}
              />
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-[#EAEAEA] bg-[#FAFAFA] p-4">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
                    Worth Score
                  </p>
                  <p className="serif mt-1 text-3xl">{analysis.worth_score}</p>
                </div>
                <div className="rounded-2xl border border-[#EAEAEA] bg-[#FAFAFA] p-4">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
                    Wardrobe Compatibility
                  </p>
                  <p className="serif mt-1 text-3xl">{analysis.wardrobe_compatibility}</p>
                </div>
              </div>
              <RiskRing value={analysis.return_risk} />
              <p className="text-sm text-[#5C5C5C]">{analysis.summary}</p>
              <p className="text-sm text-[#111111]">
                Estimated outfits: {analysis.outfit_count}
              </p>
              <FactorBreakdown factors={analysis.factors} />
              <CostPerWearCard scenario={analysis.cost_per_wear} />
              <div>
                <p className="mb-2 text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
                  Supporting closet items
                </p>
                <WardrobeMatchList items={analysis.matched_items} />
              </div>
              <div>
                <p className="mb-2 text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
                  Compatible outfits
                </p>
                <OutfitCarousel outfits={analysis.outfits} />
              </div>
              <MethodologyDrawer
                result={analysis}
                open={whyOpen}
                onToggle={() => setWhyOpen((value) => !value)}
              />
              {previous && previous.candidate_id !== analysis.candidate_id ? (
                <div className="rounded-2xl border border-[#EAEAEA] bg-white p-4" data-testid="comparison">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
                    Before and after
                  </p>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-[#5C5C5C]">{previous.candidate_name}</p>
                      <p className="serif text-xl">{previous.recommendation_label}</p>
                      <p>Return Risk {previous.return_risk}</p>
                    </div>
                    <div>
                      <p className="text-[#5C5C5C]">{analysis.candidate_name}</p>
                      <p className="serif text-xl">{analysis.recommendation_label}</p>
                      <p>Return Risk {analysis.return_risk}</p>
                    </div>
                  </div>
                </div>
              ) : null}
            </>
          ) : (
            <div className="rounded-2xl border border-[#EAEAEA] bg-[#FAFAFA] p-6">
              <p className="serif text-2xl text-[#111111]">Wardrobe intelligence</p>
              <p className="mt-2 text-sm text-[#5C5C5C]">
                Select a jacket, then run try-on and scoring together. Recommendations are
                deterministic. This is a decision-support prototype, not a proven return model.
              </p>
              <div className="mt-4 h-40 animate-pulse rounded-xl bg-white" aria-hidden />
            </div>
          )}
          <RetailerValuePanel closeLine={demo.close_line} />
          {health?.mcp_active ? (
            <p className="text-xs text-[#5C5C5C]">MCP adapter active.</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
