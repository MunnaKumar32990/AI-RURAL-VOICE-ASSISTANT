import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // Dev proxy – forwards API calls to the backend server.
    // The frontend uses VITE_API_URL (set in .env) for direct calls,
    // but this proxy is kept as a fallback for relative-path calls.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/process-audio': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/process-text': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
