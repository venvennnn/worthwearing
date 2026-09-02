"use client";

import type { CandidateProduct } from "@/lib/types";
import { assetSrc } from "@/lib/copy";

type Props = {
  candidates: CandidateProduct[];
  selectedId: string;
  onSelect: (id: string) => void;
  disabled?: boolean;
};

export function ProductSwitcher({
  candidates,
  selectedId,
  onSelect,
  disabled,
}: Props) {
  return (
    <div className="grid grid-cols-2 gap-3" role="radiogroup" aria-label="Candidate jackets">
      {candidates.map((product) => {
        const selected = product.id === selectedId;
        return (
          <button
            key={product.id}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={disabled}
            onClick={() => onSelect(product.id)}
            className={`text-left rounded-2xl border bg-[#FAFAFA] p-3 transition-colors ${
              selected ? "border-[#111111]" : "border-[#EAEAEA] hover:border-[#C8C8C8]"
            } disabled:opacity-60`}
          >
            <div className="aspect-[3/4] overflow-hidden rounded-xl bg-white">
              <img
                src={assetSrc(product.image_url)}
                alt={`${product.short_label}: ${product.name}`}
                className="h-full w-full object-contain"
              />
            </div>
            <p className="mt-3 text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
              {product.short_label}
            </p>
            <p className="serif mt-1 text-lg leading-tight text-[#111111]">{product.name}</p>
            <p className="mt-1 text-sm text-[#5C5C5C]">
              {product.price != null ? `$${product.price}` : "Price on request"}
            </p>
          </button>
        );
      })}
    </div>
  );
}
