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
	@echo "✅ PDF Ready: $(OUT)"

# --- Hugo Build ---
hugo: website-init compose
	@echo "🌐 Syncing data and building Hugo site..."
	cd $(HUGO_DIR) && hugo --minify
	@echo "✅ Website Ready in $(HUGO_DIR)/public"

# --- NEW: Serve Development Site ---
serve: website-init compose
	@echo "🚀 Starting Hugo development server at http://localhost:1313"
	cd $(HUGO_DIR) && hugo server -D

# --- NEW: Watch PDF (Live Recompile) ---
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
	# Delete all .md files EXCEPT _index.md
	# find $(HUGO_DIR)/content.en/recipes -name "*.md" ! -name "_index.md" -delete