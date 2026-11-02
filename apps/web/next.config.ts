import type { NextConfig } from "next";

// Adresse du serveur FastAPI (services/analyzer). En local : http://localhost:8000
const API_URL = process.env.VEYRA_API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
