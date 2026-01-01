import tomllib
import os

# --- Path Resolution ---
# This finds the absolute path to the 'pdf' folder where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# This finds the project root (one level up from pdf/)
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

def build_outputs():
    # --- FIXED PATHS ---
    # You mentioned the config is at: pdf/pdf_config.toml
    CONFIG_PATH = os.path.join(SCRIPT_DIR, "pdf_config.toml")
    
    # Recipes are in the project root: /recipes
    RECIPE_DIR = os.path.join(ROOT_DIR, "recipes")
    
    # LaTeX Output Path: root/pdf/src/full_cookbook.tex
    LATEX_OUT = os.path.join(SCRIPT_DIR, "src", "full_cookbook.tex")
    
    # Hugo Output Path: root/website/content/recipes/
    HUGO_CONTENT_DIR = os.path.join(ROOT_DIR, "website", "content", "recipes")

    # Ensure directories exist
    os.makedirs(os.path.dirname(LATEX_OUT), exist_ok=True)
    os.makedirs(HUGO_CONTENT_DIR, exist_ok=True)

    # 1. Load Master Config
    try:
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find config at {CONFIG_PATH}")
        return

    full_tex = []
    defaults = config.get("defaults", {"columns": 1, "show_image": True})

    # 2. Iterate through Chapters and Recipes
    for chapter in config.get("chapters", []):
        chapter_name = chapter['name']
        full_tex.append(f"\\chapter{{{chapter_name}}}")
        
        for r_entry in chapter.get("recipes", []):
            recipe_id = r_entry['id']
            recipe_file = os.path.join(RECIPE_DIR, f"{recipe_id}.toml")
            
            try:
                with open(recipe_file, "rb") as rf:
                    recipe_raw_bytes = rf.read()
                    recipe_raw_text = recipe_raw_bytes.decode("utf-8")
                    rf.seek(0)
                    r_data = tomllib.load(rf)
            except FileNotFoundError:
                print(f"⚠️ Warning: Recipe {recipe_id}.toml not found in {RECIPE_DIR}")
                continue
                
            # --- A. LATEX GENERATION ---
            cols = r_entry.get("columns", defaults.get("columns", 1))
            show_img = r_entry.get("show_image", defaults.get("show_image", True))

            full_tex.append(f"\\section{{{r_data['title']}}}")
            full_tex.append(f"\\begin{{recipeIngredients}}{{{cols}}}")
            for ing in r_data['ingredients']:
                full_tex.append(f"  \\item {ing}")
            full_tex.append(f"\\end{{recipeIngredients}}")

            full_tex.append("\\subsection*{Method}")
            full_tex.append("\\begin{enumerate}")
            for step in r_data['instructions']:
                full_tex.append(f"  \\item {step}")
            full_tex.append("\\end{enumerate}")

            if show_img and r_data.get('image'):
                img_path = r_data['image']
                full_tex.append("\\vfill")
                full_tex.append("{\\centering")
                full_tex.append(f"\\includegraphics[width=\\textwidth, height=\\dimexpr\\pagegoal-\\pagetotal-3\\baselineskip\\relax, keepaspectratio]{{images/{img_path}}}\\par}}")

            full_tex.append("\\newpage")

            # --- B. HUGO MARKDOWN GENERATION ---
            hugo_file_path = os.path.join(HUGO_CONTENT_DIR, f"{recipe_id}.md")
       # Inside the Hugo generation loop in compose.py
            with open(hugo_file_path, "w") as hf:
                hf.write("+++\n")
                hf.write(recipe_raw_text.strip())
                hf.write(f"\nchapter = \"{chapter_name}\"")
                hf.write("\ntype = \"recipes\"")  # This links it to layouts/recipes/single.html
                hf.write("\n+++\n")

    # 3. Save LaTeX Output
    with open(LATEX_OUT, "w") as f:
        f.write("\n".join(full_tex))
    
    print(f"✅ LaTeX: {LATEX_OUT}")
    print(f"✅ Hugo Content: {HUGO_CONTENT_DIR}")

if __name__ == "__main__":
    build_outputs()