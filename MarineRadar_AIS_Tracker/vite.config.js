import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  optimizeDeps: {
    // Exclude maplibre-gl so Vite doesn't break its internal Web Worker import.meta.url resolution
    include: [],
    exclude: ['maplibre-gl'],
  },
  build: {
    // Allow larger chunks (maplibre-gl is ~590KB)
    chunkSizeWarningLimit: 1500,
  },
})
