#!/usr/bin/env python3
import tomllib
import os
import re
from typing import Dict, Any, List

# --- Path Resolution ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
RECIPE_DIR = os.path.join(ROOT_DIR, "recipes")
PDF_CONFIG_PATH = os.path.join(SCRIPT_DIR, "pdf_config.toml")
LATEX_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "src", "chapters")
FULL_COOKBOOK_PATH = os.path.join(SCRIPT_DIR, "src", "full_cookbook.tex")

# --- LaTeX Utilities ---

def escape_latex(text: str) -> str:
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
    lines = ["\\subsection*{Recipe}", "\\begin{enumerate}"]
    for step in recipe.get('instructions', []):
        lines.append(f"    \\item {escape_latex(step)}")
    lines.append("\\end{enumerate}")
    return "\n".join(lines)

def get_image_block(recipe: Dict[str, Any], chapter_name: str, height: str) -> str:
    image_filename = recipe.get('image')
    if not image_filename: return ""
    cat_folder = normalize_name(chapter_name)
    image_path = f"recipes/{cat_folder}/images/{image_filename}"
    return f"\\begin{{center}}\n    \\includegraphics[width=\\textwidth,height={height},keepaspectratio]{{{image_path}}}\n\\end{{center}}"

# --- Template Functions ---

def format_standard_recipe(recipe: Dict[str, Any], config: Dict[str, Any], chapter_name: str) -> str:
    """Standard full-page recipe template. Ends with a newpage."""
    lines = [
        f"\\section{{{escape_latex(recipe['title'])}}}",
        get_ingredients_block(recipe, config.get('columns', 1)),
        get_method_block(recipe),
        get_image_block(recipe, chapter_name, "\\dimexpr\\pagegoal-\\pagetotal-2\\baselineskip\\relax"),
        "\\newpage" 
    ]
    return "\n".join(lines)

def format_mini_recipe(recipe: Dict[str, Any], config: Dict[str, Any], chapter_name: str) -> str:
    """Compact template for stacking. Forced 2-col, All-Caps, and no horizontal line."""
    lines = [
        r"\begin{minipage}{\textwidth}",
        f"\\subsection*{{{escape_latex(recipe['title']).upper()}}}",
        get_ingredients_block(recipe, 2),
        get_method_block(recipe),
        get_image_block(recipe, chapter_name, "1.5in"),
        r"\end{minipage}",
        r"\vspace{4em}" # Just white space for a cleaner look
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
        "Special Occaisions": "04_special_occaisions",
    }
    return chapter_map.get(chapter_name, normalize_name(chapter_name))

def generate_tex():
    os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
    try:
        with open(PDF_CONFIG_PATH, "rb") as f:
            pdf_config_data = tomllib.load(f)
    except FileNotFoundError:
        print("❌ Config not found."); return

    defaults = pdf_config_data.get("defaults", {"columns": 1, "show_image": True, "template": "standard"})
    full_cookbook_lines = []
    current_chapter = None
    
    for chapter in pdf_config_data.get("chapters", []):
        chapter_name = chapter['name']
        ch_template_name = chapter.get('template', defaults.get('template', 'standard'))
        chapter_dir = get_chapter_directory(chapter_name)
        
        latex_chapter_dir = os.path.join(LATEX_OUTPUT_DIR, chapter_dir)
        os.makedirs(latex_chapter_dir, exist_ok=True)
        
        pdf_manifest = chapter.get("pdf", {}).get("recipes", [])
        recipe_overrides = {r['id']: r for r in chapter.get("recipes", [])}
        
        if pdf_manifest:
            # Chapter Transition: Clear previous page if stacking was happening
            if current_chapter != chapter_name:
                if current_chapter is not None:
                    full_cookbook_lines.append(r"\clearpage")
                full_cookbook_lines.append(f"\\chapter{{{chapter_name}}}")
                current_chapter = chapter_name
            
            for recipe_id in pdf_manifest:
                cat_folder = normalize_name(chapter_name)
                recipe_path = os.path.join(RECIPE_DIR, cat_folder, f"{recipe_id}.toml")
                if not os.path.exists(recipe_path):
                    recipe_path = os.path.join(RECIPE_DIR, f"{recipe_id}.toml")
                
                try:
                    with open(recipe_path, "rb") as f:
                        recipe_data = tomllib.load(f)
                except Exception: continue

                r_config = {**defaults, "template": ch_template_name, **recipe_overrides.get(recipe_id, {})}
                template_func = TEMPLATES.get(r_config["template"], format_standard_recipe)
                
                # Get self-contained LaTeX block from template
                latex_content = template_func(recipe_data, r_config, chapter_name)
                
                # Write individual file
                latex_filename = f"{chapter_dir.split('_')[0]}_{recipe_id}.tex"
                with open(os.path.join(latex_chapter_dir, latex_filename), "w") as f:
                    f.write(latex_content)
                
                # Append directly to full cookbook buffer
                full_cookbook_lines.append(latex_content)

    with open(FULL_COOKBOOK_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(full_cookbook_lines))
    print(f"✅ Full Cookbook generated at {FULL_COOKBOOK_PATH}")

if __name__ == "__main__":
    generate_tex()