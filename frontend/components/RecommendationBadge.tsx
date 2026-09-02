"use client";

import type { Recommendation } from "@/lib/types";
import { RECOMMENDATION_COPY } from "@/lib/copy";

type Props = {
  recommendation: Recommendation;
  label: string;
};

export function RecommendationBadge({ recommendation, label }: Props) {
  const copy = RECOMMENDATION_COPY[recommendation];
  return (
    <div data-testid="recommendation-badge">
      <p
        className="serif text-4xl tracking-tight"
        style={{ color: copy.color }}
      >
        {label}
      </p>
      <p className="mt-1 text-sm text-[#5C5C5C]">{copy.helper}</p>
    </div>
  );
}
