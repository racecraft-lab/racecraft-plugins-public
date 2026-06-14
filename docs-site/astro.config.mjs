import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://racecraft-lab.github.io',
  base: '/racecraft-plugins-public',
  trailingSlash: 'always',
  integrations: [
    starlight({
      title: 'Racecraft Public Plugins',
      sidebar: [],
    }),
  ],
});
