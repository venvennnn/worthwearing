"use client";

import type { CandidateProduct, ScenarioAsset, Shopper, TryOnJob } from "@/lib/types";
import { assetSrc } from "@/lib/copy";
import { ProviderStatusBadge } from "./ProviderStatusBadge";

type Props = {
  shopper: Shopper;
  candidate: CandidateProduct;
  job: TryOnJob | null;
  timedOut: boolean;
  onUsePrepared: () => void;
  usingPrepared: boolean;
  scenarios: ScenarioAsset[];
  selectedScenarioId: string | null;
  onSelectScenario: (id: string | null) => void;
  busy: boolean;
};

export function TryOnStage({
  shopper,
  candidate,
  job,
  timedOut,
  onUsePrepared,
  usingPrepared,
  scenarios,
  selectedScenarioId,
  onSelectScenario,
  busy,
}: Props) {
  const selectedScenario = scenarios.find((item) => item.id === selectedScenarioId);
  const imageUrl =
    selectedScenario?.image_url ||
    job?.result_image_url ||
    shopper.photo_url;
  const alt =
    selectedScenario?.alt ||
    (job?.result_image_url
      ? `Virtual try-on of ${candidate.name} on ${shopper.name}`
      : shopper.photo_alt);
  const showFallbackCta =
    (timedOut || job?.status === "failed") && job?.prepared_fallback_available && !job.result_image_url;
  const providerMode = usingPrepared || job?.provider === "demo" ? "demo" : job?.provider || "demo";

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
          Perfect Corp try-on
        </p>
        <ProviderStatusBadge
          mode={providerMode}
          label={usingPrepared || job?.provider === "demo" ? "Prepared demo" : "Live API"}
        />
      </div>
      <div className="relative overflow-hidden rounded-3xl border border-[#EAEAEA] bg-white">
        {busy && !job?.result_image_url ? (
          <div
            className="absolute inset-0 z-10 bg-white/80"
            data-testid="tryon-skeleton"
            aria-hidden
          >
            <div className="h-full w-full animate-pulse bg-[#FAFAFA]" />
          </div>
        ) : null}
        <img
          src={assetSrc(imageUrl)}
          alt={alt}
          className="mx-auto max-h-[720px] w-full object-contain"
          data-testid="tryon-image"
        />
      </div>
      {showFallbackCta ? (
        <div className="rounded-2xl border border-[#EAEAEA] bg-[#FAFAFA] p-4">
          <p className="text-sm text-[#111111]">
            Live try-on {timedOut ? "exceeded 20 seconds" : "failed"}. No result was invented.
          </p>
          <button
            type="button"
            onClick={onUsePrepared}
            className="mt-3 rounded-full bg-[#111111] px-4 py-2 text-sm text-white"
            data-testid="use-prepared-demo"
          >
            Use prepared demo result
          </button>
        </div>
      ) : null}
      {scenarios.length > 0 ? (
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
            Occasion scenarios
          </p>
          <div className="flex gap-2 overflow-x-auto pb-1">
            <button
              type="button"
              onClick={() => onSelectScenario(null)}
              className={`shrink-0 rounded-xl border px-3 py-2 text-sm ${
                !selectedScenarioId ? "border-[#111111]" : "border-[#EAEAEA]"
              }`}
            >
              Studio try-on
            </button>
            {scenarios.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectScenario(item.id)}
                className={`shrink-0 overflow-hidden rounded-xl border ${
                  selectedScenarioId === item.id ? "border-[#111111]" : "border-[#EAEAEA]"
                }`}
              >
                <img
                  src={assetSrc(item.image_url)}
                  alt={item.alt}
                  className="h-20 w-16 object-cover"
                />
                <span className="block px-2 py-1 text-[11px]">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
