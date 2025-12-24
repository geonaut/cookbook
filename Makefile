# Build Makefile for LaTeX cookbook
# - runs dependency check
# - builds placeholder images
# - builds the LaTeX document and outputs $(OUT)

# Ensure common TeX and Homebrew bin dirs are available to all recipe shells
# (helps when make runs in a non-login/non-interactive shell).
export PATH := /Library/TeX/texbin:/opt/homebrew/bin:/usr/local/bin:$(PATH)

# Add the src directory to TeX's input path so \input{cover.tex} etc. resolve
# correctly when using -output-directory (which changes where outputs go).
export TEXINPUTS := src:$(TEXINPUTS)

CC = pdflatex
LATEXMK = latexmk
# Note: latexmk will read a project-local 'latexmkrc' (or '.latexmkrc') if present;
# otherwise it falls back to ~/.latexmkrc. You don't need both — use a project-local
# file for repo-specific settings and ~/.latexmkrc for personal defaults.
SRC = src/main.tex
OUT = cookbook.pdf

SRCDIR := $(dir $(SRC))
SRCBASE := $(basename $(notdir $(SRC)))
SRC_PDF := $(SRCDIR)$(SRCBASE).pdf

.PHONY: all check images clean rebuild

all: check images $(OUT)

check:
	chmod +x build/check_deps.sh
	# Ensure common TeX and Homebrew bin dirs are available to the check script
	PATH=/Library/TeX/texbin:/opt/homebrew/bin:/usr/local/bin:$(PATH) ./build/check_deps.sh

images:
	@echo "Generating placeholder images..."
	@mkdir -p images
	$(CC) -interaction=nonstopmode -halt-on-error -output-directory=images images/cover.tex

$(OUT): $(SRC)
	@echo "Generating auto-inputs..."
	@bash build/generate_inputs.sh
	@echo "Building LaTeX document..."
	@mkdir -p build
	@echo "Running latexmk (see build/latexmk.log)..."
	@{ $(LATEXMK) -pdf -f -pdflatex="$(CC) -interaction=nonstopmode -file-line-error" $(SRC) > build/latexmk.log 2>&1; rc=$$?; \
	  if [ $$rc -ne 0 ]; then \
	    echo "latexmk failed with exit $$rc — showing logs (last 200 lines)"; \
	    echo "---- build/latexmk.log ----"; tail -n 200 build/latexmk.log || true; \
	    if [ -f src/texput.log ]; then echo "---- src/texput.log ----"; tail -n 200 src/texput.log || true; fi; \
	    if [ -f images/cover.log ]; then echo "---- images/cover.log ----"; tail -n 200 images/cover.log || true; fi; \
	    exit $$rc; \
	  fi; \
	}
	@echo "Locating generated PDF..."
	@{ \
	  OUT_SRC=""; \
	  if [ -f "$(SRC_PDF)" ]; then OUT_SRC="$(SRC_PDF)"; \
	  elif [ -f "$(SRCBASE).pdf" ]; then OUT_SRC="$(SRCBASE).pdf"; \
	  elif [ -f "main.pdf" ]; then OUT_SRC="main.pdf"; \
	  elif [ -f "build/$(SRCBASE).pdf" ]; then OUT_SRC="build/$(SRCBASE).pdf"; \
	  fi; \
	  if [ -n "$$OUT_SRC" ] && [ -f "$$OUT_SRC" ]; then \
	    mv -f "$$OUT_SRC" "$(OUT)"; \
	    echo "Built $(OUT) (from $$OUT_SRC)"; \
	    exit 0; \
	  else \
	    echo "Failed to build $(OUT) (no PDF produced at expected locations)"; \
	    exit 1; \
	  fi; \
	}

clean:
	@# Remove generated outputs but preserve helper scripts in build/
	@# Keep build/check_deps.sh and build/generate_inputs.sh
	@mkdir -p build
	@find build -type f ! -name check_deps.sh ! -name generate_inputs.sh -delete || true
	@find build -type d -empty -delete || true
	@rm -f $(OUT)
	@rm -f images/*.aux images/*.log images/*.pdf || true

# convenience: fully clean and rebuild
rebuild: clean all

.PHONY: show-logs debug

# convenience: run pdflatex once directly and capture its log for diagnosis
debug:
	@echo "Running pdflatex once and saving log to build/pdflatex.log..."
	@mkdir -p build
	@{ $(CC) -interaction=nonstopmode -file-line-error -output-directory=build $(SRC) > build/pdflatex.log 2>&1; rc=$$?; \
	  echo "pdflatex exit code: $$rc"; \
	  echo "---- build/pdflatex.log (tail) ----"; tail -n 200 build/pdflatex.log || true; \
	  exit $$rc; \
	}

show-logs:
	@echo "---- build/latexmk.log (tail) ----"; [ -f build/latexmk.log ] && tail -n 200 build/latexmk.log || echo "(no build/latexmk.log)"; \
	[ -f build/pdflatex.log ] && (echo "---- build/pdflatex.log (tail) ----"; tail -n 200 build/pdflatex.log) || true; \
	[ -f src/texput.log ] && (echo "---- src/texput.log (tail) ----"; tail -n 200 src/texput.log) || true; \
	[ -f images/cover.log ] && (echo "---- images/cover.log (tail) ----"; tail -n 200 images/cover.log) || true