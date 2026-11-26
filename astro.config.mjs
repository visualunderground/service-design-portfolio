import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';

export default defineConfig({
  site: 'https://visualunderground.github.io',
  base: '/service-design-portfolio',
  integrations: [mdx()],
});
