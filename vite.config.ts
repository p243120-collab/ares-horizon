import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// base './' lets the built site run from any sub-path (GitHub Pages project sites).
export default defineConfig({
  plugins: [react()],
  base: './',
  worker: { format: 'es' },
  test: { environment: 'node', include: ['tests/**/*.test.ts'] },
});
