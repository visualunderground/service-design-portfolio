# Service design portfolio

Static Astro website with MDX content, published automatically to GitHub Pages.

- `content/`: editable pages, projects and gallery content. Project and gallery order is controlled by MDX frontmatter.
- `public/assets/`: local images and PDFs, grouped by project, gallery and logos.
- `src/components/`: presentation components.
- `src/pages/`: page layout and routing.
- `.github/workflows/pages.yml`: automatic deployment.

## Local development

```sh
npm install
npm run dev
npm run build
```

The site builds from local content and assets. The résumé remains unpublished. Asset references in MDX start with `/assets/` and resolve inside `public/`.
