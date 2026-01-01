#!/usr/bin/env bash
set -euo pipefail

MISSING=0

# Check if a command is on PATH; if not, also check common fallback locations.
check_cmd() {
	name="$1"
	install_hint="$2"
	alt_paths=(
		"/Library/TeX/texbin/$name"
		"/opt/homebrew/bin/$name"
		"/usr/local/bin/$name"
		"/usr/texbin/$name"
	)
	if command -v "$name" >/dev/null 2>&1; then
		printf "Found: %s (on PATH)\n" "$name"
		return 0
	fi

	for p in "${alt_paths[@]}"; do
		if [ -x "$p" ]; then
			printf "Found: %s at %s\n" "$name" "$p"
			printf "  Note: the binary is not on PATH when 'make' runs. Add its parent dir to PATH, for example:\n"
			printf "    export PATH=\"%s:\$PATH\"\n\n" "$(dirname "$p")"
			return 0
		fi
	done

	printf "Missing: %s\n  Install hint: %s\n\n" "$name" "$install_hint"
	MISSING=1
}

OS="$(uname -s 2>/dev/null || echo Unknown)"

check_cmd pdflatex "macOS: brew install --cask mactex  | Debian/Ubuntu: sudo apt-get install texlive-latex-recommended texlive-latex-extra"
check_cmd kpsewhich "Provided by TeX Live / MacTeX. On macOS: brew install --cask mactex"
check_cmd latexmk "macOS: brew install latexmk | Debian/Ubuntu: sudo apt-get install latexmk"

if [ "$MISSING" -ne 0 ]; then
	printf "One or more dependencies are missing or not on PATH.\n"
	if [ "$OS" = "Darwin" ]; then
		printf "\nmacOS notes:\n"
		printf " - MacTeX installs TeX binaries into /Library/TeX/texbin. Ensure that directory is on PATH in non-login shells used by tools like 'make'.\n"
		printf "   Example (bash/zsh): add to ~/.zshrc or ~/.bash_profile:\n"
		printf "     export PATH=\"/Library/TeX/texbin:\$PATH\"\n"
		printf " - Homebrew installs for ARM (Apple Silicon) go under /opt/homebrew/bin; for Intel they may be under /usr/local/bin.\n"
	else
		printf "Refer to your OS package manager to install a TeX distribution and latexmk.\n"
	fi
	exit 1
else
	printf "All required dependencies are present.\n"
	exit 0
fi
