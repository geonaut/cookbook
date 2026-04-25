#!/usr/bin/env python3
"""
generate_md.py — compile recipe TOMLs into Hugo markdown content.

Discovery-based: every recipe in recipes/ is included unless it has dev = true.
Group order and recipe render order are defined in recipes/recipe_groups.toml.

Usage:
    python3 generate_md.py          # production — skips dev recipes
    python3 generate_md.py --dev    # includes dev recipes
"""
import tomllib
import os
import shutil
import json
import datetime
import argparse
from typing import Dict, Any, List, Tuple

# --- Paths ---
SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR        = os.path.dirname(SCRIPT_DIR)
RECIPE_DIR      = os.path.join(ROOT_DIR, "recipes")
GROUPS_PATH     = os.path.join(RECIPE_DIR, "recipe_groups.toml")
HUGO_CONTENT_DIR = os.path.join(SCRIPT_DIR, "content.en", "recipes")


def group_folder(group_name: str) -> str:
    return group_name.lower().replace(" ", "_")


def load_groups() -> List[Dict]:
    with open(GROUPS_PATH, "rb") as f:
        return tomllib.load(f)["groups"]


def ordered_recipes(group: Dict, include_dev: bool) -> List[Tuple[str, Dict]]:
    """
    Return (recipe_id, recipe_data) pairs in render order:
      1. Recipes explicitly listed in recipe_groups.toml, in that order.
      2. Any unlisted recipes in the folder, appended alphabetically.
    Dev recipes are filtered out unless include_dev is True.
    """
    folder = group_folder(group["name"])
    group_dir = os.path.join(RECIPE_DIR, folder)
    explicit = group.get("recipes", [])

    # Discover all recipe folders in this group directory
    discovered = set()
    if os.path.isdir(group_dir):
        for entry in os.scandir(group_dir):
            if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "recipe.toml")):
                discovered.add(entry.name)

    # Warn about recipes listed in groups file but missing from disk
    for recipe_id in explicit:
        if recipe_id not in discovered:
            print(f"⚠️  '{recipe_id}' listed in recipe_groups.toml but not found in recipes/{folder}/")

    # Build ordered list: explicit first, then unlisted alphabetically
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


def generate_markdown(recipe: Dict[str, Any], group_name: str) -> str:
    lines = ["---"]
    lines.append(f'title: "{recipe.get("title", "Untitled")}"')
    lines.append(f'date: {datetime.date.today().isoformat()}')

    blurb = recipe.get("blurb", "")
    if blurb:
        safe_blurb = blurb.replace('"', '\\"')
        lines.append(f'description: "{safe_blurb}"')

    category = recipe.get("category", group_name)
    lines.append(f'categories: ["{category}"]')
    lines.append(f'tags: {json.dumps(recipe.get("tags", []))}')
    lines.append(f'nationality: "{recipe.get("nationality", "")}"')

    img_data = recipe.get("images", {})
    lines.append(f'banner: "{img_data.get("banner", "")}"')
    if img_data.get("thumbnail"):
        lines.append(f'thumbnail: "{img_data["thumbnail"]}"')
    if img_data.get("gallery"):
        lines.append(f'gallery: {json.dumps(img_data["gallery"])}')

    site_cfg = recipe.get("site", {})
    if site_cfg.get("featured") or recipe.get("featured"):  # support legacy top-level key
        lines.append("featured: true")
    if site_cfg.get("nav"):
        lines.append("nav: true")

    lines.append("---")

    if blurb:
        lines.append(f"\n_{blurb}_\n")

    lines.append("{{< recipe-grid >}}")
    lines.append("{{< instructions >}}")
    for idx, step in enumerate(recipe.get("instructions", []), 1):
        lines.append(f"{idx}. {step}")
    lines.append("{{< /instructions >}}")

    lines.append("{{< ingredients >}}")
    for ing in recipe.get("ingredients", []):
        lines.append(f"- {ing}")
    lines.append("{{< /ingredients >}}")

    if recipe.get("hints"):
        lines.append("{{< hints >}}")
        for hint in recipe.get("hints", []):
            lines.append(f"- {hint}")
        lines.append("{{< /hints >}}")

    if img_data.get("gallery"):
        lines.append("{{< gallery >}}")

    lines.append("{{< /recipe-grid >}}")

    return "\n".join(lines)


def generate_md(include_dev: bool = False):
    if not os.path.exists(GROUPS_PATH):
        print(f"❌ recipe_groups.toml not found at {GROUPS_PATH}")
        return

    groups = load_groups()

    # Fresh output directory
    if os.path.exists(HUGO_CONTENT_DIR):
        shutil.rmtree(HUGO_CONTENT_DIR)
    os.makedirs(HUGO_CONTENT_DIR)

    # Top-level _index.md — cascade print output to all recipe pages
    with open(os.path.join(HUGO_CONTENT_DIR, "_index.md"), "w") as f:
        f.write('---\ntitle: "Recipes"\ncascade:\n  outputs:\n    - HTML\n    - print\n---\n')

    for group in groups:
        group_name = group["name"]
        folder = group_folder(group_name)

        recipes = ordered_recipes(group, include_dev)

        # Always write the section _index.md (weight preserves recipe_groups.toml order)
        section_dir = os.path.join(HUGO_CONTENT_DIR, folder)
        os.makedirs(section_dir, exist_ok=True)
        with open(os.path.join(section_dir, "_index.md"), "w") as f:
            weight = groups.index(group) + 1
            f.write(f'---\ntitle: "{group_name}"\nweight: {weight}\n---\n')

        for recipe_id, recipe_data in recipes:
            recipe_bundle_dir = os.path.join(section_dir, recipe_id)
            os.makedirs(recipe_bundle_dir, exist_ok=True)

            md_content = generate_markdown(recipe_data, group_name)
            with open(os.path.join(recipe_bundle_dir, "index.md"), "w", encoding="utf-8") as f:
                f.write(md_content)

            # Copy images
            img_data = recipe_data.get("images", {})
            images = [img_data.get("thumbnail"), img_data.get("banner")]
            images += img_data.get("gallery", [])
            for img_name in set(filter(None, images)):
                src = os.path.join(RECIPE_DIR, folder, recipe_id, img_name)
                dst = os.path.join(recipe_bundle_dir, img_name)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                else:
                    print(f"⚠️  Image not found: {src}")

        label = " [DEV]" if include_dev else ""
        print(f"  {group_name}: {len(recipes)} recipe(s){label}")

    print("✅ All recipes compiled successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile recipe TOMLs to Hugo markdown.")
    parser.add_argument("--dev", action="store_true", help="Include dev recipes.")
    args = parser.parse_args()
    generate_md(include_dev=args.dev)
