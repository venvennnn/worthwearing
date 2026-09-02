export function assetSrc(url: string) {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return url;
}

export const RECOMMENDATION_COPY = {
  worth_it: {
    label: "Worth It",
    color: "#0F7B4B",
    helper: "Wardrobe evidence supports keeping this piece.",
  },
  think_again: {
    label: "Think Again",
    color: "#B45309",
    helper: "Mixed evidence — inspect the factors before you buy.",
  },
  skip_it: {
    label: "Skip It",
    color: "#B42318",
    helper: "Likely to duplicate what you own or go unworn.",
  },
} as const;
