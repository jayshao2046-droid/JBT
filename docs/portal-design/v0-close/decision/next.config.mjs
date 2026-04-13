/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    const backendBase = process.env.BACKEND_BASE_URL ?? "http://localhost:8104"
    return [
      {
        source: "/api/decision/:path*",
        destination: `${backendBase}/:path*`,
      },
    ]
  },
}

export default nextConfig
