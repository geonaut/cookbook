#!/usr/bin/env python3
"""
generate_tex.py — compile recipe TOMLs into LaTeX for PDF generation.

Discovery-based: every recipe in recipes/ is included unless it has dev = true.
Group order and recipe render order are defined in recipes/recipe_groups.toml.

Layout system (set per-recipe in recipe.toml [pdf], default from [groups.pdf]):
  layout = "full"        — 1 page per recipe (default)
  layout = "double"      — 2 pages per recipe
  layout = "half"        — ½ page; two recipes packed per page
  layout = "half-image"  — recipe top half + recipe image bottom half = 1 page
  layout = "third"       — ⅓ page; three recipes packed per page

Image pages (declared in recipe_groups.toml [[groups.image_pages]]):
  type = "full"   — full-bleed image with caption
  type = "split"  — top + bottom images with captions

Chapter breaks use chapter_image + chapter_image_caption from recipe_groups.toml.

Usage:
    python3 generate_tex.py          # production — skips dev recipes
    python3 generate_tex.py --dev    # includes dev recipes (for kitchen printing)
"""
import tomllib
import os
import re
import argparse
from typing import Dict, Any, List, Tuple, Optional

# --- Paths ---
SCRIPT_DIR         = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR           = os.path.dirname(SCRIPT_DIR)
RECIPE_DIR         = os.path.join(ROOT_DIR, "recipes")
GROUPS_PATH        = os.path.join(RECIPE_DIR, "recipe_groups.toml")
LATEX_OUTPUT_DIR   = os.path.join(SCRIPT_DIR, "src", "chapters")
FULL_COOKBOOK_PATH     = os.path.join(SCRIPT_DIR, "src", "full_cookbook.tex")
FULL_COOKBOOK_DEV_PATH = os.path.join(SCRIPT_DIR, "src", "full_cookbook_dev.tex")

# How much of a page each layout consumes.
# "full" and "half-image" always occupy exactly 1 page.
# "double" occupies 2 pages.
# "half" and "third" are packed together.
LAYOUT_SIZE = {
    "full":       1.0,
    "double":     2.0,
    "half":       0.5,
    "half-image": 1.0,
    "third":      1 / 3,
}

# Layouts that always start and end on their own page(s).
SELF_CONTAINED = {"full", "double", "half-image"}


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
    mapping = {
        "Sauces":             "01_sauces",
        "Starters":           "02_starters_and_sides",
        "Mains":              "03_mains",
        "Special Occaisions": "04_special_occaisions",
    }
    return mapping.get(group_name, normalize_name(group_name))


# --- Content block generators ---

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


def recipe_image_path(recipe: Dict, group_name: str, recipe_id: str) -> str:
    """Return the image path (relative to repo root) for the recipe's banner/thumbnail."""
    img_data = recipe.get("images", {})
    filename = img_data.get("banner") or img_data.get("thumbnail")
    if not filename:
        return ""
    folder = group_folder(group_name)
    return f"recipes/{folder}/{recipe_id}/{filename}"


# --- Recipe content (layout-agnostic inner content) ---

def recipe_inner(recipe: Dict, cfg: Dict) -> str:
    """Generate the recipe body (title + content) without any layout wrapper."""
    lines = []
    title = escape_latex(recipe.get("title", "Untitled"))

    # Use \section* for full/double, \subsection* for smaller layouts
    layout = cfg.get("layout", "full")
    if layout in ("half", "third"):
        lines.append(f"\\textbf{{\\large {title}}}")
    else:
        lines.append(f"\\section*{{{title}}}")

    if recipe.get("blurb") and layout not in ("third",):
        lines.append(f"\\textit{{{escape_latex(recipe['blurb'])}}}\\\\[2pt]")

    # Use explicit columns if set in [pdf]; otherwise auto-2-col for >4 ingredients
    if "columns" in recipe.get("pdf", {}):
        columns = cfg.get("columns", 1)
    else:
        columns = 2 if len(recipe.get("ingredients", [])) > 4 else 1
    lines.append(ingredients_block(recipe, columns))
    lines.append(method_block(recipe))

    # Omit hints for third-page layout to save space
    if layout != "third":
        lines.append(hints_block(recipe))

    return "\n".join(lines)


