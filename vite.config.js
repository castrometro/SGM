import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(),],
  define: {
    'import.meta.env.VITE_MEDIA_BASE_URL': JSON.stringify(process.env.VITE_MEDIA_BASE_URL || 'http://172.17.11.18:8000')
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  }
})

