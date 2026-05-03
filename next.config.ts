import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1"],
  output: "standalone",
  logging: {
    incomingRequests: false,
    browserToTerminal: "error",
  },
};

export default nextConfig;
