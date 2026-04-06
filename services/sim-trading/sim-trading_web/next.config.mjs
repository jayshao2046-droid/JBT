/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/sim/:path*",
        destination: "http://localhost:8101/:path*",
      },
    ]
  },
}

export default nextConfig
