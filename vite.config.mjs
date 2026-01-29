import { defineConfig } from 'vite';
import { resolve } from 'path';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  base: "/static/",
  resolve: {
    alias: {
      '@': resolve(__dirname, './static'),
    },
  },
  build: {
    manifest: "manifest.json",
    outDir: resolve("./assets"),
    rollupOptions: {
      input: {
        test: resolve('./static/js/main.js'),
        explore: resolve('./static/js/pages/explore.js')
      }
    }
  },
  plugins: [
    tailwindcss(),
  ]
})
