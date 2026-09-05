import tailwindcss from "@tailwindcss/vite"
import { devtools } from "@tanstack/devtools-vite"
import { tanstackStart } from "@tanstack/react-start/plugin/vite"
import viteReact from "@vitejs/plugin-react"
import { nitro } from "nitro/vite"
import { fileURLToPath, URL } from "url"
import { defineConfig } from "vite"
import viteTsConfigPaths from "vite-tsconfig-paths"

const config = defineConfig({
  // Both apps read one .env at the repo root, so paired values (the API base
  // URL and the API's CORS allowlist, the platform tenant id) cannot drift.
  // Only VITE_-prefixed variables reach the browser bundle; the backend's
  // secrets sit in the same file and stay server-side.
  envDir: fileURLToPath(new URL("../../", import.meta.url)),
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  plugins: [
    devtools(),
    nitro(),
    viteTsConfigPaths({ projects: ["./tsconfig.json"] }),
    tailwindcss(),
    tanstackStart({
      router: {
        // Skip co-located test files and fixtures inside src/routes/.
        routeFileIgnorePattern: "\\.test\\.[jt]sx?$|-fixture\\.[jt]sx?$",
      },
    }),
    viteReact(),
  ],
})

export default config
