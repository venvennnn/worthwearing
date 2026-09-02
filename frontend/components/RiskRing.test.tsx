import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RiskRing } from "./RiskRing";

describe("RiskRing", () => {
  it("exposes the numeric risk", () => {
    render(<RiskRing value={76} />);
    expect(screen.getByLabelText("Return Risk 76")).toBeInTheDocument();
    expect(screen.getByText("76")).toBeInTheDocument();
  });
});
