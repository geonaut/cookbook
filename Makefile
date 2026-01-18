# --- Configuration ---
SRC        = pdf/src/main.tex
OUT        = cookbook.pdf
BUILDDIR   = build
HUGO_DIR   = website
BOOTSTRAP  = $(HUGO_DIR)/bootstrap/bootstrap.sh

# --- Commands ---
LATEXMK    = latexmk
PYTHON     = python3

.PHONY: all pdf hugo website-init compose clean serve watch

# Default: Build both PDF and Website
all: pdf hugo

# --- PDF Build ---
pdf: compose
	@bash pdf/scripts/generate_inputs.sh
	@echo "🖨️  Building LaTeX PDF..."
	@mkdir -p $(BUILDDIR)
	$(LATEXMK) -pdf -xelatex -outdir=$(BUILDDIR) -jobname=cookbook $(SRC)
	@cp $(BUILDDIR)/$(OUT) .
	# Ensure the PDF is available to Hugo's static folder for linking
	@mkdir -p $(HUGO_DIR)/static
	@cp $(BUILDDIR)/$(OUT) $(HUGO_DIR)/static/cookbook.pdf
	@echo "✅ PDF Ready: $(OUT)"

# --- Hugo Build ---
hugo: website-init compose
	@echo "🌐 Syncing data and building Hugo site..."
	# Using --gc (Garbage Collect) to clean up old processed assets
	cd $(HUGO_DIR) && hugo --minify --gc
	@echo "✅ Website Ready in $(HUGO_DIR)/public"

# --- Serve Development Site ---
serve: website-init compose
	@echo "🚀 Starting Hugo development server at http://localhost:1313"
	cd $(HUGO_DIR) && hugo server -D

# --- Watch PDF (Live Recompile) ---
watch:
	@echo "👀 Watching for changes to recompile PDF..."
	$(LATEXMK) -pvc -pdf -xelatex -outdir=$(BUILDDIR) -jobname=cookbook $(SRC)

# --- Data Composition ---
compose:
	@echo "🐍 Compiling recipes from TOML to LaTeX and Markdown..."
	$(PYTHON) pdf/generate_tex.py
	$(PYTHON) $(HUGO_DIR)/generate_md.py

# --- Website Environment Setup ---
website-init:
	@echo "⚙️  Ensuring website dependencies are met..."
	@chmod +x $(BOOTSTRAP)
	@zsh $(BOOTSTRAP)

# --- Cleanup ---
clean:
	@echo "🧹 Cleaning all build artifacts..."
	-$(LATEXMK) -C -outdir=$(BUILDDIR) $(SRC)
	rm -rf $(BUILDDIR)
	rm -f $(OUT) 
	rm -f pdf/src/full_cookbook.tex
	rm -rf $(HUGO_DIR)/public
	# Clean up Hugo resources/gen to fix those git tracking/build issues
	rm -rf $(HUGO_DIR)/resources/_gen
	# Remove the symlink that was causing the "File exists" error
	rm -f $(HUGO_DIR)/static/images

PYTHON := python3
HUGO := hugo
MAP_SCRIPT := map/process_map_data.py
MAP_SOURCE := "Geonaut's North London Foodie Map.kmz"
MAP_OUT_DIR := .

sync-map:
	@echo "📍 Extracting latest map pins..."
	@$(PYTHON) $(MAP_SCRIPT)