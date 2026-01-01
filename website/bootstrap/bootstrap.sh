#!/bin/zsh

# --- Configuration ---
HUGO_VERSION="extended" # 'extended' is recommended for many themes
SITE_DIR="website"

echo "🔍 Checking dependencies..."

# 1. Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew is installed."
fi

# 2. Check/Install Hugo
if ! command -v hugo &> /dev/null; then
    echo "📦 Installing Hugo..."
    brew install hugo
else
    echo "✅ Hugo is already installed."
fi

# 3. Create Hugo Site if it doesn't exist
# Note: We run this from the root, so we check if the directory exists
if [ ! -d "$SITE_DIR" ] || [ -z "$(ls -A $SITE_DIR)" ]; then
    echo "🏗️  Initializing Hugo site in /$SITE_DIR..."
    hugo new site "$SITE_DIR" --force
else
    echo "✅ Hugo directory already exists."
fi

# 4. Install the 'Hugo Book' theme
if [ ! -d "$SITE_DIR/themes/hugo-book" ]; then
    echo "📚 Installing Hugo Book theme..."
    cd "$SITE_DIR"
    git init
    git submodule add https://github.com/alex-shpak/hugo-book themes/hugo-book
    echo 'theme = "hugo-book"' >> hugo.toml
    cd ..
else
    echo "✅ Hugo Book theme is already present."
fi

# 5. Create Symlinks for shared assets
echo "🔗 Linking images to Hugo static folder..."
mkdir -p "$SITE_DIR/static"
# Remove old link if it exists to avoid nesting, then create new one
rm -f "$SITE_DIR/static/images"
ln -s ../../images "$SITE_DIR/static/images"

echo "✨ Website environment is ready!"