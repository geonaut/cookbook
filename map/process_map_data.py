import os
import re
import urllib.request
import xml.etree.ElementTree as ET

# Configuration
MAP_ID = "1F2hS3T8QPhS3uK8dJCNxfgFnxC-DRmM"
# Reverting to the simpler, direct URL structure
MAP_URL = f"https://www.google.com/maps/d/kml?mid={MAP_ID}&forcekml=1"
OUTPUT_FILE = "website/content.en/foodie-map.md"
TOML_FILE = "map/location_comments.toml" 

def load_manual_metadata():
    """Parses the 'Name' = 'Comment' format from your location_comments.toml."""
    metadata = {}
    if not os.path.exists(TOML_FILE):
        print(f"⚠️ TOML file not found at {TOML_FILE}")
        return metadata
    
    print(f"📖 Reading comments from {TOML_FILE}...")
    with open(TOML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        # regex handles: "Location" = "Comment" with optional whitespace
        matches = re.findall(r'^\s*"(.*?)"\s*=\s*"(.*?)"', content, re.MULTILINE)
        for name, comment in matches:
            metadata[name] = comment
    return metadata

def process_map():
    manual_comments = load_manual_metadata()
    structured_data = {}
    
    print(f"🌍 Fetching live map data from Google...")
    # Added a slightly more robust User-Agent to avoid 403/404 blocks
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    req = urllib.request.Request(MAP_URL, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            root = ET.fromstring(response.read())
    except Exception as e:
        print(f"❌ Error fetching KML: {e}")
        print(f"🔗 Attempted URL: {MAP_URL}")
        return

    # Process KML Folders (Layers)
    folders = root.findall(".//{*}Folder")
    for f in folders:
        cat_node = f.find("{*}name")
        cat_name = cat_node.text if cat_node is not None else "Uncategorized"
        structured_data[cat_name] = []
        
        for pm in f.findall(".//{*}Placemark"):
            name_node = pm.find("{*}name")
            name = name_node.text if name_node is not None else "Unnamed"
            
            # 1. Coordinates
            coords = pm.find(".//{*}coordinates")
            lon, lat = "0", "0"
            if coords is not None and coords.text:
                parts = coords.text.strip().split(',')
                if len(parts) >= 2:
                    lon, lat = parts[0].strip(), parts[1].strip()

            # 2. Comment Merging
            desc_node = pm.find("{*}description")
            kml_desc = ""
            if desc_node is not None and desc_node.text:
                kml_desc = re.sub('<[^<]+?>', '', desc_node.text).strip()
            
            # Use TOML comment if it exists, otherwise KML description
            final_comment = manual_comments.get(name, kml_desc)

            structured_data[cat_name].append({
                "name": name,
                "comment": final_comment,
                "lat": lat,
                "lon": lon
            })

    # --- Write Hugo Markdown ---
    print(f"🚀 Generating {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        f.write("---\n")
        f.write(f'title: "Foodie Map"\nmap_id: "{MAP_ID}"\ncategories:\n')
        
        # Sort Categories Alphabetically
        for cat in sorted(structured_data.keys()):
            safe_id = "".join([c if c.isalnum() else "-" for c in cat.lower()]).strip("-")
            f.write(f"  - name: '{cat}'\n    id: '{safe_id}'\n    locations:\n")
            
            # --- ALPHABETISE LOCATIONS WITHIN CATEGORY ---
            sorted_locations = sorted(structured_data[cat], key=lambda x: x['name'].lower())
            
            for loc in sorted_locations:
                n = loc['name'].replace("'", "''")
                c = loc['comment'].replace("'", "''")
                
                f.write(f"      - name: '{n}'\n")
                f.write(f"        comment: '{c}'\n")
                f.write(f"        lat: '{loc['lat']}'\n")
                f.write(f"        lon: '{loc['lon']}'\n")
                f.write(f"        website: ''\n")
        
        f.write("---\n\n{{< foodie_map_interface >}}\n")
    print(f"✅ Success! Alphabetized locations & synced comments.")

if __name__ == "__main__":
    process_map()