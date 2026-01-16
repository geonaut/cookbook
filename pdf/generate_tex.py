#!/usr/bin/env python3
import tomllib
import os
import re
import json
from typing import Dict, Any, List

# --- Path Resolution ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
RECIPE_DIR = os.path.join(ROOT_DIR, "recipes") # Source TOMLs
PDF_CONFIG_PATH = os.path.join(SCRIPT_DIR, "pdf_config.toml")
LATEX_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "src", "chapters")
FULL_COOKBOOK_PATH = os.path.join(SCRIPT_DIR, "src", "full_cookbook.tex")

# --- LaTeX Utilities ---

def escape_latex(text: str) -> str:
    if not text: return ""
    protected_map = {}
    counter = 0
    def protect_match(m):
        nonlocal counter
        placeholder = f'PROTECTEDLATEXSEQ{counter}PROTECTED'
        protected_map[placeholder] = m.group(0); counter += 1
        return placeholder
    
    text = re.sub(r'\\([&%$#_{}])', protect_match, text)
    replacements = {'&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '^': r'\textasciicircum{}', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}'}
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    for placeholder, original in protected_map.items():
        text = text.replace(placeholder, original)
    return text

def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_").replace("'", "")

# --- Formatting Helpers ---

def get_ingredients_block(recipe: Dict[str, Any], columns: int) -> str:
    lines = ["\\subsection*{Ingredients}"]
    if columns > 1: lines.append(f"\\begin{{multicols}}{{{columns}}}")
    lines.append("\\begin{ingredients}")
    for ing in recipe.get('ingredients', []):
        lines.append(f"    \\item {escape_latex(ing)}")
    lines.append("\\end{ingredients}")
    if columns > 1: lines.append("\\end{multicols}")
    return "\n".join(lines)

def get_method_block(recipe: Dict[str, Any]) -> str:
    lines = ["\\subsection*{Instructions}", "\\begin{enumerate}"]
    for step in recipe.get('instructions', []):
        lines.append(f"    \\item {escape_latex(step)}")
    lines.append("\\end{enumerate}")
    return "\n".join(lines)

def get_hints_block(recipe: Dict[str, Any]) -> str:
    hints = recipe.get('hints', [])
    if isinstance(hints, dict): hints = hints.get('items', [])
    if not hints: return ""
    
    lines = ["\\subsection*{Hints \\& Tips}", "\\begin{itemize}"]
    for hint in hints:
        lines.append(f"    \\item {escape_latex(hint)}")
    lines.append("\\end{itemize}")
    return "\n".join(lines)

def get_image_block(recipe: Dict[str, Any], chapter_name: str, recipe_id: str, height: str) -> str:
    # Use 'banner' from images section as priority
    img_data = recipe.get('images', {})
    image_filename = img_data.get('banner') or img_data.get('thumbnail')
    
    if not image_filename: return ""
    
    cat_folder = normalize_name(chapter_name)
    # Correct path to the Leaf Bundle image
    image_path = f"recipes/{cat_folder}/{recipe_id}/{image_filename}"
    
    return f"\\begin{{center}}\n    \\includegraphics[width=\\textwidth,height={height},keepaspectratio]{{{image_path}}}\n\\end{{center}}"

# --- Template Functions ---

def format_standard_recipe(recipe: Dict[str, Any], config: Dict[str, Any], chapter_name: str, recipe_id: str) -> str:
    lines = [
        f"\\section{{{escape_latex(recipe['title'])}}}",
    ]
    
    if recipe.get('blurb'):
        lines.append(f"\\textit{{{escape_latex(recipe['blurb'])}}}\\\\")

    lines.append(get_ingredients_block(recipe, config.get('columns', 1)))
    lines.append(get_method_block(recipe))
    lines.append(get_hints_block(recipe))
    lines.append(get_image_block(recipe, chapter_name, recipe_id, "3in"))
    lines.append("\\newpage")
    return "\n".join(lines)

