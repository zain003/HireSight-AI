/**
 * Windows: cwd may be ...\code\... while the folder on disk is ...\Code\...
 * Node then caches the same physical `react` twice → invalid hooks during SSR/prerender.
 * Resolve the real directory casing and chdir there before running the Next CLI.
 */
const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')

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

const scriptDir = __dirname
const root = canonicalizeWinPath(path.resolve(scriptDir, '..'))

try {
  process.chdir(root)
} catch (e) {
  console.error('[run-next] chdir failed:', root, e)
  process.exit(1)
}

const nextCli = path.join(root, 'node_modules', 'next', 'dist', 'bin', 'next')
const args = process.argv.slice(2)
if (args.length === 0) {
  console.error('Usage: node scripts/run-next.cjs <dev|build|start|...> [args]')
  process.exit(1)
}

const child = spawn(process.execPath, [nextCli, ...args], {
  stdio: 'inherit',
  cwd: root,
  env: { ...process.env },
  windowsHide: true,
})

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal)
  }
  process.exit(code == null ? 1 : code)
})
