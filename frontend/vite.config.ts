import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [
    react(),
    mode === "development" && componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  define: {
    "process.env.NODE_ENV": JSON.stringify(mode),
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // ✅ Group specific heavy libraries into static chunks
          // ✅ Core React
          if (id.includes('react')) return 'react-core';

          // ✅ UI component libraries
          if (id.includes('@radix-ui')) return 'radix-ui';
          if (id.includes('lucide-react')) return 'icons'; // Icons
          if (id.includes('cmdk')) return 'cmdk';

          // ✅ Charts
          if (id.includes('recharts')) return 'charts';

          // ✅ Forms & validation
          if (id.includes('react-hook-form')) return 'forms';
          if (id.includes('@hookform')) return 'forms';
          if (id.includes('zod')) return 'validation';

          // ✅ Date & time
          if (id.includes('date-fns')) return 'date-utils';
          if (id.includes('react-day-picker')) return 'date-picker';

          // ✅ Routing
          if (id.includes('react-router')) return 'router';

          // ✅ State / data fetching
          if (id.includes('@tanstack')) return 'react-query';

          // ✅ Utils & misc
          if (id.includes('clsx')) return 'utils';
          if (id.includes('tailwind-merge')) return 'utils';

          // ✅ File processing
          if (id.includes('xlsx')) return 'file-utils';

          // ✅ Notifications
          if (id.includes('react-hot-toast') || id.includes('sonner')) return 'notifications';


          // ✅ Fallback: split other node_modules dynamically
          if (id.includes('node_modules')) {
            const parts = id.split('node_modules/')[1].split('/');
            const name = parts[0].startsWith('@')
              ? parts[0] + '-' + parts[1]
              : parts[0];
            return `vendor-${name}`;
          }
        },
      },
    },
  },
}));
