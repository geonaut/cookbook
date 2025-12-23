# LaTeX Cookbook (A4, two-sided)

This repository contains a LaTeX cookbook template:
- A4, twoside layout for printing and binding
- full-bleed cover
- Table of Contents
- chapter title pages
- sauces as compact mini-recipes (2–3 per page)
- one recipe per page for other sections
- optional left-hand photo pages (photo on verso / recipe on recto)

## Requirements

- A working TeX distribution (MacTeX / TeX Live)
- pdflatex
- latexmk
- kpsewhich (provided by TeX distribution)

Recommended (macOS):
- Install MacTeX:
  brew install --cask mactex

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

## Notes on editor/IDE builds
- If an editor or CI job prints an error like:
  "Error: spawn latexmk ENOENT" or "latexmk: Command not found"
  it usually means the editor's runtime environment does not include the TeX/bin locations (Homebrew / MacTeX) in $PATH.
- Permanent fixes:
  - Add TeX bin dirs to your shell and GUI environment (example for macOS):
      export PATH="/Library/TeX/texbin:/opt/homebrew/bin:/usr/local/bin:$PATH"
    Put that in ~/.zshrc or the environment configuration your editor uses.
  - Or configure your editor's LaTeX build task to call `make` instead of invoking `latexmk` directly.
- This repository includes a small proxy script at `./latexmk` that will try to forward to a system latexmk if available; it's a convenience but not a substitute for fixing the editor/CI PATH.

## Project layout

- main.tex
- preamble.tex
- cover.tex
- toc.tex
- chapters/
- images/
- build/check_deps.sh
- Makefile