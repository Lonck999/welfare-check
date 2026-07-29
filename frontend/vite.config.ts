import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  // `npm run start` (production: serves the built dist/) needs to bind 0.0.0.0 and
  // read the platform-assigned $PORT. Configured here instead of via shell syntax in
  // package.json's script so it works the same on Windows (local test) and Linux (Railway).
  preview: {
    host: '0.0.0.0',
    port: Number(process.env.PORT) || 4173,
    // Railway's proxy forwards the public domain as the Host header; Vite's preview
    // server blocks unrecognized hosts by default (DNS-rebinding protection). This is
    // a public-facing form site with no host-based security model, so allow any host.
    allowedHosts: true,
  },
})
