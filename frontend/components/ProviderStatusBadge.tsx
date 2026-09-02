"use client";

import type { ProviderMode } from "@/lib/types";

type Props = {
  mode: ProviderMode;
  label?: string;
};

export function ProviderStatusBadge({ mode, label }: Props) {
  const text =
    label ||
    (mode === "live" ? "Live API" : mode === "demo" ? "Prepared demo" : "Unavailable");
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-[#EAEAEA] bg-white px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-[#5C5C5C]"
      data-testid="provider-badge"
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          mode === "live" ? "bg-[#0F7B4B]" : mode === "demo" ? "bg-[#B45309]" : "bg-[#B42318]"
        }`}
        aria-hidden
      />
      {text}
    </span>
  );
}
