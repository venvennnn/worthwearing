import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RecommendationBadge } from "./RecommendationBadge";

describe("RecommendationBadge", () => {
  it("renders Worth It in green language", () => {
    render(<RecommendationBadge recommendation="worth_it" label="Worth It" />);
    expect(screen.getByText("Worth It")).toBeInTheDocument();
    expect(screen.getByText(/wardrobe evidence/i)).toBeInTheDocument();
  });

  it("renders Skip It", () => {
    render(<RecommendationBadge recommendation="skip_it" label="Skip It" />);
    expect(screen.getByText("Skip It")).toBeInTheDocument();
  });
});
