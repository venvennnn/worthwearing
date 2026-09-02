"use client";

import type { MatchedItem } from "@/lib/types";
import { assetSrc } from "@/lib/copy";

type Props = {
  items: MatchedItem[];
};

export function WardrobeMatchList({ items }: Props) {
  if (!items.length) {
    return <p className="text-sm text-[#5C5C5C]">No supporting closet items yet.</p>;
  }
  return (
    <ul className="space-y-2" data-testid="wardrobe-matches">
      {items.slice(0, 8).map((item) => (
        <li
          key={item.item_id}
          className="flex items-center gap-3 rounded-xl border border-[#EAEAEA] bg-[#FAFAFA] p-2"
        >
          <img
            src={assetSrc(item.image_url)}
            alt=""
            className="h-12 w-12 rounded-lg object-cover bg-white"
          />
          <div>
            <p className="text-sm text-[#111111]">{item.name}</p>
            <p className="text-xs text-[#5C5C5C]">{item.reason}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
