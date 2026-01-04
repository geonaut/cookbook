# Geonaut's Cookbook

A dual-output cookbook system that generates both a PDF and a Hugo website from TOML recipe files.

## Setup

### Prerequisites
- Python 3
- LaTeX (for PDF generation)
- Hugo (for website)

### First Time Setup

```bash
make website-init
```

This sets up the Hugo website environment.

## Adding Recipes

1. Create a new `.toml` file in the appropriate `recipes/{category}/` directory
2. Use this format:

```toml
title = "Recipe Name"
category = "category_name"

[ingredients]
ingredient1 = "quantity"
ingredient2 = "quantity"

[instructions]
step1 = "Do this"
step2 = "Then do this"

image = "recipe-name.jpg"  # Optional: place image in recipes/{category}/images/
notes = "Optional notes"
hints = "Optional tips"
```

## Workflow Commands

### Generate Everything
```bash
make all
```
Generates both PDF and website from recipes.

### Generate Only (without serving)
```bash
make compose
```
Converts recipes to LaTeX and Markdown files.

### Development - Serve Website Locally
```bash
make serve
```
Starts Hugo development server at `http://localhost:1313`

### Watch PDF (Live Recompile)
```bash
make watch
```
Automatically recompiles the PDF as you edit LaTeX files.

### Build PDF Only
```bash
make pdf
```
Generates `cookbook.pdf`

### Build Website Only
```bash
make hugo
```
Builds the static site in `website/public/`

### Clean Everything
```bash
make clean
```
Removes all build artifacts.

## Typical Workflow

1. **Edit recipes in `recipes/{category}/`**
   - Add or modify `.toml` files
   - Add images to `recipes/{category}/images/`

2. **Generate outputs**
   ```bash
   make compose
   ```

3. **Preview website locally**
   ```bash
   make serve
   ```
   - Visit `http://localhost:1313`
   - Markdown files auto-generate in `website/content.en/recipes/`

4. **Build final outputs**
   ```bash
   make all
   ```
   - Creates `cookbook.pdf` in root
   - Creates website in `website/public/`

## Website Structure

The Hugo website has these main sections (see sidebar):
- **Recipes** - All recipes organized by category
  - About These Recipes (intro)
  - Sauces
  - Starters & Sides
  - Mains
  - Special Occasions
- **Blog** - Placeholder for future blog posts
- **About Me** - About the cookbook creator
- **PDF Cookbook** - PDF viewer and download
- **Foodie Map** - Placeholder for food destinations

## Notes

- Recipe images should be in `recipes/{category}/images/`
- They're automatically copied to `website/static/images/` during generation
- The website is built with the [hugo-book](https://github.com/alex-shpak/hugo-book) theme
- Both PDF and website generate from the same recipe files (single source of truth)