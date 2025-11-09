# Diagram Regeneration Guide for MAZE

This guide explains how to regenerate diagrams for the MAZE GitHub Pages site.

## Overview

MAZE uses [D2](https://d2lang.com/) for diagram generation. Diagrams are stored in `docs/whitepaper/diagrams/` as `.d2` source files and rendered to SVG format with both light and dark theme variants.

## Prerequisites

Install D2:
```bash
curl -fsSL https://d2lang.com/install.sh | sh -s --
```

Add to your PATH (if not already):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Current Diagram Inventory

The following diagrams exist in `docs/whitepaper/diagrams/`:
- `01-pipeline*.d2` - 5-stage processing pipeline
- `02-constraints*.d2` - 4-tier constraint hierarchy
- `03-type*.d2` - Type inhabitation search examples
- `04-integrations*.d2` - Integration ecosystem
- `06-roadmap*.d2` - Development roadmap

Some diagrams have `-light.d2` and `-dark.d2` variants, others are theme-agnostic.

## Regeneration Process

### Option 1: Regenerate All Diagrams

```bash
cd /Users/rand/src/maze/docs/whitepaper

# Create output directory
mkdir -p assets/diagrams

# Regenerate all diagrams with light and dark themes
for diagram in diagrams/*.d2; do
  basename=$(basename "$diagram" .d2)
  echo "Rendering: $basename"

  # Skip if already a theme variant
  if [[ "$basename" == *-light || "$basename" == *-dark ]]; then
    d2 "$diagram" "assets/diagrams/${basename}.svg"
  else
    # Generate both themes
    d2 --theme=0 "$diagram" "assets/diagrams/${basename}-light.svg"
    d2 --theme=200 "$diagram" "assets/diagrams/${basename}-dark.svg"
  fi
done
```

### Option 2: Regenerate Single Diagram

```bash
cd /Users/rand/src/maze/docs/whitepaper

# For a specific diagram (e.g., pipeline)
d2 --theme=0 diagrams/01-pipeline.d2 assets/diagrams/01-pipeline-light.svg
d2 --theme=200 diagrams/01-pipeline.d2 assets/diagrams/01-pipeline-dark.svg
```

### Option 3: Set Up GitHub Actions (Recommended)

Create `.github/workflows/deploy-pages.yml`:

```yaml
name: Deploy GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - '.github/workflows/deploy-pages.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup D2
        run: |
          curl -fsSL https://d2lang.com/install.sh | sh -s --
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Render diagrams
        run: |
          cd docs/whitepaper
          mkdir -p assets/diagrams
          for diagram in diagrams/*.d2; do
            basename=$(basename "$diagram" .d2)
            if [[ "$basename" != *-light && "$basename" != *-dark ]]; then
              d2 --theme=0 "$diagram" "assets/diagrams/${basename}-light.svg"
              d2 --theme=200 "$diagram" "assets/diagrams/${basename}-dark.svg"
            else
              d2 "$diagram" "assets/diagrams/${basename}.svg"
            fi
          done

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## Theme Variants

D2 theme options:
- `--theme=0` - Light theme (white background, dark text)
- `--theme=200` - Dark theme (dark background, light text)

## Diagram Styling Consistency

To match RUNE's diagram styling:
1. Use consistent color scheme (orange/amber accent for MAZE)
2. Set proper padding and margins in D2 files
3. Use clear, readable fonts
4. Test both light and dark themes

## HTML Integration

Update HTML to use theme-aware diagram loading:

```html
<!-- Option 1: CSS-based theme switching -->
<div class="diagram-container">
    <img class="diagram-svg"
         alt="Pipeline Diagram"
         src="whitepaper/assets/diagrams/01-pipeline-light.svg" />
</div>

<style>
body.dark-theme .diagram-svg[src*="-light.svg"] {
    content: url('whitepaper/assets/diagrams/01-pipeline-dark.svg');
}
</style>

<!-- Option 2: Picture element with media queries -->
<picture>
    <source srcset="whitepaper/assets/diagrams/01-pipeline-dark.svg"
            media="(prefers-color-scheme: dark)">
    <img src="whitepaper/assets/diagrams/01-pipeline-light.svg"
         alt="Pipeline Diagram">
</picture>
```

## Verification

After regeneration:
1. Check file sizes (should be reasonable, < 200KB per diagram)
2. View in browser with light/dark theme toggle
3. Verify text is readable in both themes
4. Check that colors match MAZE's orange theme (#F59E0B)

## Troubleshooting

**D2 not found**: Ensure `~/.local/bin` is in your PATH
**Permission denied**: Run `chmod +x ~/.local/bin/d2`
**Rendering issues**: Check D2 syntax with `d2 --help`
**Theme not applying**: Verify `--theme` flag and output filenames

## References

- [D2 Documentation](https://d2lang.com/)
- [D2 Themes](https://d2lang.com/tour/themes/)
- [RUNE Diagram Style Guide](../../RUNE/docs/diagrams/)
