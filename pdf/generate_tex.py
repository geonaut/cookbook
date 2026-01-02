#!/usr/bin/env python3
"""
LaTeX Generation Script

Reads raw recipe TOML files and PDF config to generate:
- LaTeX (.tex) files for PDF inclusion
- full_cookbook.tex that includes all recipes
"""

import tomllib
import os
from typing import Dict, Any


# --- Path Resolution ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

# --- Paths ---
RECIPE_DIR = os.path.join(ROOT_DIR, "recipes")
PDF_CONFIG_PATH = os.path.join(SCRIPT_DIR, "pdf_config.toml")
LATEX_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "src", "chapters")
FULL_COOKBOOK_PATH = os.path.join(SCRIPT_DIR, "src", "full_cookbook.tex")


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters, preserving already-escaped sequences."""
    import re
    
    # First, protect already-escaped LaTeX sequences (like \&, \%, etc.)
    # These come from TOML as single backslash sequences
    protected_map = {}
    counter = 0
    
    def protect_match(m):
        nonlocal counter
        # Use a placeholder that won't be escaped (no special chars)
        placeholder = f'PROTECTEDLATEXSEQ{counter}PROTECTED'
        protected_map[placeholder] = m.group(0)
        counter += 1
        return placeholder
    
    # Match backslash followed by special LaTeX characters
    text = re.sub(r'\\([&%$#_{}])', protect_match, text)
    
    # Now escape unescaped special characters
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Restore protected sequences (they already have the backslash, so they're correct)
    for placeholder, original in protected_map.items():
        text = text.replace(placeholder, original)
    
    return text


def generate_latex(recipe: Dict[str, Any], config: Dict[str, Any], chapter_name: str) -> str:
    """Generate LaTeX content for a recipe."""
    lines = []
    
    # Section title
    title = escape_latex(recipe['title'])
    lines.append(f"\\section{{{title}}}")
    
    # Ingredients
    columns = config.get('columns', 1)
    lines.append("\\subsection*{Ingredients}")
    if columns > 1:
        lines.append(f"\\begin{{multicols}}{{{columns}}}")
    # Use \begin{ingredients} environment (defined in cookbook.sty)
    lines.append("\\begin{ingredients}")
    for ing in recipe.get('ingredients', []):
        lines.append(f"    \\item {escape_latex(ing)}")
    lines.append("\\end{ingredients}")
    if columns > 1:
        lines.append("\\end{multicols}")
    lines.append("")
    
    # Recipe/Instructions - use "Recipe" to match original format
    lines.append("\\subsection*{Recipe}")
    lines.append("\\begin{enumerate}")
    for step in recipe.get('instructions', []):
        lines.append(f"    \\item {escape_latex(step)}")
    lines.append("\\end{enumerate}")
    lines.append("")
    
    # Hints (from recipe TOML)
    hints = recipe.get('hints', [])
    if hints:
        lines.append("\\subsection*{Hints}")
        lines.append("\\begin{itemize}")
        for hint in hints:
            lines.append(f"    \\item {escape_latex(hint)}")
        lines.append("\\end{itemize}")
        lines.append("")
    
    # Image (if provided in config - format-specific path)
    pdf_config = config.get('pdf', {})
    image = pdf_config.get('image')
    show_image = config.get('show_image', True)
    if image and show_image:
        lines.append("\\vfill % Push to bottom")
        lines.append("\\begin{center}")
        lines.append("    \\includegraphics[")
        lines.append("        width=\\textwidth,")
        lines.append("        height=\\dimexpr\\pagegoal-\\pagetotal-2\\baselineskip\\relax,")
        lines.append("        keepaspectratio")
        lines.append(f"    ]{{chapters/{image}}}")
        lines.append("\\end{center}")
    
    lines.append("\\newpage")
    
    return "\n".join(lines)


def normalize_name(name: str) -> str:
    """Normalize a name for comparison (lowercase, replace spaces/special chars)."""
    return name.lower().replace(" ", "_").replace("-", "_").replace("'", "")


def get_chapter_directory(chapter_name: str) -> str:
    """Map chapter name to directory name."""
    # Simple mapping - can be extended
    chapter_map = {
        "Starters": "02_starters_and_sides",
        "Mains": "03_mains",
        "Special Occaisions": "04_special_occaisions",
    }
    return chapter_map.get(chapter_name, chapter_name.lower().replace(" ", "_"))


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


def generate_tex():
    """Main LaTeX generation function."""
    # Ensure directories exist
    os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
    
    # Load PDF config
    try:
        with open(PDF_CONFIG_PATH, "rb") as f:
            pdf_config_data = tomllib.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find PDF config at {PDF_CONFIG_PATH}")
        return
    
    pdf_defaults = pdf_config_data.get("defaults", {"columns": 1, "show_image": True})
    
    # Build lookup map: chapter_name -> recipe_id -> recipe_config
    pdf_recipe_configs = {}
    for chapter in pdf_config_data.get("chapters", []):
        chapter_name = chapter['name']
        pdf_recipe_configs[chapter_name] = {}
        for recipe_config in chapter.get("recipes", []):
            recipe_id = recipe_config['id']
            pdf_recipe_configs[chapter_name][recipe_id] = recipe_config
    
    # Store full cookbook content for PDF
    full_cookbook_lines = []
    current_chapter = None
    
    # Process PDF chapters
    for chapter in pdf_config_data.get("chapters", []):
        chapter_name = chapter['name']
        chapter_dir = get_chapter_directory(chapter_name)
        latex_chapter_dir = os.path.join(LATEX_OUTPUT_DIR, chapter_dir)
        os.makedirs(latex_chapter_dir, exist_ok=True)
        
        # Get PDF manifest
        pdf_manifest = chapter.get("pdf", {}).get("recipes", [])
        
        # Process PDF recipes in manifest order
        if pdf_manifest:
            # Add chapter header to full cookbook if this is a new chapter
            if current_chapter != chapter_name:
                full_cookbook_lines.append(f"\\chapter{{{chapter_name}}}")
                current_chapter = chapter_name
            
            for recipe_id in pdf_manifest:
                # Get recipe config for this recipe
                recipe_config = pdf_recipe_configs.get(chapter_name, {}).get(recipe_id, {})
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
                    print(f"   Skipping PDF generation for {recipe_id}")
                    continue
                
                # Merge defaults with recipe-specific config
                merged_config = {**pdf_defaults, **recipe_config}
                
                # Generate LaTeX
                latex_content = generate_latex(recipe_data, merged_config, chapter_name)
                # Determine LaTeX filename (use chapter number prefix if available)
                latex_filename = f"{chapter_dir.split('_')[0]}_{recipe_id}.tex"
                latex_path = os.path.join(latex_chapter_dir, latex_filename)
                with open(latex_path, "w", encoding="utf-8") as f:
                    f.write(latex_content)
                print(f"✅ LaTeX: {latex_path}")
                
                # Add to full cookbook (remove the final \newpage, we'll add it separately)
                cookbook_content = latex_content.rstrip()
                if cookbook_content.endswith("\\newpage"):
                    cookbook_content = cookbook_content[:-8].rstrip()
                elif cookbook_content.endswith("\n\\newpage"):
                    cookbook_content = cookbook_content[:-9].rstrip()
                full_cookbook_lines.append(cookbook_content)
                full_cookbook_lines.append("\\newpage")
    
    # Write full cookbook file
    with open(FULL_COOKBOOK_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(full_cookbook_lines))
    print(f"✅ Full Cookbook: {FULL_COOKBOOK_PATH}")


if __name__ == "__main__":
    generate_tex()

