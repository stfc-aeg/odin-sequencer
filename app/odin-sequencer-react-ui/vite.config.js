import { defineConfig } from 'vite'
import { extname, relative, resolve } from 'path'
import { fileURLToPath } from 'node:url'
import { glob } from 'glob'
import react from '@vitejs/plugin-react'
import dts from 'vite-plugin-dts'
import { libInjectCss } from 'vite-plugin-lib-inject-css'

export default defineConfig({
  plugins: [
    react(),
    libInjectCss(),
    dts({
      include: ['lib'],
      outputDir: 'dist',
    })
  ],
  resolve: {
    dedupe: ['react', 'react-dom']
  },
  build: {
    minify: false,
    lib: {
      entry: resolve(__dirname, 'lib/index.js'),
      fileName: 'index',
      formats: ['es'],
    },
    rollupOptions: {
      external: ['react', 'react-dom', 'react/jsx-runtime', 'bootstrap', 'react-bootstrap', 'odin-react'],
      input: Object.fromEntries(
        glob.sync('lib/**/*.{js,jsx}', {
          ignore: ["lib/**/*.d.js"],
        }).map(file => [
          // The name of the entry point
          // lib/nested/foo.ts becomes nested/foo
          relative(
            'lib',
            file.slice(0, file.length - extname(file).length)
          ),
          // The absolute path to the entry file
          // lib/nested/foo.ts becomes /project/lib/nested/foo.ts
          fileURLToPath(new URL(file, import.meta.url))
        ])
      ),
      output: {
        assetFileNames: 'assets/[name][extname]',
        entryFileNames: '[name].js',
        globals: { react: 'React', 'react-dom': 'ReactDOM' },
        exports: 'named',
      }
    },
    copyPublicDir: false,
  }
})
