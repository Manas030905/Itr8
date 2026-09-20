import type { NextConfig } from "next";

// Where the FastAPI service lives. NOTE: rewrite destinations are fixed at BUILD time, so
// API_INTERNAL_URL must be set when running `next build` (Docker: build arg; Vercel: env var).
const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Docker builds set NEXT_OUTPUT=standalone for a small runtime image; `npm start` works normally.
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
  poweredByHeader: false,
  // Same-origin API: the browser only ever talks to this origin (see docs/ARCHITECTURE.md).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_INTERNAL_URL}/api/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
