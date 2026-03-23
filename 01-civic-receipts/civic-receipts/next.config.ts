import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: ".",
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "unitedstates.github.io",
        pathname: "/images/congress/**",
      },
    ],
  },
};

export default nextConfig;
