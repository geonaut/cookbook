#!/usr/bin/env python3
"""
generate_tex.py — compile recipe TOMLs into LaTeX for PDF generation.

Discovery-based: every recipe in recipes/ is included unless it has dev = true.
Group order and recipe render order are defined in recipes/recipe_groups.toml.
Per-recipe PDF config (template, columns, show_image) lives in each recipe.toml
under [pdf]. Group-level defaults live in recipe_groups.toml under [groups.pdf].

Usage:
    python3 generate_tex.py          # production — skips dev recipes
    python3 generate_tex.py --dev    # includes dev recipes (for kitchen printing)
"""
import tomllib
import os
import re
import argparse
from typing import Dict, Any, List, Tuple

# --- Paths ---
SCRIPT_DIR        = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR          = os.path.dirname(SCRIPT_DIR)
RECIPE_DIR        = os.path.join(ROOT_DIR, "recipes")
GROUPS_PATH       = os.path.join(RECIPE_DIR, "recipe_groups.toml")
LATEX_OUTPUT_DIR  = os.path.join(SCRIPT_DIR, "src", "chapters")
FULL_COOKBOOK_PATH = os.path.join(SCRIPT_DIR, "src", "full_cookbook.tex")


# --- Utilities ---

def group_folder(group_name: str) -> str:
    return group_name.lower().replace(" ", "_")


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_").replace("'", "")


def escape_latex(text: str) -> str:
    if not text:
        return ""
    protected = {}
    counter = 0

    def protect(m):
        nonlocal counter
        key = f"PROTECTEDLATEXSEQ{counter}PROTECTED"
        protected[key] = m.group(0)
        counter += 1
        return key

    text = re.sub(r'\\([&%$#_{}])', protect, text)
    for char, replacement in {
        "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "^": r"\textasciicircum{}", "_": r"\_",
        "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    }.items():
        text = text.replace(char, replacement)
    for key, original in protected.items():
        text = text.replace(key, original)
    return text


def get_chapter_directory(group_name: str) -> str:
    """Map group name to the LaTeX chapter subdirectory."""
    mapping = {
        "Sauces":            "01_sauces",
        "Starters":          "02_starters_and_sides",
        "Mains":             "03_mains",
        "Special Occaisions": "04_special_occaisions",
    }
    return mapping.get(group_name, normalize_name(group_name))


# --- Block generators ---

def ingredients_block(recipe: Dict, columns: int) -> str:
    lines = [r"\subsection*{Ingredients}"]
    if columns > 1:
        lines.append(f"\\begin{{multicols}}{{{columns}}}")
    lines.append(r"\begin{ingredients}")
    for ing in recipe.get("ingredients", []):
        lines.append(f"    \\item {escape_latex(ing)}")
    lines.append(r"\end{ingredients}")
    if columns > 1:
        lines.append(r"\end{multicols}")
    return "\n".join(lines)


def method_block(recipe: Dict) -> str:
    lines = [r"\subsection*{Instructions}", r"\begin{enumerate}"]
    for step in recipe.get("instructions", []):
        lines.append(f"    \\item {escape_latex(step)}")
    lines.append(r"\end{enumerate}")
    return "\n".join(lines)


def hints_block(recipe: Dict) -> str:
    hints = recipe.get("hints", [])
    if isinstance(hints, dict):
        hints = hints.get("items", [])
    if not hints:
        return ""
    lines = [r"\subsection*{Hints \& Tips}", r"\begin{itemize}"]
    for hint in hints:
        lines.append(f"    \\item {escape_latex(hint)}")
    lines.append(r"\end{itemize}")
    return "\n".join(lines)


def image_block(recipe: Dict, group_name: str, recipe_id: str, height: str) -> str:
    img_data = recipe.get("images", {})
    filename = img_data.get("banner") or img_data.get("thumbnail")
    if not filename:
        return ""
    folder = group_folder(group_name)
    path = f"recipes/{folder}/{recipe_id}/{filename}"
    return (
        f"\\begin{{center}}\n"
        f"    \\includegraphics[width=\\textwidth,height={height},keepaspectratio]{{{path}}}\n"
        f"\\end{{center}}"
    )


# --- Templates ---

def format_standard(recipe: Dict, cfg: Dict, group_name: str, recipe_id: str) -> str:
    lines = [f"\\section{{{escape_latex(recipe['title'])}}}"]
    if recipe.get("blurb"):
        lines.append(f"\\textit{{{escape_latex(recipe['blurb'])}}}\\\\")
    lines.append(ingredients_block(recipe, cfg.get("columns", 1)))
    lines.append(method_block(recipe))
    lines.append(hints_block(recipe))
    if cfg.get("show_image", True):
        lines.append(image_block(recipe, group_name, recipe_id, "3in"))
    lines.append(r"\newpage")
    return "\n".join(lines)


def format_mini(recipe: Dict, cfg: Dict, group_name: str, recipe_id: str) -> str:
    lines = [
        r"\begin{minipage}{0.98\textwidth}",
        f"\\subsection*{{{escape_latex(recipe['title']).upper()}}}",
        ingredients_block(recipe, 2),
        method_block(recipe),
    ]
    if cfg.get("show_image", True):
        lines.append(image_block(recipe, group_name, recipe_id, "1.5in"))
    lines += [r"\end{minipage}", r"\vspace{4em}"]
    return "\n".join(lines)


TEMPLATES = {
    "standard": format_standard,
    "mini":     format_mini,
}


# --- Discovery ---

def load_groups() -> List[Dict]:
    with open(GROUPS_PATH, "rb") as f:
        return tomllib.load(f)["groups"]


def ordered_recipes(group: Dict, include_dev: bool) -> List[Tuple[str, Dict]]:
    """
    Return (recipe_id, recipe_data) in render order:
      1. Explicitly listed recipes in recipe_groups.toml order.
      2. Unlisted recipes in the folder, alphabetically.
    Filters out dev = true unless include_dev is True.
    """
    folder = group_folder(group["name"])
    group_dir = os.path.join(RECIPE_DIR, folder)
    explicit = group.get("recipes", [])

    discovered = set()
    if os.path.isdir(group_dir):
        for entry in os.scandir(group_dir):
            if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "recipe.toml")):
                discovered.add(entry.name)

    for recipe_id in explicit:
        if recipe_id not in discovered:
            print(f"⚠️  '{recipe_id}' listed in recipe_groups.toml but not found in recipes/{folder}/")

    ordered = [r for r in explicit if r in discovered]
    ordered += sorted(r for r in discovered if r not in explicit)

    result = []
    for recipe_id in ordered:
        recipe_path = os.path.join(group_dir, recipe_id, "recipe.toml")
        with open(recipe_path, "rb") as f:
            recipe_data = tomllib.load(f)
        if recipe_data.get("dev", False) and not include_dev:
            continue
        result.append((recipe_id, recipe_data))

    return result