# --- Layout wrappers ---

def wrap_layout(inner: str, layout: str, image_path: str = "") -> str:
    """Wrap recipe inner content in the appropriate fixed-height LaTeX block."""
    if layout == "full":
        return (
            "\\begin{minipage}[t][\\fullpageheight][t]{\\textwidth}\n"
            + inner + "\n"
            + "\\end{minipage}\n"
            + "\\clearpage"
        )
    elif layout == "double":
        return inner + "\n\\clearpage"
    elif layout == "half":
        return (
            "\\begin{minipage}[t][\\halfpageheight][t]{\\textwidth}\n"
            + inner + "\n"
            + "\\end{minipage}"
        )
    elif layout == "half-image":
        img_line = (
            f"\\noindent\\includegraphics[width=\\textwidth,height=\\halfpageheight,"
            f"keepaspectratio=false,clip]{{{image_path}}}"
            if image_path else
            "\\vspace{\\halfpageheight}"
        )
        return (
            "\\begin{minipage}[t][\\halfpageheight][t]{\\textwidth}\n"
            + inner + "\n"
            + "\\end{minipage}\n"
            + "\\par\\vspace{2mm}\n"
            + img_line + "\n"
            + "\\clearpage"
        )
    elif layout == "third":
        return (
            "\\begin{minipage}[t][\\thirdpageheight][t]{\\textwidth}\n"
            + inner + "\n"
            + "\\end{minipage}"
        )
    # Fallback
    return inner + "\n\\clearpage"


# --- Image page generators ---

def image_page_full(image_path: str, caption: str) -> str:
    return f"\\imagepagefull{{{image_path}}}{{{escape_latex(caption)}}}"


def image_page_split(images: List[str], captions: List[str]) -> str:
    top_img  = images[0]  if len(images)  > 0 else ""
    bot_img  = images[1]  if len(images)  > 1 else ""
    top_cap  = captions[0] if len(captions) > 0 else ""
    bot_cap  = captions[1] if len(captions) > 1 else ""
    return (
        f"\\imagepagesplit{{{top_img}}}{{{escape_latex(top_cap)}}}"
        f"{{{bot_img}}}{{{escape_latex(bot_cap)}}}"
    )


def generate_image_page(item: Dict) -> str:
    page_type = item.get("type", "full")
    if page_type == "split":
        return image_page_split(item.get("images", []), item.get("captions", []))
    else:
        return image_page_full(item.get("image", ""), item.get("caption", ""))


# --- Discovery ---

def load_groups() -> List[Dict]:
    with open(GROUPS_PATH, "rb") as f:
        return tomllib.load(f)["groups"]


def ordered_recipes(group: Dict, include_dev: bool) -> List[Tuple[str, Dict]]:
    folder    = group_folder(group["name"])
    group_dir = os.path.join(RECIPE_DIR, folder)
    explicit  = group.get("recipes", [])

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
    # Migrate legacy 'template' field to 'layout'
    group_layout = group_pdf.get("layout") or {
        "standard": "full", "mini": "half"
    }.get(group_pdf.get("template", ""), "full")

    defaults = {
        "layout":     group_layout,
        "columns":    1,
        "show_image": True,
    }
    per_recipe = dict(recipe_data.get("pdf", {}))
    # Migrate legacy 'template' field in per-recipe config
    if "template" in per_recipe and "layout" not in per_recipe:
        per_recipe["layout"] = {"standard": "full", "mini": "half"}.get(per_recipe.pop("template"), "full")
    return {**defaults, **per_recipe}


# --- Page packing ---

