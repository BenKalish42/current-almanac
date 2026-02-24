import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const netlifyTarget = env.VITE_NETLIFY_PROXY_TARGET || 'http://localhost:8888'

  return {
    base: '/Current/',
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    server: {
      proxy: {
        '/.netlify/functions': {
          target: netlifyTarget,
          changeOrigin: true
        }
      }
    }
  }
})
