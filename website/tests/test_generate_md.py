"""
Tests for generate_md.generate_markdown()

Run from the website/ directory:
    python -m pytest tests/
    python -m unittest discover tests/
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generate_md import generate_markdown


def parse_frontmatter(md: str) -> tuple[dict, str]:
    """Split generated markdown into a dict of front matter values and body text."""
    lines = md.split("\n")
    assert lines[0] == "---", "Expected opening ---"
    end = lines.index("---", 1)
    fm = {}
    for line in lines[1:end]:
        key, _, val = line.partition(": ")
        fm[key.strip()] = val.strip()
    body = "\n".join(lines[end + 1:])
    return fm, body


class TestFrontmatter(unittest.TestCase):

    def test_title(self):
        recipe = {"title": "Pão de Queijo", "ingredients": [], "instructions": []}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertEqual(fm["title"], '"Pão de Queijo"')

    def test_date_is_set(self):
        recipe = {"title": "Test", "ingredients": [], "instructions": []}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        import re
        self.assertRegex(fm["date"], r"\d{4}-\d{2}-\d{2}")

    def test_category_from_chapter(self):
        recipe = {"title": "T", "ingredients": [], "instructions": []}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Mains"))
        self.assertIn("Mains", fm["categories"])

    def test_category_from_recipe_overrides_chapter(self):
        recipe = {"title": "T", "category": "Sauces", "ingredients": [], "instructions": []}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Mains"))
        self.assertIn("Sauces", fm["categories"])

    def test_tags_empty(self):
        recipe = {"title": "T", "ingredients": [], "instructions": []}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertEqual(fm["tags"], "[]")

    def test_tags_present(self):
        recipe = {"title": "T", "tags": ["Brazilian", "Vegetarian"], "ingredients": [], "instructions": []}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertIn("Brazilian", fm["tags"])
        self.assertIn("Vegetarian", fm["tags"])

    def test_blurb_becomes_description(self):
        recipe = {"title": "T", "blurb": "A tasty dish.", "ingredients": [], "instructions": []}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertIn("A tasty dish.", fm["description"])

    def test_no_blurb_no_description(self):
        recipe = {"title": "T", "ingredients": [], "instructions": []}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertNotIn("description", fm)

    def test_banner(self):
        recipe = {"title": "T", "ingredients": [], "instructions": [], "images": {"banner": "banner.jpg"}}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertEqual(fm["banner"], '"banner.jpg"')

    def test_thumbnail(self):
        recipe = {"title": "T", "ingredients": [], "instructions": [], "images": {"thumbnail": "thumb.jpg"}}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertIn("thumb.jpg", fm["thumbnail"])

    def test_no_thumbnail_key_when_absent(self):
        recipe = {"title": "T", "ingredients": [], "instructions": [], "images": {}}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertNotIn("thumbnail", fm)

    def test_gallery_in_frontmatter(self):
        imgs = ["g1.jpg", "g2.jpg"]
        recipe = {"title": "T", "ingredients": [], "instructions": [], "images": {"gallery": imgs}}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertIn("g1.jpg", fm["gallery"])
        self.assertIn("g2.jpg", fm["gallery"])

    def test_no_gallery_key_when_absent(self):
        recipe = {"title": "T", "ingredients": [], "instructions": [], "images": {}}
        fm, _ = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertNotIn("gallery", fm)


class TestBody(unittest.TestCase):

    def test_blurb_italic_intro(self):
        recipe = {"title": "T", "blurb": "Delicious!", "ingredients": [], "instructions": []}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertIn("_Delicious!_", body)

    def test_instructions_numbered(self):
        recipe = {"title": "T", "ingredients": [], "instructions": ["Step one", "Step two"]}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertIn("1. Step one", body)
        self.assertIn("2. Step two", body)

    def test_ingredients_bulleted(self):
        recipe = {"title": "T", "ingredients": ["Flour", "Eggs"], "instructions": []}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertIn("- Flour", body)
        self.assertIn("- Eggs", body)

    def test_hints_shortcode_present(self):
        recipe = {"title": "T", "ingredients": [], "instructions": [], "hints": ["Don't burn it."]}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertIn("{{< hints >}}", body)
        self.assertIn("- Don't burn it.", body)
        self.assertIn("{{< /hints >}}", body)

    def test_hints_shortcode_absent_when_no_hints(self):
        recipe = {"title": "T", "ingredients": [], "instructions": []}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertNotIn("{{< hints >}}", body)

    def test_gallery_shortcode_present(self):
        recipe = {"title": "T", "ingredients": [], "instructions": [], "images": {"gallery": ["g.jpg"]}}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertIn("{{< gallery >}}", body)

    def test_gallery_shortcode_absent_when_no_images(self):
        recipe = {"title": "T", "ingredients": [], "instructions": [], "images": {}}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        self.assertNotIn("{{< gallery >}}", body)

    def test_recipe_grid_wraps_content(self):
        recipe = {"title": "T", "ingredients": ["Salt"], "instructions": ["Mix."]}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        grid_open = body.index("{{< recipe-grid >}}")
        grid_close = body.index("{{< /recipe-grid >}}")
        self.assertLess(grid_open, grid_close)
        ingredients_pos = body.index("- Salt")
        instructions_pos = body.index("1. Mix.")
        self.assertGreater(ingredients_pos, grid_open)
        self.assertGreater(instructions_pos, grid_open)
        self.assertLess(ingredients_pos, grid_close)
        self.assertLess(instructions_pos, grid_close)

    def test_hints_inside_recipe_grid(self):
        recipe = {"title": "T", "ingredients": [], "instructions": [], "hints": ["Tip."]}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        grid_close = body.index("{{< /recipe-grid >}}")
        hints_pos = body.index("{{< hints >}}")
        self.assertLess(hints_pos, grid_close)

    def test_gallery_inside_recipe_grid(self):
        recipe = {"title": "T", "ingredients": [], "instructions": [], "images": {"gallery": ["g.jpg"]}}
        _, body = parse_frontmatter(generate_markdown(recipe, "Starters"))
        grid_close = body.index("{{< /recipe-grid >}}")
        gallery_pos = body.index("{{< gallery >}}")
        self.assertLess(gallery_pos, grid_close)


if __name__ == "__main__":
    unittest.main()
