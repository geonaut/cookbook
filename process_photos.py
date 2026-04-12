#!/usr/bin/env python3
"""
process_photos.py — resize and optionally tone-grade recipe photos.

For each recipe with a [photos] section in recipe.toml, reads raw source
filenames from recipes/<group>/<recipe>/raw/, runs ffmpeg to produce sized
outputs, then updates the images field in recipe.toml.

Output filenames (written alongside recipe.toml):
  {name}_thumb.jpg   — 600×400   (thumbnail)
  {name}_banner.jpg  — 1400×560  (banner / hero)
  {name}_gallery.jpg — 1200×800  (gallery)

LUT (optional): place a tone.cube file at photos/tone.cube to apply
consistent colour grading to all photos. Skipped if absent.

Usage:
    python3 process_photos.py           # skip already up-to-date outputs
    python3 process_photos.py --force   # reprocess everything
"""

import os
import re
import tomllib
import subprocess
import argparse
from pathlib import Path

SCRIPT_DIR  = Path(__file__).parent
RECIPE_DIR  = SCRIPT_DIR / "recipes"
GROUPS_PATH = RECIPE_DIR / "recipe_groups.toml"
LUT_PATH    = SCRIPT_DIR / "photos" / "tone.cube"

SIZES = {
    "thumb":   (600,  400),
    "banner":  (1400, 560),
    "gallery": (1200, 800),
}


def group_folder(name: str) -> str:
    return name.lower().replace(" ", "_")


def find_raw(recipe_dir: Path, stem: str) -> Path | None:
    # stems starting with "photos/" are resolved from the repo root,
    # looking in a raw/ subdirectory alongside the stem's parent
    if stem.startswith("photos/"):
        raw_dir = SCRIPT_DIR / Path(stem).parent / "raw"
        for ext in ("jpg", "jpeg", "JPG", "JPEG", "png", "PNG"):
            p = raw_dir / f"{Path(stem).name}.{ext}"
            if p.exists():
                return p
        return None
    for ext in ("jpg", "jpeg", "JPG", "JPEG", "png", "PNG"):
        p = recipe_dir / "raw" / f"{stem}.{ext}"
        if p.exists():
            return p
    return None


def is_stale(src: Path, out: Path, lut: Path | None) -> bool:
    if not out.exists():
        return True
    out_mtime = out.stat().st_mtime
    if src.stat().st_mtime > out_mtime:
        return True
    if lut and lut.exists() and lut.stat().st_mtime > out_mtime:
        return True
    return False


def run_ffmpeg(src: Path, out: Path, width: int, height: int, lut: Path | None) -> bool:
    scale = f"scale={width}:{height}:force_original_aspect_ratio=increase"
    crop  = f"crop={width}:{height}"
    vf    = f"lut3d={lut},{scale},{crop}" if (lut and lut.exists()) else f"{scale},{crop}"
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-vf", vf, "-q:v", "2", str(out)],
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"    ✗ ffmpeg: {result.stderr.decode().strip().splitlines()[-1]}")
        return False
    return True


def update_images_in_toml(toml_path: Path, images: dict):
    gallery_str = "[" + ", ".join(f'"{g}"' for g in images["gallery"]) + "]"
    new_line = (
        f'images = {{thumbnail = "{images["thumbnail"]}", '
        f'banner = "{images["banner"]}", '
        f'gallery = {gallery_str}}}'
    )
    text = toml_path.read_text()
    text = re.sub(r"^images\s*=\s*\{[^\n]*\}$", new_line, text, flags=re.MULTILINE)
    toml_path.write_text(text)


def process_recipe(recipe_dir: Path, force: bool):
    toml_path = recipe_dir / "recipe.toml"
    with open(toml_path, "rb") as f:
        recipe = tomllib.load(f)

    photos = recipe.get("photos")
    if not photos:
        return

    lut     = LUT_PATH if LUT_PATH.exists() else None
    images  = {"thumbnail": "", "banner": "", "gallery": []}
    updated = False

    def process(stem: str, role: str) -> str | None:
        nonlocal updated
        src = find_raw(recipe_dir, stem)
        if not src:
            print(f"    ⚠️  raw not found: {stem}")
            return None
        w, h     = SIZES[role]
        out_stem = Path(stem).name  # handles "photos/general/IMG_1955" → "IMG_1955"
        out      = recipe_dir / f"{out_stem}_{role}.jpg"
        if force or is_stale(src, out, lut):
            if run_ffmpeg(src, out, w, h, lut):
                print(f"    ✓ {out.name}")
                updated = True
        return out.name

    if stem := photos.get("thumbnail"):
        images["thumbnail"] = process(stem, "thumb") or ""

    if stem := photos.get("banner"):
        images["banner"] = process(stem, "banner") or ""

    for stem in photos.get("gallery", []):
        if name := process(stem, "gallery"):
            images["gallery"].append(name)

    if updated:
        update_images_in_toml(toml_path, images)
        print(f"    → updated images field")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Reprocess all photos")
    args = parser.parse_args()

    with open(GROUPS_PATH, "rb") as f:
        groups = tomllib.load(f)["groups"]

    for group in groups:
        group_dir = RECIPE_DIR / group_folder(group["name"])
        if not group_dir.is_dir():
            continue
        for entry in sorted(group_dir.iterdir()):
            if not entry.is_dir() or not (entry / "recipe.toml").exists():
                continue
            with open(entry / "recipe.toml", "rb") as f:
                has_photos = "photos" in tomllib.load(f)
            if not has_photos:
                continue
            print(entry.name)
            process_recipe(entry, args.force)


if __name__ == "__main__":
    main()
