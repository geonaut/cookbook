#!/usr/bin/env python3
import tomllib
import os
import shutil
import json
from typing import Dict, Any, Optional

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
RECIPE_DIR = os.path.join(ROOT_DIR, "recipes")
HUGO_CONFIG_PATH = os.path.join(SCRIPT_DIR, "hugo_config.toml")
HUGO_CONTENT_DIR = os.path.join(SCRIPT_DIR, "content.en", "recipes")

def generate_markdown(recipe: Dict[str, Any], order: Optional[int] = None) -> str:
    """Generates Markdown with everything in Frontmatter for Template control."""
    lines = ["---"]
    lines.append(f'title: "{recipe.get("title", "Untitled")}"')
    if order is not None:
        lines.append(f"weight: {order}")
    
    # Metadata
    blurb = recipe.get("blurb", "").replace('"', '\\"')
    lines.append(f'blurb: "{blurb}"')
    
    # Tags
    tags = recipe.get("tags", [])
    lines.append(f"tags: {json.dumps(tags)}")

    # Ingredients & Instructions for the Template to use
    ingredients = recipe.get("ingredients", [])
    lines.append(f"ingredients: {json.dumps(ingredients)}")
    
    instructions = recipe.get("instructions", [])
    lines.append(f"instructions: {json.dumps(instructions)}")

    # Hints
    hints = recipe.get("hints", [])
    if isinstance(hints, dict):
        hints = hints.get("items", [])
    # Fallback for old TOML structure
    if not hints:
        hints = recipe.get("images", {}).get("hints", [])
    lines.append(f"hints: {json.dumps(hints)}")

    # Images
    img_data = recipe.get("images", {})
    if img_data.get("banner"):
        lines.append(f'banner: "{img_data["banner"]}"')
    if img_data.get("gallery"):
        lines.append(f"gallery: {json.dumps(img_data['gallery'])}")

    lines.append("---")
    
    # We leave the body empty so the template handles 100% of the layout
    return "\n".join(lines)

def generate_md():
    """Main loop to process all recipes into Hugo Leaf Bundles."""
    if not os.path.exists(HUGO_CONFIG_PATH):
        print(f"❌ Error: {HUGO_CONFIG_PATH} not found.")
        return

    with open(HUGO_CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)

    for chapter in config.get("chapters", []):
        chapter_folder = chapter["name"].lower().replace(" ", "_")

        for idx, recipe_id in enumerate(chapter.get("recipes", [])):
            recipe_path = os.path.join(RECIPE_DIR, chapter_folder, recipe_id, "recipe.toml")

            if not os.path.exists(recipe_path):
                print(f"⚠️  Skipping: {recipe_id} (File not found at {recipe_path})")
                continue

            with open(recipe_path, "rb") as f:
                recipe_data = tomllib.load(f)

            recipe_bundle_dir = os.path.join(HUGO_CONTENT_DIR, chapter_folder, recipe_id)
            os.makedirs(recipe_bundle_dir, exist_ok=True)

            md_content = generate_markdown(recipe_data, order=idx + 1)
            with open(os.path.join(recipe_bundle_dir, "index.md"), "w", encoding="utf-8") as f:
                f.write(md_content)

            img_section = recipe_data.get("images", {})
            images_to_copy = [img_section.get("thumbnail"), img_section.get("banner")]
            images_to_copy.extend(img_section.get("gallery", []))

            for img_name in set(images_to_copy):
                if not img_name: continue
                src = os.path.join(RECIPE_DIR, chapter_folder, recipe_id, img_name)
                dst = os.path.join(recipe_bundle_dir, img_name)
                if os.path.exists(src):
                    shutil.copy2(src, dst)

    print("🚀 All recipes compiled successfully!")

if __name__ == "__main__":
    generate_md()