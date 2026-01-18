import os
import io
import zipfile
import urllib.request
import xml.etree.ElementTree as ET

# Configuration
# The 'mid' is the ID from your existing MAP_ID
MAP_URL = f"https://www.google.com/maps/d/kml?mid=1F2hS3T8QPhS3uK8dJCNxfgFnxC-DRmM&forcekml=1"
COMMENTS_FILE = "map/location_comments.toml"
OUTPUT_FILE = "website/content.en/foodie-map.md"
MAP_ID = "1F2hS3T8QPhS3uK8dJCNxfgFnxC-DRmM"

def load_comments():
    comments = {}
    current_cat = None
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if line.startswith('[') and line.endswith(']'):
                    current_cat = line[1:-1]
                    comments[current_cat] = {}
                elif '=' in line and current_cat is not None:
                    key, val = line.split('=', 1)
                    k = key.strip().strip('"')
                    v = val.strip().strip('"').replace('\\"', '"')
                    comments[current_cat][k] = v
    return comments

def save_comments(comments):
    print(f"💾 Updating {COMMENTS_FILE}...")
    # Ensure directory exists
    os.makedirs(os.path.dirname(COMMENTS_FILE), exist_ok=True)
    with open(COMMENTS_FILE, 'w', encoding='utf-8') as f:
        f.write("# Organized by Category (Google Map Layers)\n")
        for cat in sorted(comments.keys()):
            if not comments[cat]: continue
            f.write(f"\n[{cat}]\n")
            for name in sorted(comments[cat].keys()):
                safe_val = comments[cat][name].replace('"', '\\"')
                f.write(f'"{name}" = "{safe_val}"\n')

def fetch_and_extract_kml(url):
    """Downloads KMZ and extracts KML in memory."""
    print(f"🌍 Fetching latest map data from Google...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        kmz_data = response.read()
        
    # KMZ is a ZIP file. Try to unzip it.
    try:
        with zipfile.ZipFile(io.BytesIO(kmz_data)) as z:
            kml_name = [n for n in z.namelist() if n.endswith('.kml')][0]
            return z.read(kml_name)
    except zipfile.BadZipFile:
        # If Google returns raw KML instead of KMZ
        return kmz_data

def process_map():
    existing_comments = load_comments()
    structured_data = {}

    # 1. Get KML from Web
    try:
        kml_content = fetch_and_extract_kml(MAP_URL)
        root = ET.fromstring(kml_content)
    except Exception as e:
        print(f"❌ Failed to fetch map: {e}")
        return

    # Handle potential NetworkLinks inside the fetched KML
    network_href = root.find(".//{*}href")
    if network_href is not None and "google.com" in network_href.text:
        kml_content = fetch_and_extract_kml(network_href.text)
        root = ET.fromstring(kml_content)

    # 2. Extract Data
    folders = root.findall(".//{*}Folder")
    if not folders:
        placemarks = root.findall(".//{*}Placemark")
        folders_to_process = [("General", placemarks)]
    else:
        folders_to_process = [(f.find("{*}name").text or "General", f.findall(".//{*}Placemark")) for f in folders]

    for cat_name, placemarks in folders_to_process:
        if cat_name not in structured_data:
            structured_data[cat_name] = []
        
        for pm in placemarks:
            name_node = pm.find("{*}name")
            if name_node is None: continue
            name = name_node.text
            
            comment = ""
            for old_cat in existing_comments:
                if name in existing_comments[old_cat]:
                    comment = existing_comments[old_cat][name]
                    break
            
            structured_data[cat_name].append({"name": name, "comment": comment})
        structured_data[cat_name].sort(key=lambda x: x['name'])

    # 3. Save / Sync
    toml_export = {cat: {i['name']: i['comment'] for i in items} for cat, items in structured_data.items()}
    save_comments(toml_export)

    # 4. Write Hugo Markdown
    print(f"🚀 Generating {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        f.write("---\n")
        f.write(f'title: "Geonaut\'s North London Foodie Map"\n')
        f.write(f'map_id: "{MAP_ID}"\n')
        f.write("categories:\n")
        for cat in sorted(structured_data.keys()):
            if not structured_data[cat]: continue
            safe_id = "".join([c if c.isalnum() else "-" for c in cat.lower()]).strip("-")
            f.write(f"  - name: '{cat}'\n")
            f.write(f"    id: '{safe_id}'\n")
            f.write("    locations:\n")
            for loc in structured_data[cat]:
                # YAML safety
                s_name = loc['name'].replace("'", "''")
                s_comment = loc['comment'].replace("'", "''")
                f.write(f"      - name: '{s_name}'\n")
                f.write(f"        comment: '{s_comment}'\n")
        f.write("---\n\n")
        f.write("{{< foodie_map_interface >}}\n")

    print(f"✅ Sync complete!")

if __name__ == "__main__":
    process_map()