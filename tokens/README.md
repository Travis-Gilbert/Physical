# tokens

Neutral design tokens in DTCG format. The base ships uncommitted to any single
visual identity; a theme is an extension a user installs, not a default baked
into the core.

- `base.tokens.json` — structural tokens (scale, spacing, radii, semantic
  color *roles*) with neutral values. No brand.
- themes live outside the core and map roles to concrete values.

This mirrors the renderer-neutral token approach in Theorem's own SceneOS work
(project tokens into whatever the renderer needs), kept deliberately generic so
Physical is not scoped to one person's taste.