def generate_group_latex(
    group: Dict,
    include_dev: bool,
) -> List[str]:
    """
    Return a list of LaTeX strings for this group (chapter break + recipes +
    image pages), with correct page packing for sub-page layouts.
    """
    group_name = group["name"]
    lines: List[str] = []

    # ── Chapter break ────────────────────────────────────────────────────────
    chapter_img     = group.get("chapter_image", "")
    chapter_caption = group.get("chapter_image_caption", "")
    if chapter_img:
        lines.append(
            f"\\chapterbreak{{{escape_latex(group_name)}}}"
            f"{{{chapter_img}}}{{{escape_latex(chapter_caption)}}}"
        )
    else:
        lines.append(f"\\chapterbreakplain{{{escape_latex(group_name)}}}")

    # ── Build image-page index keyed by position ──────────────────────────────
    # Each entry: after → list of image page dicts
    image_pages_raw: List[Dict] = group.get("image_pages", [])
    image_page_map: Dict[str, List[Dict]] = {}
    for ip in image_pages_raw:
        key = ip.get("after", "__start__")
        image_page_map.setdefault(key, []).append(ip)

    # ── Emit image pages scheduled for __start__ ──────────────────────────────
    for ip in image_page_map.get("__start__", []):
        lines.append(generate_image_page(ip))

    # ── Recipes + interleaved image pages ─────────────────────────────────────
    recipes = ordered_recipes(group, include_dev)

    space_used = 0.0  # fraction of current page already filled

    for recipe_id, recipe_data in recipes:
        cfg    = recipe_pdf_config(recipe_data, group)
        layout = cfg.get("layout", "full")
        size   = LAYOUT_SIZE.get(layout, 1.0)

        # Self-contained layouts always start fresh
        if layout in SELF_CONTAINED and space_used > 0.01:
            lines.append(r"\clearpage")
            space_used = 0.0

        # Packed layout: flush page if recipe won't fit
        if layout not in SELF_CONTAINED and space_used > 0.01:
            if space_used + size > 1.0 + 0.01:
                lines.append(r"\clearpage")
                space_used = 0.0

        # Separator between recipes sharing a page
        if space_used > 0.01:
            lines.append(r"\recipesep")

        # Generate and wrap recipe
        img_path = recipe_image_path(recipe_data, group_name, recipe_id)
        inner    = recipe_inner(recipe_data, cfg)
        lines.append(wrap_layout(inner, layout, img_path))

        # Update page accounting
        if layout in SELF_CONTAINED:
            space_used = 0.0
        else:
            space_used += size
            if space_used >= 1.0 - 0.01:
                lines.append(r"\clearpage")
                space_used = 0.0

        # ── Image pages after this recipe ─────────────────────────────────────
        for ip in image_page_map.get(recipe_id, []):
            if space_used > 0.01:
                lines.append(r"\clearpage")
                space_used = 0.0
            lines.append(generate_image_page(ip))

    # Flush any partial page at end of group
    if space_used > 0.01:
        lines.append(r"\clearpage")

    # ── Image pages scheduled for __end__ ─────────────────────────────────────
    for ip in image_page_map.get("__end__", []):
        lines.append(generate_image_page(ip))

    return lines


# --- Main ---

def generate_tex(include_dev: bool = False):
    if not os.path.exists(GROUPS_PATH):
        print(f"❌ recipe_groups.toml not found at {GROUPS_PATH}")
        return

    output_path = FULL_COOKBOOK_DEV_PATH if include_dev else FULL_COOKBOOK_PATH
    os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
    groups = load_groups()

    all_lines: List[str] = []

    for group in groups:
        group_name  = group["name"]
        chapter_dir = get_chapter_directory(group_name)
        latex_chapter_dir = os.path.join(LATEX_OUTPUT_DIR, chapter_dir)
        os.makedirs(latex_chapter_dir, exist_ok=True)

        recipes = ordered_recipes(group, include_dev)
        if not recipes:
            continue

        group_lines = generate_group_latex(group, include_dev)
        all_lines.extend(group_lines)

        label = " [DEV]" if include_dev else ""
        print(f"  {group_name}: {len(recipes)} recipe(s){label}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines))

    print(f"✅ Full cookbook generated at {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile recipe TOMLs to LaTeX.")
    parser.add_argument("--dev", action="store_true", help="Include dev recipes.")
    args = parser.parse_args()
    generate_tex(include_dev=args.dev)
