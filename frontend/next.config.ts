import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        // Proxies frontend API calls to the backend running locally.
        // Using 127.0.0.1 specifically avoids Node.js IPv6 resolution issues on Windows.
        source: "/api/v1/:path*",
        destination: "http://127.0.0.1:8000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
