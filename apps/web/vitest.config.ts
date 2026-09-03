import viteReact from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'url'
import viteTsConfigPaths from 'vite-tsconfig-paths'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  plugins: [
    viteTsConfigPaths({ projects: ['./tsconfig.json'] }),
    viteReact(),
  ],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    css: false,
    env: {
      // The fixture-mode endpoint tests assert fixture behaviour, so they must
      // not depend on a developer's .env. Without this, setting
      // VITE_USE_FIXTURES=false to work against the real API makes them attempt
      // real network calls and fail.
      VITE_USE_FIXTURES: 'true',
    },
  },
})
