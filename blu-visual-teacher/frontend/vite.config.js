import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    allowedHosts: true,
    // When the frontend itself uses port 8000, point the proxy at the API on another port.
    proxy: { '/api': process.env.BLU_API_PROXY_TARGET || 'http://127.0.0.1:8000' },
  },
  preview: { host: '0.0.0.0', allowedHosts: true },
});
