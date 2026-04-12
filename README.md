# Geonaut's Cookbook

Personal recipe collection, published at **[geonauts-cookbook.uk](https://geonauts-cookbook.uk/)**.

Recipes are written as TOML files and compiled to both a Hugo website and a printable PDF.

## Adding a Recipe

1. Create a `.toml` file in `recipes/{category}/`
2. Run `make compose` to generate Markdown and LaTeX
3. Preview locally with `make serve` → `http://localhost:1313`

```toml
title = "Recipe Name"
category = "mains"

[ingredients]
ingredient1 = "quantity"

[instructions]
step1 = "Do this"

image = "recipe-name.jpg"   # optional — place in recipes/{category}/images/
notes = "..."
hints = "..."
```

## Commands

| Command | What it does |
|---|---|
| `make website-init` | First-time setup |
| `make compose` | Convert recipes → Markdown + LaTeX |
| `make serve` | Hugo dev server at localhost:1313 |
| `make all` | Build PDF + static site |
| `make pdf` | Build PDF only |
| `make hugo` | Build static site only |
| `make watch` | Live-recompile PDF on changes |
| `make clean` | Remove all build artefacts |

## Theme

The website uses **[hugo-cookbook-theme](https://github.com/geonaut/hugo-cookbook-theme)** — a Material Design 3 Hugo theme built for this project.
