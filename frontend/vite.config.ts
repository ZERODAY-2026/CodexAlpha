import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      plugins: [
        {
          name: 'remove-react-external-error-decoder-url',
          generateBundle(_options, bundle) {
            for (const output of Object.values(bundle)) {
              if (output.type === 'chunk') {
                // Keep React's minified error text local instead of embedding a remote decoder URL.
                output.code = output.code.replace(
                  'https://reactjs.org/docs/error-decoder.html?invariant=',
                  'React error #',
                );
              }
            }
          },
        },
      ],
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
    },
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
  },
});
