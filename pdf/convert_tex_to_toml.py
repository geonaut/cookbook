#!/usr/bin/env python3
"""
Convert existing .tex recipe files to TOML format
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Optional


# --- Path Resolution ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
RECIPE_DIR = os.path.join(ROOT_DIR, "recipes")
CHAPTERS_DIR = os.path.join(SCRIPT_DIR, "src", "chapters")


def extract_section(text: str, section_name: str) -> Optional[str]:
    """Extract content from a LaTeX subsection."""
    pattern = rf'\\subsection\*\{{{re.escape(section_name)}\}}\s*(.*?)(?=\\subsection\*|\\vfill|\\newpage|$)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_list_items(text: str, list_type: str = "itemize") -> List[str]:
    """Extract items from a LaTeX list environment."""
    pattern = rf'\\begin\{{{list_type}\}}\s*(.*?)\\end\{{{list_type}\}}'
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return []
    
    items_text = match.group(1)
    # Extract \item content
    items = re.findall(r'\\item\s+(.*?)(?=\\item|$)', items_text, re.DOTALL)
    # Clean up items - remove LaTeX commands but keep text
    cleaned_items = []
    for item in items:
        # Remove LaTeX formatting but keep content
        item = re.sub(r'\\textbf\{(.*?)\}', r'\1', item)  # Remove bold
        item = re.sub(r'\\textit\{(.*?)\}', r'\1', item)  # Remove italic
        item = re.sub(r'\$.*?\$', '', item)  # Remove math mode
        item = item.strip()
        if item:
            cleaned_items.append(item)
    return cleaned_items


def extract_enumerate_items(text: str) -> List[str]:
    """Extract items from a LaTeX enumerate environment."""
    pattern = r'\\begin\{enumerate\}\s*(.*?)\\end\{enumerate\}'
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return []
    
    items_text = match.group(1)
    # Extract \item content
    items = re.findall(r'\\item\s+(.*?)(?=\\item|$)', items_text, re.DOTALL)
    # Clean up items
    cleaned_items = []
    for item in items:
        # Remove LaTeX formatting but keep content
        item = re.sub(r'\\textbf\{(.*?)\}:', r'\1:', item)  # Remove bold labels
        item = re.sub(r'\\textbf\{(.*?)\}', r'\1', item)  # Remove bold
        item = re.sub(r'\\textit\{(.*?)\}', r'\1', item)  # Remove italic
        item = re.sub(r'\$.*?\$', '', item)  # Remove math mode
        item = item.strip()
        if item:
            cleaned_items.append(item)
    return cleaned_items


def extract_image_path(text: str) -> Optional[str]:
    """Extract image path from LaTeX."""
    # Look for \includegraphics
    pattern = r'\\includegraphics.*?\{chapters/(.*?)\}'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def get_column_count(text: str) -> int:
    """Determine column count from multicols or default to 1."""
    match = re.search(r'\\begin\{multicols\}\{(\d+)\}', text)
    if match:
        return int(match.group(1))
    return 1


def parse_tex_file(tex_path: str) -> Dict:
    """Parse a .tex recipe file and extract data."""
    with open(tex_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title
    title_match = re.search(r'\\section\{(.*?)\}', content)
    if not title_match:
        raise ValueError(f"No title found in {tex_path}")
    title = title_match.group(1)
    
    # Extract ingredients
    ingredients_section = extract_section(content, "Ingredients")
    if not ingredients_section:
        ingredients = []
    else:
        # Check if it uses \begin{ingredients} or \begin{itemize}
        if '\\begin{ingredients}' in ingredients_section:
            ingredients = extract_list_items(ingredients_section, "ingredients")
        else:
            ingredients = extract_list_items(ingredients_section, "itemize")
    
    # Extract instructions - check for "Recipe" or "Instructions"
    recipe_section = extract_section(content, "Recipe")
    if not recipe_section:
        recipe_section = extract_section(content, "Instructions")
    
    if not recipe_section:
        instructions = []
    else:
        instructions = extract_enumerate_items(recipe_section)
    
    # Extract hints
    hints_section = extract_section(content, "Hints")
    hints = []
    if hints_section:
        hints = extract_list_items(hints_section, "itemize")
    
    # Extract image
    image = extract_image_path(content)
    
    # Get column count
    columns = get_column_count(content)
    
    # Determine category from directory structure
    # e.g., 02_starters_and_sides -> "Starters"
    path_parts = Path(tex_path).parts
    chapter_dir = None
    for part in path_parts:
        if part.startswith(('01_', '02_', '03_', '04_')):
            chapter_dir = part
            break
    
    category_map = {
        "01_sauces": "Sauces",
        "02_starters_and_sides": "Starters",
        "03_mains": "Mains",
        "04_special_occaisions": "Special Occaisions"
    }
    category = category_map.get(chapter_dir, "Unknown")
    
    return {
        "title": title,
        "category": category,
        "ingredients": ingredients,
        "instructions": instructions,
        "hints": hints if hints else None,
        "image": image,
        "columns": columns
    }


def escape_toml_string(s: str) -> str:
    """Properly escape a string for TOML format."""
    # TOML requires escaping: \ -> \\, " -> \", and control chars
    s = s.replace('\\', '\\\\')  # Escape backslashes first
    s = s.replace('"', '\\"')     # Escape quotes
    s = s.replace('\n', '\\n')    # Escape newlines
    s = s.replace('\r', '\\r')    # Escape carriage returns
    s = s.replace('\t', '\\t')    # Escape tabs
    return s


def convert_to_toml(recipe_data: Dict, recipe_id: str) -> str:
    """Convert recipe data to TOML format."""
    lines = []
    lines.append(f'title = "{escape_toml_string(recipe_data["title"])}"')
    lines.append(f'category = "{escape_toml_string(recipe_data["category"])}"')
    
    # Ingredients
    lines.append("ingredients = [")
    for ing in recipe_data["ingredients"]:
        lines.append(f'    "{escape_toml_string(ing)}",')
    lines.append("]")
    
    # Instructions
    lines.append("instructions = [")
    for step in recipe_data["instructions"]:
        lines.append(f'    "{escape_toml_string(step)}",')
    lines.append("]")
    
    # Hints (optional)
    if recipe_data.get("hints"):
        lines.append("")
        lines.append("# Optional: hints and tips for the recipe")
        lines.append("hints = [")
        for hint in recipe_data["hints"]:
            lines.append(f'    "{escape_toml_string(hint)}",')
        lines.append("]")
    
    return "\n".join(lines)


def get_recipe_id_from_path(tex_path: str) -> str:
    """Extract recipe ID from file path."""
    filename = Path(tex_path).stem
    # Remove chapter prefix (e.g., "02_01_pao_de_queijo" -> "pao_de_queijo")
    parts = filename.split('_', 2)
    if len(parts) >= 3:
        return '_'.join(parts[2:])
    elif len(parts) == 2:
        return parts[1]
    return filename


def convert_all_tex_files():
    """Convert all .tex recipe files to TOML."""
    # Find all .tex files (excluding chapter breaks and intro)
    tex_files = []
    for root, dirs, files in os.walk(CHAPTERS_DIR):
        for file in files:
            if file.endswith('.tex') and not file.endswith(('_chapter_break.tex', '_index.tex', 'intro.tex')):
                tex_path = os.path.join(root, file)
                # Skip test file and chapter breaks
                if 'test' not in file and 'chapter_break' not in file and 'intro' not in file:
                    tex_files.append(tex_path)
    
    print(f"Found {len(tex_files)} recipe files to convert")
    
    for tex_path in tex_files:
        try:
            recipe_data = parse_tex_file(tex_path)
            recipe_id = get_recipe_id_from_path(tex_path)
            
            # Generate TOML content
            toml_content = convert_to_toml(recipe_data, recipe_id)
            
            # Write TOML file
            toml_path = os.path.join(RECIPE_DIR, f"{recipe_id}.toml")
            with open(toml_path, 'w', encoding='utf-8') as f:
                f.write(toml_content)
            
            print(f"✅ Converted: {recipe_id}.toml")
            print(f"   Title: {recipe_data['title']}")
            print(f"   Ingredients: {len(recipe_data['ingredients'])}")
            print(f"   Instructions: {len(recipe_data['instructions'])}")
            if recipe_data.get('hints'):
                print(f"   Hints: {len(recipe_data['hints'])}")
            if recipe_data.get('image'):
                print(f"   Image: {recipe_data['image']}")
            print()
            
        except Exception as e:
            print(f"❌ Error converting {tex_path}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    os.makedirs(RECIPE_DIR, exist_ok=True)
    convert_all_tex_files()

