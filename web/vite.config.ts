import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api/portfolio': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api/tax': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/risk': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api/market-data': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
      '/api/onboarding': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
      '/api/notifications': {
        target: 'http://localhost:8005',
        changeOrigin: true,
      },
    },
  },
})
