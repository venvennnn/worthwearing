import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FactorBreakdown } from "./FactorBreakdown";

const factors = [
  {
    key: "duplication",
    label: "Duplication",
    value: 1,
    weight: 0.3,
    contribution: 0.3,
    explanation: "Matches the leather jacket.",
  },
  {
    key: "style_isolation",
    label: "Style isolation",
    value: 0.8,
    weight: 0.25,
    contribution: 0.2,
    explanation: "Few compatible items.",
  },
];

describe("FactorBreakdown", () => {
  it("lists weighted contributions", () => {
    render(<FactorBreakdown factors={factors} />);
    expect(screen.getByText(/30% × 1.00 = 30.0 pts/)).toBeInTheDocument();
    expect(screen.getByText(/25% × 0.80 = 20.0 pts/)).toBeInTheDocument();
  });
});
