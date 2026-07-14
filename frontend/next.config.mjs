/** @type {import('next').NextConfig} */
const API_URL = process.env.BACKEND_API_URL || "http://localhost:8000";

const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/escalations/:path*",
        destination: `${API_URL}/escalations/:path*`,
      },
      {
        source: "/chat/:path*",
        destination: `${API_URL}/chat/:path*`,
      },
      {
        source: "/tickets/:path*",
        destination: `${API_URL}/tickets/:path*`,
      },
    ];
  },
};

export default nextConfig;