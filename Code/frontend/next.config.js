/** @type {import('next').NextConfig} */
const fs = require('fs')
const path = require('path')

/**
 * On Windows (NTFS), `...\Code\...` and `...\code\...` are the same directory but webpack treats
 * them as different module graphs → duplicate React / invalid hooks.
 * Walk the path and rewrite each segment to the casing returned by `readdir` (true on-disk name).
 */
function canonicalizeWinPath(absPath) {
  if (process.platform !== 'win32') {
    return path.normalize(absPath)
  }
  const normalized = path.normalize(absPath)
  const parsed = path.parse(normalized)
  if (!parsed.root) {
    return normalized
  }
  let rebuilt = parsed.root
  const segments = path.relative(parsed.root, normalized).split(path.sep).filter(Boolean)
  for (const segment of segments) {
    let entries = []
    try {
      entries = fs.readdirSync(rebuilt, { withFileTypes: true })
    } catch {
      return normalized
    }
    const hit = entries.find((d) => d.name.toLowerCase() === segment.toLowerCase())
    if (!hit) {
      return normalized
    }
    rebuilt = path.join(rebuilt, hit.name)
  }
  return rebuilt
}

function frontendRoot() {
  const raw = path.dirname(
    require.resolve('./package.json', { paths: [__dirname] }),
  )
  return canonicalizeWinPath(raw)
}

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
    ]
  },
  /**
   * Pin `next`, `react`, and `react-dom` under one canonical `frontendRoot()` (see `canonicalizeWinPath`).
   * Do not alias `react` to `index.js` — that breaks `react/jsx-runtime`.
   * Keep scheduler + styled-jsx client-only; aliasing those on the server broke the server
   * webpack runtime (`__webpack_require__.a is not a function`).
   */
  webpack(config, { isServer }) {
    const ROOT = frontendRoot()
    const nm = (...segments) => path.join(ROOT, 'node_modules', ...segments)
    const reactDir = nm('react')
    const rd = nm('react-dom')

    config.context = ROOT

    config.resolve.alias = {
      ...config.resolve.alias,
      next: nm('next'),
      react: reactDir,
      'react-dom': rd,
    }

    if (!isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        scheduler: nm('scheduler'),
        'styled-jsx': nm('styled-jsx'),
      }
    }
    return config
  },
}

module.exports = nextConfig
