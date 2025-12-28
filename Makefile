# --- Settings ---
CC       = xelatex
LATEXMK  = latexmk
SRC      = src/main.tex
OUT      = cookbook.pdf
BUILDDIR = build

export PATH := /Library/TeX/texbin:/opt/homebrew/bin:/usr/local/bin:$(PATH)
# This allows LaTeX to find your .sty and .tex files inside src/
export TEXINPUTS := .:src:styles:$(TEXINPUTS)

.PHONY: all check images clean rebuild

all: check $(OUT)

check:
	chmod +x scripts/check_deps.sh
	./scripts/check_deps.sh

$(OUT): $(SRC)
	@bash scripts/generate_inputs.sh
	@mkdir -p $(BUILDDIR)
	# -xelatex: Forces the engine
	# -jobname: Ensures the output is named 'cookbook'
	# -outdir:  Keeps the root clean
	$(LATEXMK) -xelatex -interaction=nonstopmode -halt-on-error -file-line-error \
		-jobname=cookbook -outdir=$(BUILDDIR) $(SRC)
	cp $(BUILDDIR)/$(OUT) .

clean:
	rm -rf $(BUILDDIR)
	rm -f $(OUT)
	rm -f images/*.aux images/*.log images/*.pdf

rebuild: clean all