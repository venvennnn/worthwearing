import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "yce-us.s3-accelerate.amazonaws.com" },
      { protocol: "https", hostname: "**.makeupar.com" },
      { protocol: "https", hostname: "**.amazonaws.com" },
    ],
  },
  async rewrites() {
    const backend = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      { source: "/backend-assets/:path*", destination: `${backend}/assets/:path*` },
    ];
  },
};

export default nextConfig;
