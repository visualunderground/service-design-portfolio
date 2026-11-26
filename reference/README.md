# Portfolio migration

Original Notion wording retained; metadata and structure converted to MDX. `content/` contains proposed public pages; `reference/` contains source component examples and migration inventories. No site has been built or deployed.

Component contracts: `ApproachPrinciple`, `Callout`, `Challenge`, `Column`, `Columns`, `Figure`, `Metric`, `Metrics`, `Principle`, `ProjectDetails`. These must be implemented and registered in Astro before rendering. Columns express structure rather than styling; source colours and blank layout paragraphs are intentionally discarded. Review routes against the existing Super site, media paths, alternative text, and employer-related content before publication. 

Original media files have not been copied. `core-assets.json` maps proposed stable local paths to Notion references; no expiring signed URLs are embedded in MDX. Do not publish until assets are copied and links validated.

## Collection import

- 48 gallery entries have source IDs, captions, organisation, type and image references. See gallery-assets-1.json through gallery-assets-4.json. Media binaries still need to be copied.
- Collection landing pages use `ProjectGrid` and `PhotoGallery`. The Vimeo embed is represented by `Video`; PDF references use `Attachment` (see attachment-assets.json).
- Review source text and MDX compilation before deployment. The original core-migration.json is a snapshot of the first commit's findings; database blocks, headings, video embed and attachment markup have since been normalised.
