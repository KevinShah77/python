import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (
            id.includes('/node_modules/.pnpm/recharts@') ||
            id.includes('/node_modules/.pnpm/victory-vendor@') ||
            id.includes('/node_modules/recharts/') ||
            id.includes('/node_modules/victory-vendor/')
          ) {
            return 'charts';
          }
        },
      },
    },
  },
});
