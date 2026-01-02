#!/usr/bin/env python3
"""
Markdown Generation Script

Reads raw recipe TOML files and Hugo config to generate:
- Markdown (.md) files for Hugo website inclusion
"""

import tomllib
import os
from typing import Dict, Any, Optional


# --- Path Resolution ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

# --- Paths ---
RECIPE_DIR = os.path.join(ROOT_DIR, "recipes")
HUGO_CONFIG_PATH = os.path.join(SCRIPT_DIR, "hugo_config.toml")
HUGO_CONTENT_DIR = os.path.join(SCRIPT_DIR, "content.en", "recipes")


def generate_markdown(recipe: Dict[str, Any], config: Dict[str, Any], chapter_name: str, order: Optional[int] = None) -> str:
    """Generate Markdown content for Hugo."""
    lines = []
    
    # Frontmatter (TOML format)
    # lines.append("+++")
    lines.append(f'title = "{recipe["title"]}"')
    
    # Category/blurb if present
    if 'category' in recipe:
        lines.append(f'category = "{recipe["category"]}"')
    if 'blurb' in recipe:
        lines.append(f'blurb = "{recipe["blurb"]}"')
    
    # Ingredients
    lines.append("ingredients = [")
    for ing in recipe.get('ingredients', []):
        lines.append(f'    "{ing}",')
    lines.append("]")
    
    # Instructions
    lines.append("instructions = [")
    for step in recipe.get('instructions', []):
        lines.append(f'    "{step}",')
    lines.append("]")
    
    # Chapter and type
    lines.append(f'chapter = "{chapter_name}"')
    lines.append('type = "recipes"')
    
    # Image (if provided in config - format-specific path)
    md_config = config.get('md', {})
    image = md_config.get('image')
    if image:
        lines.append(f'image = "{image}"')
    
    # Weight: use explicit order from manifest
    if order is not None:
        lines.append(f"weight = {order}")
    
    # lines.append("+++")
    lines.append("")  # Empty line after frontmatter
    
    # Notes from recipe TOML
    notes = recipe.get('notes', '').strip()
    if notes:
        lines.append(notes)
    
    return "\n".join(lines)


def normalize_name(name: str) -> str:
    """Normalize a name for comparison (lowercase, replace spaces/special chars)."""
    return name.lower().replace(" ", "_").replace("-", "_").replace("'", "")


def get_hugo_folder_name(chapter_name: str) -> str:
    """Get the expected Hugo folder name for a chapter."""
    return normalize_name(chapter_name)


def validate_category_chapter_match(recipe_data: Dict[str, Any], chapter_name: str, recipe_id: str) -> bool:
    """Validate that recipe category matches chapter name."""
    recipe_category = recipe_data.get('category', '').strip()
    if not recipe_category:
        print(f"⚠️  Warning: Recipe {recipe_id} has no category field")
        return False
    
    # Normalize both for comparison
    normalized_category = normalize_name(recipe_category)
    normalized_chapter = normalize_name(chapter_name)
    
    if normalized_category != normalized_chapter:
        print(f"❌ Error: Recipe {recipe_id} category '{recipe_category}' does not match chapter '{chapter_name}'")
        return False
    
    return True


def validate_hugo_folder_exists(chapter_name: str) -> bool:
    """Validate that the Hugo folder exists for this chapter."""
    folder_name = get_hugo_folder_name(chapter_name)
    folder_path = os.path.join(HUGO_CONTENT_DIR, folder_name)
    
    if not os.path.isdir(folder_path):
        print(f"⚠️  Warning: Hugo folder '{folder_name}' does not exist for chapter '{chapter_name}'")
        print(f"   Expected path: {folder_path}")
        return False
    
    return True


def generate_md():
    """Main Markdown generation function."""
    # Ensure directories exist
    os.makedirs(HUGO_CONTENT_DIR, exist_ok=True)
    
    # Load Hugo config
    try:
        with open(HUGO_CONFIG_PATH, "rb") as f:
            hugo_config_data = tomllib.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find Hugo config at {HUGO_CONFIG_PATH}")
        return
    
    # Build lookup map: chapter_name -> recipe_id -> recipe_config
    hugo_recipe_configs = {}
    for chapter in hugo_config_data.get("chapters", []):
        chapter_name = chapter['name']
        hugo_recipe_configs[chapter_name] = {}
        for recipe_config in chapter.get("recipes", []):
            recipe_id = recipe_config['id']
            hugo_recipe_configs[chapter_name][recipe_id] = recipe_config
    
    # Process Hugo chapters
    for chapter in hugo_config_data.get("chapters", []):
        chapter_name = chapter['name']
        
        # Validate Hugo folder exists
        validate_hugo_folder_exists(chapter_name)
        
        # Get MD manifest
        md_manifest = chapter.get("md", {}).get("recipes", [])
        
        # Process MD recipes in manifest order
        for idx, recipe_id in enumerate(md_manifest):
            # Get recipe config for this recipe
            recipe_config = hugo_recipe_configs.get(chapter_name, {}).get(recipe_id, {})
            recipe_file = os.path.join(RECIPE_DIR, f"{recipe_id}.toml")
            
            # Load recipe
            try:
                with open(recipe_file, "rb") as f:
                    recipe_data = tomllib.load(f)
            except FileNotFoundError:
                print(f"⚠️  Warning: Recipe {recipe_id}.toml not found in {RECIPE_DIR}")
                continue
            
            # Validate category matches chapter
            if not validate_category_chapter_match(recipe_data, chapter_name, recipe_id):
                print(f"   Skipping Markdown generation for {recipe_id}")
                continue
            
            # Merge config (Hugo doesn't use PDF defaults)
            merged_config = recipe_config
            
            # Generate Markdown
            md_content = generate_markdown(recipe_data, merged_config, chapter_name, order=idx + 1)
            # Create subdirectory structure for Hugo if needed
            md_subdir = get_hugo_folder_name(chapter_name)
            md_dir = os.path.join(HUGO_CONTENT_DIR, md_subdir)
            os.makedirs(md_dir, exist_ok=True)
            md_path = os.path.join(md_dir, f"{recipe_id}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            print(f"✅ Markdown: {md_path}")


if __name__ == "__main__":
    generate_md()

