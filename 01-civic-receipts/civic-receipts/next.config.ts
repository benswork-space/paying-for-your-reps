import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: ".",
  },
  outputFileTracingIncludes: {
    "/zip/[zip]/[bioguideId]": ["./public/data/members/**", "./public/data/districts/**"],
    "/zip/[zip]": ["./public/data/members/**", "./public/data/districts/**"],
    "/api/zip-lookup/[zip]": ["./data/output/**"],
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "unitedstates.github.io",
        pathname: "/images/congress/**",
      },
      {
        protocol: "https",
        hostname: "www.congress.gov",
        pathname: "/img/member/**",
      },
    ],
  },
};

export default nextConfig;