def format_mini_recipe(recipe: Dict[str, Any], config: Dict[str, Any], chapter_name: str, recipe_id: str) -> str:
    lines = [
        r"\begin{minipage}{0.98\textwidth}",
        f"\\subsection*{{{escape_latex(recipe['title']).upper()}}}",
        get_ingredients_block(recipe, 2),
        get_method_block(recipe),
        get_image_block(recipe, chapter_name, recipe_id, "1.5in"),
        r"\end{minipage}",
        r"\vspace{4em}"
    ]
    return "\n".join(lines)

TEMPLATES = {
    "standard": format_standard_recipe,
    "mini": format_mini_recipe
}

# --- Main Logic ---

def get_chapter_directory(chapter_name: str) -> str:
    chapter_map = {
        "Sauces": "01_sauces",
        "Starters": "02_starters_and_sides",
        "Mains": "03_mains",
        "Special Occasions": "04_special_occasions",
    }
    return chapter_map.get(chapter_name, normalize_name(chapter_name))

def generate_tex():
    os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
    try:
        with open(PDF_CONFIG_PATH, "rb") as f:
            pdf_config_data = tomllib.load(f)
    except FileNotFoundError:
        print("❌ PDF Config not found."); return

    defaults = pdf_config_data.get("defaults", {"columns": 1, "template": "standard"})
    full_cookbook_lines = []
    current_chapter = None
    
    for chapter in pdf_config_data.get("chapters", []):
        chapter_name = chapter['name']
        ch_template_name = chapter.get('template', defaults.get('template', 'standard'))
        chapter_dir = get_chapter_directory(chapter_name)
        
        latex_chapter_dir = os.path.join(LATEX_OUTPUT_DIR, chapter_dir)
        os.makedirs(latex_chapter_dir, exist_ok=True)
        
        # 'recipes' in pdf_config are usually IDs
        pdf_manifest = chapter.get("recipes", []) 
        
        if pdf_manifest:
            if current_chapter != chapter_name:
                if current_chapter is not None:
                    full_cookbook_lines.append(r"\clearpage")
                full_cookbook_lines.append(f"\\chapter{{{chapter_name}}}")
                current_chapter = chapter_name
            
            for recipe_item in pdf_manifest:
                # Handle if manifest is list of IDs or list of dicts
                recipe_id = recipe_item['id'] if isinstance(recipe_item, dict) else recipe_item
                
                cat_folder = normalize_name(chapter_name)
                # POINT TO THE NEW LEAF BUNDLE STRUCTURE
                recipe_path = os.path.join(RECIPE_DIR, cat_folder, recipe_id, "recipe.toml")
                
                if not os.path.exists(recipe_path):
                    print(f"⚠️ Warning: Recipe {recipe_id} not found at {recipe_path}")
                    continue
                
                try:
                    with open(recipe_path, "rb") as f:
                        recipe_data = tomllib.load(f)
                except Exception as e: 
                    print(f"❌ Error reading {recipe_id}: {e}")
                    continue

                r_config = {**defaults, "template": ch_template_name}
                if isinstance(recipe_item, dict):
                    r_config.update(recipe_item)

                template_func = TEMPLATES.get(r_config["template"], format_standard_recipe)
                
                # Get LaTeX block
                latex_content = template_func(recipe_data, r_config, chapter_name, recipe_id)
                
                # Write individual file
                latex_filename = f"{chapter_dir.split('_')[0]}_{recipe_id}.tex"
                with open(os.path.join(latex_chapter_dir, latex_filename), "w", encoding="utf-8") as f:
                    f.write(latex_content)
                
                full_cookbook_lines.append(latex_content)

    with open(FULL_COOKBOOK_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(full_cookbook_lines))
    print(f"✅ Full Cookbook generated at {FULL_COOKBOOK_PATH}")

if __name__ == "__main__":
    generate_tex()