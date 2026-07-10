/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/escalations/:path*",
        destination: "http://localhost:8000/escalations/:path*",
      },
      {
        source: "/chat/:path*",
        destination: "http://localhost:8000/chat/:path*",
      },
      {
        source: "/tickets/:path*",
        destination: "http://localhost:8000/tickets/:path*",
      },
    ];
  },
};

export default nextConfig;
