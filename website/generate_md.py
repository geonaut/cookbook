#!/usr/bin/env python3
import tomllib
import os
import shutil
import json
import datetime
from typing import Dict, Any, Optional

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
RECIPE_DIR = os.path.join(ROOT_DIR, "recipes")
HUGO_CONFIG_PATH = os.path.join(SCRIPT_DIR, "hugo_config.toml")
HUGO_CONTENT_DIR = os.path.join(SCRIPT_DIR, "content.en", "recipes")

def generate_markdown(recipe: Dict[str, Any], chapter_name: str) -> str:
    lines = ["---"]
    lines.append(f'title: "{recipe.get("title", "Untitled")}"')
    lines.append(f'date: {datetime.date.today().isoformat()}')

    blurb = recipe.get("blurb", "")
    if blurb:
        # Escape any quotes in the blurb for YAML safety
        lines.append(f'description: "{blurb}"')

    # categories: prefer recipe-level category, fall back to chapter name
    category = recipe.get("category", chapter_name)
    lines.append(f'categories: ["{category}"]')

    lines.append(f'tags: {json.dumps(recipe.get("tags", []))}')

    img_data = recipe.get("images", {})
    lines.append(f'banner: "{img_data.get("banner", "")}"')
    if img_data.get("thumbnail"):
        lines.append(f'thumbnail: "{img_data.get("thumbnail")}"')
    if img_data.get("gallery"):
        lines.append(f'gallery: {json.dumps(img_data.get("gallery"))}')

    lines.append("---")

    # Italic blurb intro
    if blurb:
        lines.append(f"\n_{blurb}_\n")

    # Recipe grid shortcode
    lines.append("{{< recipe-grid >}}")
    lines.append("{{< instructions >}}")
    for idx, step in enumerate(recipe.get("instructions", []), 1):
        lines.append(f"{idx}. {step}")
    lines.append("{{< /instructions >}}")

    lines.append("{{< ingredients >}}")
    for ing in recipe.get("ingredients", []):
        lines.append(f"- {ing}")
    lines.append("{{< /ingredients >}}")
    # Hints inside the grid (grid-area: hints)
    if recipe.get("hints"):
        lines.append("{{< hints >}}")
        for hint in recipe.get("hints", []):
            lines.append(f"- {hint}")
        lines.append("{{< /hints >}}")

    # Gallery inside the grid (grid-area: gallery) — reads from .Params.gallery
    if img_data.get("gallery"):
        lines.append("{{< gallery >}}")

    lines.append("{{< /recipe-grid >}}")

    return "\n".join(lines)

def generate_md():
    if not os.path.exists(HUGO_CONFIG_PATH):
        print(f"❌ Error: {HUGO_CONFIG_PATH} not found.")
        return

    with open(HUGO_CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)

    # Clean output directory for a fresh generation
    if os.path.exists(HUGO_CONTENT_DIR):
        shutil.rmtree(HUGO_CONTENT_DIR)
    os.makedirs(HUGO_CONTENT_DIR)

    for chapter in config.get("chapters", []):
        chapter_name = chapter["name"]
        chapter_folder = chapter_name.lower().replace(" ", "_")

        for recipe_id in chapter.get("recipes", []):
            recipe_path = os.path.join(RECIPE_DIR, chapter_folder, recipe_id, "recipe.toml")

            if not os.path.exists(recipe_path):
                print(f"⚠️  Skipping: {recipe_id} (not found at {recipe_path})")
                continue

            with open(recipe_path, "rb") as f:
                recipe_data = tomllib.load(f)

            recipe_bundle_dir = os.path.join(HUGO_CONTENT_DIR, chapter_folder, recipe_id)
            os.makedirs(recipe_bundle_dir, exist_ok=True)

            md_content = generate_markdown(recipe_data, chapter_name)
            with open(os.path.join(recipe_bundle_dir, "index.md"), "w", encoding="utf-8") as f:
                f.write(md_content)

            # Copy associated images
            img_section = recipe_data.get("images", {})
            images_to_copy = [img_section.get("thumbnail"), img_section.get("banner")]
            images_to_copy.extend(img_section.get("gallery", []))

            for img_name in set(filter(None, images_to_copy)):
                src = os.path.join(RECIPE_DIR, chapter_folder, recipe_id, img_name)
                dst = os.path.join(recipe_bundle_dir, img_name)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                else:
                    print(f"⚠️  Image not found: {src}")

        # Write section _index.md if it doesn't already exist
        section_dir = os.path.join(HUGO_CONTENT_DIR, chapter_folder)
        os.makedirs(section_dir, exist_ok=True)
        index_path = os.path.join(section_dir, "_index.md")
        if not os.path.exists(index_path):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(f"---\ntitle: \"{chapter_name}\"\n---\n")

    print("✅ All recipes compiled successfully!")

if __name__ == "__main__":
    generate_md()
