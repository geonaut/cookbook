# --- Settings ---
CC       = xelatex
LATEXMK  = latexmk
SRC      = src/main.tex
OUT      = cookbook.pdf
BUILDDIR = build

export PATH := /Library/TeX/texbin:/opt/homebrew/bin:/usr/local/bin:$(PATH)
export TEXINPUTS := src:$(TEXINPUTS)

.PHONY: all check images clean rebuild

all: check images $(OUT)

check:
	chmod +x build/check_deps.sh
	./build/check_deps.sh

$(OUT): $(SRC)
	@bash build/generate_inputs.sh
	@mkdir -p $(BUILDDIR)
	# -xelatex: Use XeTeX engine
	# -jobname: Force the output PDF to be named 'cookbook'
	# -outdir:  Put all auxiliary files in 'build'
	$(LATEXMK) -xelatex -jobname=$(basename $(OUT)) -outdir=$(BUILDDIR) -f -interaction=nonstopmode $(SRC)
	cp $(BUILDDIR)/$(OUT) .

clean:
	rm -f $(OUT)
	rm -f images/*.aux images/*.log images/*.pdf

rebuild: clean all