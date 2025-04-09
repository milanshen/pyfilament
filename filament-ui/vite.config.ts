import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
    plugins: [react(), tailwindcss()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        host: true,
        port: 3001,
        allowedHosts: true,
        proxy: {
            '/graphql': {
                target: 'http://127.0.0.1:5006',
                changeOrigin: true,
            },
        },
    },
    preview: {
        host: true,
        port: 3001,
        allowedHosts: true,
    },
});
