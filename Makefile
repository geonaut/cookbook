# --- Configuration ---
PYTHON   ?= mise exec -- python3
LATEXMK  ?= latexmk
HUGO_DIR  = website

.PHONY: all pdf pdf-dev site build serve clean sync-map photos

## Generate everything (production)
all: pdf site
	cp pdf/build/cookbook.pdf $(HUGO_DIR)/static/cookbook.pdf

## Compile production PDF (skips dev=true recipes)
pdf:
	$(PYTHON) pdf/generate_tex.py
	$(LATEXMK) -pdf -xelatex -outdir=pdf/build -jobname=cookbook pdf/src/main.tex

## Compile dev PDF (all recipes including dev=true, no images — use for printing/editing)
pdf-dev:
	$(PYTHON) pdf/generate_tex.py --dev
	$(LATEXMK) -pdf -xelatex -outdir=pdf/build -jobname=cookbook_dev pdf/src/main_dev.tex

## Generate Hugo markdown from recipe TOMLs
site:
	$(PYTHON) $(HUGO_DIR)/generate_md.py

## Generate markdown + build Hugo site
build: site
	cd $(HUGO_DIR) && hugo --gc --minify

## Start Hugo dev server (includes draft content)
serve: site
	cd $(HUGO_DIR) && hugo server -D --disableFastRender --ignoreCache

## Process raw recipe photos → sized outputs, update images field in recipe.toml
photos:
	$(PYTHON) process_photos.py

## Sync foodie map data from KMZ export
sync-map:
	$(PYTHON) map/process_map_data.py

## Remove all generated files
clean:
	rm -f pdf/src/full_cookbook.tex pdf/src/full_cookbook_dev.tex
	rm -rf pdf/build
	rm -rf $(HUGO_DIR)/content.en/recipes
	rm -rf $(HUGO_DIR)/public
	rm -rf $(HUGO_DIR)/resources/_gen
