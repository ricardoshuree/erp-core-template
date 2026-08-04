// [mcp-local harness] feature: fix-rbac-supabase-production-ready | plano: 509f25bf | 2026-08-04 07:25:23
// Corrige outDir de ../backend/app/frontend (padrao do template original, servido pelo FastAPI) para dist (padrao Vite), que e o que a Vercel espera encontrar apos o build. Causa raiz do Deployment Failed.
import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

// https://vitejs.dev/config/
export default defineConfig({
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
})
