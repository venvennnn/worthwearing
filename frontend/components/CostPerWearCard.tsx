"use client";

import { useState } from "react";
import type { CostPerWearScenario } from "@/lib/types";

type Props = {
  scenario: CostPerWearScenario | null;
};

export function CostPerWearCard({ scenario }: Props) {
  const [open, setOpen] = useState(false);
  if (!scenario) {
    return (
      <p className="text-sm text-[#5C5C5C]">No price on this candidate, so CPW is omitted.</p>
    );
  }
  return (
    <div className="rounded-2xl border border-[#EAEAEA] bg-[#FAFAFA] p-4" data-testid="cpw-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
            Estimated CPW scenario
          </p>
          <p className="serif mt-1 text-3xl text-[#111111]">${scenario.estimated_cpw.toFixed(2)}</p>
          <p className="mt-1 text-sm text-[#5C5C5C]">
            ${scenario.price} ÷ {scenario.estimated_wears} wears over {scenario.horizon_months} months
          </p>
        </div>
        <button
          type="button"
          aria-expanded={open}
          aria-label="What estimated CPW scenario means"
          onClick={() => setOpen((value) => !value)}
          className="rounded-full border border-[#EAEAEA] bg-white px-2 py-1 text-xs text-[#111111]"
        >
          i
        </button>
      </div>
      {open ? (
        <div className="mt-3 text-xs text-[#5C5C5C]">
          <p>Formula: {scenario.formula}. This is a scenario, not a prediction.</p>
          <ul className="mt-2 list-disc space-y-1 pl-4">
            {scenario.assumptions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
