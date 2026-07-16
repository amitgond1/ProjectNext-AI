import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // 5173 was previously used by another PWA in this browser. A distinct
  // origin prevents that app's service worker from serving stale HTML.
  server: { port: 5174, strictPort: true },
});
