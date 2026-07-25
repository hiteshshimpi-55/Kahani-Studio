import path from 'node:path'
import { fileURLToPath } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const rootDir = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(rootDir, './src'),
    },
  },
  server: {
    host: true,
    port: 5173,
    watch: {
      usePolling: process.env.CHOKIDAR_USEPOLLING === 'true',
    },
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
        // Flush SSE chunks immediately — default proxy buffering kills typewriter.
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes, _req, res) => {
            const ct = proxyRes.headers['content-type']
            if (typeof ct === 'string' && ct.includes('text/event-stream')) {
              res.setHeader('Cache-Control', 'no-cache, no-transform')
              res.setHeader('X-Accel-Buffering', 'no')
              // Disable Nagle on the client socket when available.
              const socket = (res as { socket?: { setNoDelay?: (v: boolean) => void } }).socket
              socket?.setNoDelay?.(true)
            }
          })
        },
      },
    },
  },
})
