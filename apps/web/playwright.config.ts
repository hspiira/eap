import { defineConfig, devices } from "@playwright/test"

const PORT = 3100
// `localhost`, not `127.0.0.1`: the dev server binds IPv6 only.
const BASE_URL = `http://localhost:${PORT}`

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "line" : "list",
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `pnpm vite dev --port ${PORT} --strictPort`,
    url: BASE_URL,
    env: { E2E: "1" },
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
