/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    const backend = process.env.BACKEND_BASE_URL || "http://localhost:8105"
    return [
      {
        source: "/api/data/:path*",
        destination: `${backend}/:path*`,
      },
    ]
  },
}

export default nextConfig