def recipe_pdf_config(recipe_data: Dict, group: Dict) -> Dict:
    """Merge group-level PDF defaults with per-recipe [pdf] overrides."""
    group_pdf = group.get("pdf", {})
    defaults = {
        "template":   group_pdf.get("template", "standard"),
        "columns":    1,
        "show_image": True,
    }
    per_recipe = recipe_data.get("pdf", {})
    return {**defaults, **per_recipe}


# --- Main ---

def generate_tex(include_dev: bool = False):
    if not os.path.exists(GROUPS_PATH):
        print(f"❌ recipe_groups.toml not found at {GROUPS_PATH}")
        return

    os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
    groups = load_groups()

    full_cookbook_lines = []
    current_chapter = None

    for group in groups:
        group_name = group["name"]
        chapter_dir = get_chapter_directory(group_name)
        latex_chapter_dir = os.path.join(LATEX_OUTPUT_DIR, chapter_dir)
        os.makedirs(latex_chapter_dir, exist_ok=True)

        recipes = ordered_recipes(group, include_dev)
        if not recipes:
            continue

        if current_chapter != group_name:
            if current_chapter is not None:
                full_cookbook_lines.append(r"\clearpage")
            full_cookbook_lines.append(f"\\chapter{{{group_name}}}")
            current_chapter = group_name

        for recipe_id, recipe_data in recipes:
            cfg = recipe_pdf_config(recipe_data, group)
            template_fn = TEMPLATES.get(cfg["template"], format_standard)
            latex_content = template_fn(recipe_data, cfg, group_name, recipe_id)

            # Write individual .tex file
            prefix = chapter_dir.split("_")[0]
            latex_filename = f"{prefix}_{normalize_name(recipe_id)}.tex"
            with open(os.path.join(latex_chapter_dir, latex_filename), "w", encoding="utf-8") as f:
                f.write(latex_content)

            full_cookbook_lines.append(latex_content)

        label = " [DEV]" if include_dev else ""
        print(f"  {group_name}: {len(recipes)} recipe(s){label}")

    with open(FULL_COOKBOOK_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(full_cookbook_lines))

    print(f"✅ Full cookbook generated at {FULL_COOKBOOK_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile recipe TOMLs to LaTeX.")
    parser.add_argument("--dev", action="store_true", help="Include dev recipes.")
    args = parser.parse_args()
    generate_tex(include_dev=args.dev)
