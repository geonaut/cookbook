#!/bin/zsh

echo "🔍 Checking dependencies..."

# Check for Hugo
if ! command -v hugo &> /dev/null; then
    echo "📦 Hugo not found. Installing via Homebrew..."
    brew install hugo
else
    echo "✅ Hugo is installed ($(hugo version | head -1))."
fi

# Symlink shared images into Hugo's static folder
echo "🔗 Linking images to Hugo static folder..."
mkdir -p static
rm -f static/images
ln -s ../../../images static/images

echo "✨ Website environment is ready!"
