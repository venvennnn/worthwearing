"use client";

import type { CompatibleOutfit } from "@/lib/types";
import { assetSrc } from "@/lib/copy";

type Props = {
  outfits: CompatibleOutfit[];
};

export function OutfitCarousel({ outfits }: Props) {
  if (!outfits.length) {
    return <p className="text-sm text-[#5C5C5C]">No compatible outfits under the current rules.</p>;
  }
  return (
    <div className="flex gap-3 overflow-x-auto pb-2" data-testid="outfit-carousel">
      {outfits.map((outfit) => (
        <article
          key={outfit.id}
          className="min-w-[220px] rounded-2xl border border-[#EAEAEA] bg-[#FAFAFA] p-3"
        >
          <p className="text-[11px] uppercase tracking-[0.16em] text-[#5C5C5C]">
            {outfit.occasion}
          </p>
          <div className="mt-2 flex gap-1">
            {outfit.pieces.map((piece) => (
              <img
                key={piece.item_id}
                src={assetSrc(piece.image_url)}
                alt={piece.name}
                className="h-16 w-12 rounded-lg object-cover bg-white"
              />
            ))}
          </div>
          <p className="mt-2 text-xs text-[#5C5C5C]">{outfit.rationale}</p>
        </article>
      ))}
    </div>
  );
}
