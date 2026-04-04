/** @type {import('next').NextConfig} */
const backendBaseUrl = process.env.BACKEND_BASE_URL || 'http://localhost:8103'

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
        source: '/api/:path*',
        destination: `${backendBaseUrl}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
