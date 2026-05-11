/** @type {import('next').NextConfig} */
const path = require('path')

const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/:path*',
      },
    ];
  },
  /**
   * Windows: mixed casing (Code vs code) can duplicate react/react-dom on the client
   * → invalid hook call. Pin one copy for the *client* bundle only.
   * Do not alias on the server: forcing scheduler/styled-jsx paths breaks the server
   * webpack runtime (`__webpack_require__.a is not a function` on /login, etc.).
   */
  webpack(config, { isServer }) {
    if (!isServer) {
      const nm = (...segments) => path.join(__dirname, 'node_modules', ...segments)
      config.resolve.alias = {
        ...config.resolve.alias,
        react: nm('react'),
        'react-dom': nm('react-dom'),
        scheduler: nm('scheduler'),
        'styled-jsx': nm('styled-jsx'),
      }
    }
    return config
  },
}

module.exports = nextConfig
