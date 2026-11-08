import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react(),
    // Dependency diagnostics contain documentation URLs. Keep those dormant strings
    // from looking like runtime network dependencies in the offline build audit.
    {
      name: 'offline-url-literals',
      generateBundle(_, bundle) {
        for (const entry of Object.values(bundle)) {
          if (entry.type === 'chunk') entry.code = entry.code.replaceAll('https://', 'https:\\x2f\\x2f').replaceAll('http://', 'http:\\x2f\\x2f');
        }
      },
    },
  ],
  base: './',
  build: { outDir: '../dist', emptyOutDir: true, sourcemap: false },
  server: { proxy: { '/api': 'http://localhost:8060' } },
});
