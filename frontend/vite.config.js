import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// In development, requests to /api are proxied to the Python backend so the
// browser never needs CORS. Override the target with VITE_BACKEND_PROXY_TARGET.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxyTarget = env.VITE_BACKEND_PROXY_TARGET || 'http://127.0.0.1:8000';

  const proxy = {
    '/api': {
      target: proxyTarget,
      changeOrigin: true,
      // Local model inference can be slow; keep the proxy from timing out first.
      timeout: 600000,
      proxyTimeout: 600000,
    },
  };

  return {
    plugins: [react()],
    server: { host: '127.0.0.1', port: 5173, proxy },
    preview: { host: '127.0.0.1', port: 4173, proxy },
  };
});
