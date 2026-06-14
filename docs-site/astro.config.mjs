import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';

export default defineConfig({
  site: 'https://racecraft-lab.github.io',
  base: '/racecraft-plugins-public',
  trailingSlash: 'always',
  integrations: [
    starlight({
      title: 'Racecraft Public Plugins',
      plugins: [starlightLinksValidator()],
      sidebar: [
        {
          label: 'Tutorials',
          items: ['index', 'install/claude-code', 'install/codex', 'first-run'],
        },
        {
          label: 'How-to',
          items: ['choose-your-path', 'troubleshooting', 'contribute-and-release'],
        },
        {
          label: 'Reference',
          items: ['reference', 'glossary'],
        },
        {
          label: 'Explanation',
          items: ['security-and-trust', 'spec-kit-lifecycle'],
        },
      ],
    }),
  ],
});
