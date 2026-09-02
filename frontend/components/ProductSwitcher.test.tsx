import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProductSwitcher } from "./ProductSwitcher";
import type { CandidateProduct } from "@/lib/types";

const candidates: CandidateProduct[] = [
  {
    id: "jacket-a",
    name: "Noir Moto Jacket",
    short_label: "Jacket A",
    demo_role: "duplicative",
    category: "outerwear",
    subcategory: "leather_jacket",
    colors: ["black"],
    style_tags: ["edgy"],
    season_tags: ["fall"],
    occasion_tags: ["weekend"],
    layer: "outer",
    image_url: "/assets/jacket-a-product.png",
    prepared_try_on_url: "/assets/jacket-a-tryon.png",
    prepared_try_on_alt: "try on a",
    scenario_assets: [],
  },
  {
    id: "jacket-b",
    name: "Harbor Field Jacket",
    short_label: "Jacket B",
    demo_role: "versatile",
    category: "outerwear",
    subcategory: "field_jacket",
    colors: ["navy"],
    style_tags: ["classic"],
    season_tags: ["fall"],
    occasion_tags: ["work"],
    layer: "outer",
    image_url: "/assets/jacket-b-product.png",
    prepared_try_on_url: "/assets/jacket-b-tryon.png",
    prepared_try_on_alt: "try on b",
    scenario_assets: [],
  },
];

describe("ProductSwitcher", () => {
  it("selects jacket cards", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <ProductSwitcher
        candidates={candidates}
        selectedId="jacket-a"
        onSelect={onSelect}
      />
    );
    expect(screen.getByRole("radio", { name: /jacket a/i })).toHaveAttribute(
      "aria-checked",
      "true"
    );
    await user.click(screen.getByRole("radio", { name: /jacket b/i }));
    expect(onSelect).toHaveBeenCalledWith("jacket-b");
  });
});
