# LaTeX Cookbook (A4, two-sided)

This repository contains a LaTeX cookbook template:
- A4, twoside layout for printing and binding
- full-bleed cover
- Table of Contents
- chapter title pages
- sauces as compact mini-recipes (2–3 per page)
- one recipe per page for other sections
- optional left-hand photo pages

## Requirements

- A working TeX distribution (MacTeX / TeX Live) e.g. `brew install --cask mactex`
- pdflatex
- latexmk
- kpsewhich (provided by TeX distribution)
  
## Quick setup & build

1. Run the build (Makefile will run the dependency check first):
   cd /Users/oliverbazely/Coding/cookbook
   make

   The Makefile runs `build/check_deps.sh` first; if required commands or common LaTeX packages are missing the script will exit non-zero and print suggested actions.

2. Optional: run dependency checker manually:
   chmod +x build/check_deps.sh
   PATH=/Library/TeX/texbin:/opt/homebrew/bin:/usr/local/bin:$$PATH ./build/check_deps.sh

Notes:
- kpsewhich (and pdflatex) are included with TeX Live / MacTeX. On macOS MacTeX places binaries in /Library/TeX/texbin; if your shell or CI environment does not include that directory in PATH, `make` may not see these commands even though MacTeX is installed. Add /Library/TeX/texbin (and Homebrew bin dirs like /opt/homebrew/bin or /usr/local/bin) to your PATH to fix that.
- To install on macOS:
  - MacTeX (full): brew install --cask mactex
  - latexmk: brew install latexmk