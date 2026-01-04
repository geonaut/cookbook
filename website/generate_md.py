#!/usr/bin/env python3
"""
Markdown Generation Script

Reads raw recipe TOML files and Hugo config to generate:
- Markdown (.md) files for Hugo website inclusion
- Copies recipe images to static folder
"""

import tomllib
import os
import shutil
from typing import Dict, Any, Optional


# --- Path Resolution ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

# --- Paths ---
RECIPE_DIR = os.path.join(ROOT_DIR, "recipes")
HUGO_CONFIG_PATH = os.path.join(SCRIPT_DIR, "hugo_config.toml")
HUGO_CONTENT_DIR = os.path.join(SCRIPT_DIR, "content.en", "recipes")
HUGO_STATIC_IMAGES_DIR = os.path.join(SCRIPT_DIR, "static", "images")


def generate_markdown(recipe: Dict[str, Any], config: Dict[str, Any], chapter_name: str, order: Optional[int] = None) -> str:
    """Generate Markdown content for Hugo."""
    lines = []
    
    # Frontmatter (YAML format)
    lines.append("---")
    
    # Weight: use explicit order from manifest
    if order is not None:
        lines.append(f"weight: {order}")
    
    # Always include bookToc: false
    lines.append("bookToc: false")
    
    lines.append("---")
    lines.append("")  # Empty line after frontmatter
    
    # Title heading
    lines.append(f"# {recipe['title']}")
    lines.append("")
    
    # Body content - Ingredients section
    lines.append("# Ingredients")
    lines.append("")
    for ing in recipe.get('ingredients', []):
        lines.append(f"* {ing}")
    
    lines.append("")
    
    # Instructions section
    lines.append("# Instructions")
    lines.append("")
    for idx, step in enumerate(recipe.get('instructions', []), 1):
        lines.append(f"{idx}. {step}")
    
    lines.append("")
    
    # Notes/Hints section
    notes = recipe.get('notes', '').strip()
    if notes:
        lines.append("# Hints and Tips")
        lines.append("")
        lines.append(f"* {notes}")
        lines.append("")
    
    # Image (if provided) - placed at the end, centered and smaller
    image_filename = recipe.get('image')
    if image_filename:
        lines.append("<div style='text-align: center; margin-top: 2rem;'>")
        lines.append(f"<img src='/images/{image_filename}' alt='{recipe['title']}' style='width: 50%; max-width: 400px; height: auto;'>")
        lines.append("</div>")
        lines.append("")
    
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
    os.makedirs(HUGO_STATIC_IMAGES_DIR, exist_ok=True)
    
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
        for recipe_config in chapter.get("recipe_config", []):
            recipe_id = recipe_config['id']
            hugo_recipe_configs[chapter_name][recipe_id] = recipe_config
    
    # Sort chapters by weight (if specified, otherwise maintain order)
    chapters = hugo_config_data.get("chapters", [])
    chapters_sorted = sorted(chapters, key=lambda c: c.get("weight", 999))
    
    # Process Hugo chapters
    for chapter in chapters_sorted:
        chapter_name = chapter['name']
        
        # Validate Hugo folder exists
        validate_hugo_folder_exists(chapter_name)
        
        # Get recipe list
        recipe_list = chapter.get("recipes", [])
        
        # Process recipes in manifest order
        for idx, recipe_id in enumerate(recipe_list):
            # Get recipe config for this recipe
            recipe_config = hugo_recipe_configs.get(chapter_name, {}).get(recipe_id, {})
            
            # Search for recipe file in category subdirectory
            # Normalize chapter name to folder name (e.g., "Starters" -> "starters")
            category_folder = get_hugo_folder_name(chapter_name)
            recipe_file = os.path.join(RECIPE_DIR, category_folder, f"{recipe_id}.toml")
            
            # If not found in category folder, try root recipes folder (backward compatibility)
            if not os.path.exists(recipe_file):
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
            
            # Copy recipe image to static folder if it exists
            image_filename = recipe_data.get('image')
            if image_filename:
                # Image source: recipes/{category}/images/{filename}
                image_src = os.path.join(RECIPE_DIR, category_folder, "images", image_filename)
                image_dst = os.path.join(HUGO_STATIC_IMAGES_DIR, image_filename)
                
                if os.path.exists(image_src):
                    shutil.copy2(image_src, image_dst)
                    print(f"  📷 Copied image: {image_filename}")
                else:
                    print(f"  ⚠️  Image not found: {image_src}")


if __name__ == "__main__":
    generate_md()


