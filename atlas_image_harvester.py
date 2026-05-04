#!/usr/bin/env python3
"""
THE GETAWAY GEEK ATLAS — Image Harvester v1.1
==============================================
Searches Wikimedia Commons, Pixabay, and Pexels for candidate images
across all 30 V1 Atlas sites.

Downloads preview-quality images for curation into your existing
ATLAS/Images folder structure, with source subfolders (wikimedia,
pixabay, pexels) created inside each site folder.

Logs full credit metadata for each image.

USAGE:
  1. Set your API keys in the config section below
  2. Set ATLAS_IMAGES_PATH to your ATLAS/Images folder location
  3. Run: python3 atlas_image_harvester.py
  4. Browse site folders, delete images you don't want
  5. Run selected images through Nano Banana for TGG treatment
  6. Credits are logged in credits.json and credits_summary.txt

OUTPUT STRUCTURE (inside your existing folders):
  ATLAS/Images/
    Stonehenge/
      wikimedia/
        img_001.jpg
        img_002.jpg
      pixabay/
        img_001.jpg
      pexels/
        img_001.jpg
      credits.json
      credits_summary.txt
    Machu Picchu/
      ...
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl

# Fix Windows console encoding for Unicode site names (e.g. Ġgantija)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION — SET THESE BEFORE RUNNING
# ═══════════════════════════════════════════════════════════════

PIXABAY_API_KEY = "9744315-6bace6262de71070846bb44dd"
PEXELS_API_KEY = "mfgf1RSEtckp9AxWrwHgsaxHFmWzLkT2vO2U7ZveNxbtf4rkhu0r1EYm"

# Path to your ATLAS/Images folder
# Update this to match your system — example:
# ATLAS_IMAGES_PATH = r"C:\Users\YourName\Downloads\ATLAS\Images"
ATLAS_IMAGES_PATH = r"C:\Users\jaysc\Downloads\ATLAS\Images"

# Max images to pull per source per site (for curation)
MAX_IMAGES_PER_SOURCE = 15

# ═══════════════════════════════════════════════════════════════
# THE FIRST 30 — V1 ATLAS SITES
# Folder names match your existing ATLAS/Images subfolders exactly
# ═══════════════════════════════════════════════════════════════

SITES = [
    {
        "name": "Angkor Wat",
        "folder": "Angkor Wat",
        "queries": ["Angkor Wat", "Angkor Wat temple Cambodia", "Angkor Thom"]
    },
    {
        "name": "Borobudur",
        "folder": "Borobudur",
        "queries": ["Borobudur", "Borobudur temple Java Indonesia"]
    },
    {
        "name": "Chavín de Huántar",
        "folder": "Chavin de Huantar",
        "queries": ["Chavin de Huantar Peru", "Chavin temple", "Lanzon Chavin"]
    },
    {
        "name": "Chichén Itzá",
        "folder": "Chichen Itza",
        "queries": ["Chichen Itza", "El Castillo Chichen Itza", "Kukulkan pyramid"]
    },
    {
        "name": "Dendera",
        "folder": "Dendera",
        "queries": ["Dendera temple Egypt", "Hathor temple Dendera", "Dendera zodiac"]
    },
    {
        "name": "Derinkuyu",
        "folder": "Derinkuya",
        "queries": ["Derinkuyu underground city", "Derinkuyu Cappadocia"]
    },
    {
        "name": "Ellora / Kailasa Temple",
        "folder": "Ellora - Kailasa Temple",
        "queries": ["Kailasa temple Ellora", "Ellora caves India", "Kailash temple monolithic"]
    },
    {
        "name": "Ġgantija",
        "folder": "Ggantija",
        "queries": ["Ggantija temples Malta", "Ggantija megalithic", "Ggantija Gozo"]
    },
    {
        "name": "Göbekli Tepe",
        "folder": "Gobekli Tepe",
        "queries": ["Göbekli Tepe", "Gobekli Tepe pillars", "Gobekli Tepe archaeological site"]
    },
    {
        "name": "Goseck Circle",
        "folder": "Goseck Circle",
        "queries": ["Goseck Circle Germany", "Goseck solar observatory"]
    },
    {
        "name": "Great Pyramid of Giza",
        "folder": "Great Pyramid of Giza",
        "queries": ["Great Pyramid of Giza", "Pyramid of Khufu", "Giza pyramids"]
    },
    {
        "name": "Great Zimbabwe",
        "folder": "Great Zimbabwe",
        "queries": ["Great Zimbabwe ruins", "Great Zimbabwe walls", "Great Zimbabwe enclosure"]
    },
    {
        "name": "Ħal Saflieni Hypogeum",
        "folder": "Hal Saflieni Hypogeum",
        "queries": ["Hal Saflieni Hypogeum Malta", "Hypogeum Malta underground"]
    },
    {
        "name": "Hampi",
        "folder": "Hampi",
        "queries": ["Hampi ruins India", "Hampi Vijayanagara", "Hampi temple Karnataka"]
    },
    {
        "name": "Karahan Tepe",
        "folder": "Karahan Tepe",
        "queries": ["Karahan Tepe", "Karahan Tepe pillars Turkey"]
    },
    {
        "name": "Karnak",
        "folder": "Karnak",
        "queries": ["Karnak temple Egypt", "Karnak Luxor", "Hypostyle Hall Karnak"]
    },
    {
        "name": "Longyou Caves",
        "folder": "Longyou Caves",
        "queries": ["Longyou Caves China", "Longyou Grottoes"]
    },
    {
        "name": "Machu Picchu",
        "folder": "Machu Picchu",
        "queries": ["Machu Picchu", "Machu Picchu ruins Peru"]
    },
    {
        "name": "Mohenjo-daro",
        "folder": "Mohenjo-daro",
        "queries": ["Mohenjo-daro", "Mohenjo-daro ruins Pakistan", "Mohenjo-daro archaeological"]
    },
    {
        "name": "Nazca Lines",
        "folder": "Nazca Lines",
        "queries": ["Nazca Lines", "Nazca Lines aerial Peru", "Nazca geoglyphs"]
    },
    {
        "name": "Newgrange",
        "folder": "Newgrange",
        "queries": ["Newgrange Ireland", "Newgrange passage tomb"]
    },
    {
        "name": "Palenque",
        "folder": "Palenque",
        "queries": ["Palenque ruins Mexico", "Palenque Maya temple", "Temple of Inscriptions Palenque"]
    },
    {
        "name": "Petra",
        "folder": "Petra",
        "queries": ["Petra Jordan", "Petra Treasury Al-Khazneh", "Petra ancient city"]
    },
    {
        "name": "Poverty Point",
        "folder": "Poverty Point",
        "queries": ["Poverty Point Louisiana", "Poverty Point mounds", "Poverty Point archaeological"]
    },
    {
        "name": "Rosslyn Chapel",
        "folder": "Rosslyn Chapel",
        "queries": ["Rosslyn Chapel Scotland", "Rosslyn Chapel interior"]
    },
    {
        "name": "Saqsaywaman",
        "folder": "Saqsaywaman",
        "queries": ["Sacsayhuaman", "Saqsaywaman Cusco", "Sacsayhuaman walls Peru"]
    },
    {
        "name": "Skara Brae",
        "folder": "Skara Brae",
        "queries": ["Skara Brae", "Skara Brae Orkney", "Skara Brae Neolithic village"]
    },
    {
        "name": "Stonehenge",
        "folder": "Stonehenge",
        "queries": ["Stonehenge", "Stonehenge monument Wiltshire"]
    },
    {
        "name": "Teotihuacan",
        "folder": "Teotihuacan",
        "queries": ["Teotihuacan", "Pyramid of the Sun Teotihuacan", "Avenue of the Dead Teotihuacan"]
    },
    {
        "name": "Tiwanaku & Puma Punku",
        "folder": "Tiwanaku & Puma Punku",
        "queries": ["Tiwanaku ruins Bolivia", "Puma Punku", "Tiahuanaco", "Puma Punku H blocks"]
    },
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def make_request(url, headers=None, max_retries=3):
    """Make an HTTP request with retry logic and rate limiting."""
    ctx = ssl.create_default_context()

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            if headers:
                for key, value in headers.items():
                    req.add_header(key, value)
            req.add_header('User-Agent', 'TheGetawayGeekAtlas/1.0 (image harvester for archaeological site atlas)')

            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limited
                wait = 2 ** (attempt + 1)
                print(f"    Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    HTTP Error {e.code}: {e.reason}")
                return None
        except Exception as e:
            print(f"    Request error: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
    return None


def download_image(url, filepath, headers=None, max_retries=2):
    """Download an image to a local file."""
    ctx = ssl.create_default_context()

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'TheGetawayGeekAtlas/1.0')
            if headers:
                for key, value in headers.items():
                    req.add_header(key, value)

            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                with open(filepath, 'wb') as f:
                    f.write(response.read())
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print(f"    Download failed: {e}")
    return False


# ═══════════════════════════════════════════════════════════════
# WIKIMEDIA COMMONS SEARCH
# ═══════════════════════════════════════════════════════════════

def search_wikimedia(query, max_results=MAX_IMAGES_PER_SOURCE):
    """Search Wikimedia Commons for images and return metadata."""
    results = []

    params = {
        'action': 'query',
        'generator': 'search',
        'gsrnamespace': '6',  # File namespace
        'gsrsearch': f'{query} filetype:bitmap',
        'gsrlimit': str(min(max_results, 50)),
        'prop': 'imageinfo',
        'iiprop': 'url|extmetadata|size|mime',
        'iiurlwidth': '1280',  # Reasonably sized preview
        'format': 'json',
    }

    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    data = make_request(url)

    if not data or 'query' not in data or 'pages' not in data['query']:
        return results

    for page_id, page in data['query']['pages'].items():
        if 'imageinfo' not in page:
            continue

        info = page['imageinfo'][0]
        meta = info.get('extmetadata', {})

        # Skip non-photo formats
        mime = info.get('mime', '')
        if mime not in ['image/jpeg', 'image/png', 'image/webp']:
            continue

        # Skip tiny images
        width = info.get('width', 0)
        height = info.get('height', 0)
        if width < 800 or height < 600:
            continue

        # Extract credit information
        artist = meta.get('Artist', {}).get('value', 'Unknown')
        artist = re.sub(r'<[^>]+>', '', artist).strip()

        license_name = meta.get('LicenseShortName', {}).get('value', 'Unknown')
        license_url = meta.get('LicenseUrl', {}).get('value', '')
        description = meta.get('ImageDescription', {}).get('value', '')
        description = re.sub(r'<[^>]+>', '', description).strip()

        thumb_url = info.get('thumburl', info.get('url', ''))
        original_url = info.get('url', '')
        page_url = f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(page.get('title', '').replace('File:', ''))}"

        results.append({
            'source': 'Wikimedia Commons',
            'preview_url': thumb_url,
            'original_url': original_url,
            'page_url': page_url,
            'width': width,
            'height': height,
            'photographer': artist,
            'license': license_name,
            'license_url': license_url,
            'description': description[:200] if description else '',
            'attribution_required': license_name not in ['CC0', 'Public domain'],
        })

    return results[:max_results]


# ═══════════════════════════════════════════════════════════════
# PIXABAY SEARCH
# ═══════════════════════════════════════════════════════════════

def search_pixabay(query, max_results=MAX_IMAGES_PER_SOURCE):
    """Search Pixabay for images and return metadata."""
    results = []

    if PIXABAY_API_KEY == "YOUR_PIXABAY_API_KEY_HERE":
        return results

    params = {
        'key': PIXABAY_API_KEY,
        'q': query,
        'image_type': 'photo',
        'per_page': str(min(max_results, 200)),
        'safesearch': 'true',
        'min_width': 800,
        'min_height': 600,
    }

    url = 'https://pixabay.com/api/?' + urllib.parse.urlencode(params)
    data = make_request(url)

    if not data or 'hits' not in data:
        return results

    for hit in data['hits']:
        results.append({
            'source': 'Pixabay',
            'preview_url': hit.get('webformatURL', ''),
            'original_url': hit.get('largeImageURL', ''),
            'page_url': hit.get('pageURL', ''),
            'width': hit.get('imageWidth', 0),
            'height': hit.get('imageHeight', 0),
            'photographer': hit.get('user', 'Unknown'),
            'license': 'Pixabay Content License',
            'license_url': 'https://pixabay.com/service/license-summary/',
            'description': hit.get('tags', ''),
            'attribution_required': False,
        })

    return results[:max_results]


# ═══════════════════════════════════════════════════════════════
# PEXELS SEARCH
# ═══════════════════════════════════════════════════════════════

def search_pexels(query, max_results=MAX_IMAGES_PER_SOURCE):
    """Search Pexels for images and return metadata."""
    results = []

    if PEXELS_API_KEY == "YOUR_PEXELS_API_KEY_HERE":
        return results

    params = {
        'query': query,
        'per_page': str(min(max_results, 80)),
    }

    url = 'https://api.pexels.com/v1/search?' + urllib.parse.urlencode(params)
    headers = {'Authorization': PEXELS_API_KEY}
    data = make_request(url, headers=headers)

    if not data or 'photos' not in data:
        return results

    for photo in data['photos']:
        src = photo.get('src', {})
        results.append({
            'source': 'Pexels',
            'preview_url': src.get('large', ''),
            'original_url': src.get('original', ''),
            'page_url': photo.get('url', ''),
            'width': photo.get('width', 0),
            'height': photo.get('height', 0),
            'photographer': photo.get('photographer', 'Unknown'),
            'license': 'Pexels License',
            'license_url': 'https://www.pexels.com/license/',
            'description': photo.get('alt', ''),
            'attribution_required': False,
            'attribution_recommended': True,
        })

    return results[:max_results]


# ═══════════════════════════════════════════════════════════════
# MAIN HARVESTER
# ═══════════════════════════════════════════════════════════════

def harvest_site(site, base_path):
    """Harvest images for a single site across all sources."""
    site_dir = os.path.join(base_path, site['folder'])

    if not os.path.exists(site_dir):
        print(f"    WARNING: Folder not found: {site_dir}")
        print(f"    Creating it...")
        os.makedirs(site_dir, exist_ok=True)

    all_credits = []
    total_downloaded = 0

    for source_name, search_fn, subdir in [
        ('Wikimedia', search_wikimedia, 'wikimedia'),
        ('Pixabay', search_pixabay, 'pixabay'),
        ('Pexels', search_pexels, 'pexels'),
    ]:
        source_dir = os.path.join(site_dir, subdir)
        os.makedirs(source_dir, exist_ok=True)

        # Collect results across all search queries for this site
        seen_urls = set()
        all_results = []

        for query in site['queries']:
            print(f"    [{source_name}] Searching: {query}")
            results = search_fn(query)

            for r in results:
                if r['preview_url'] not in seen_urls:
                    seen_urls.add(r['preview_url'])
                    all_results.append(r)

            # Be polite — don't hammer APIs
            time.sleep(0.5)

        # Cap total results per source
        all_results = all_results[:MAX_IMAGES_PER_SOURCE]

        # Download preview images
        for i, result in enumerate(all_results):
            ext = '.jpg'
            if '.png' in result['preview_url'].lower():
                ext = '.png'

            filename = f"img_{i+1:03d}{ext}"
            filepath = os.path.join(source_dir, filename)

            headers = {}
            if source_name == 'Pexels':
                headers = {'Authorization': PEXELS_API_KEY}

            print(f"    [{source_name}] Downloading {filename}...")
            if download_image(result['preview_url'], filepath, headers=headers):
                result['local_file'] = os.path.join(site['folder'], subdir, filename)
                all_credits.append(result)
                total_downloaded += 1

            time.sleep(0.3)  # Rate limiting courtesy

    # Save credits file (JSON for programmatic use)
    credits_path = os.path.join(site_dir, 'credits.json')
    with open(credits_path, 'w', encoding='utf-8') as f:
        json.dump({
            'site_name': site['name'],
            'harvested_date': time.strftime('%Y-%m-%d'),
            'total_images': total_downloaded,
            'images': all_credits
        }, f, indent=2, ensure_ascii=False)

    # Save human-readable credits summary
    summary_path = os.path.join(site_dir, 'credits_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"THE GETAWAY GEEK ATLAS — Image Credits\n")
        f.write(f"Site: {site['name']}\n")
        f.write(f"Harvested: {time.strftime('%Y-%m-%d')}\n")
        f.write(f"Total images: {total_downloaded}\n")
        f.write(f"{'='*60}\n\n")

        for img in all_credits:
            f.write(f"File: {img.get('local_file', 'N/A')}\n")
            f.write(f"Source: {img['source']}\n")
            f.write(f"Photographer: {img['photographer']}\n")
            f.write(f"License: {img['license']}\n")
            if img.get('license_url'):
                f.write(f"License URL: {img['license_url']}\n")
            f.write(f"Page: {img['page_url']}\n")
            f.write(f"Original size: {img['width']}x{img['height']}\n")
            if img.get('attribution_required'):
                f.write(f">>> ATTRIBUTION REQUIRED <<<\n")
            elif img.get('attribution_recommended'):
                f.write(f"Attribution recommended (not required)\n")
            if img.get('description'):
                f.write(f"Description: {img['description']}\n")
            f.write(f"\n{'-'*40}\n\n")

    return total_downloaded


def main():
    """Run the full harvest across all 30 sites."""
    print("=" * 60)
    print("THE GETAWAY GEEK ATLAS — Image Harvester v1.1")
    print("=" * 60)
    print()

    # Resolve the images path
    base_path = os.path.abspath(ATLAS_IMAGES_PATH)
    print(f"Target folder: {base_path}")
    print()

    if not os.path.exists(base_path):
        print(f"ERROR: ATLAS Images folder not found at: {base_path}")
        print(f"Please update ATLAS_IMAGES_PATH in this script to match your setup.")
        print(f"Example: r\"C:\\Users\\YourName\\Downloads\\ATLAS\\Images\"")
        sys.exit(1)

    # Check API keys
    if PIXABAY_API_KEY == "YOUR_PIXABAY_API_KEY_HERE":
        print("WARNING: Pixabay API key not set — Pixabay will be skipped")
    if PEXELS_API_KEY == "YOUR_PEXELS_API_KEY_HERE":
        print("WARNING: Pexels API key not set — Pexels will be skipped")
    print()

    # Verify site folders exist
    missing = []
    for site in SITES:
        folder_path = os.path.join(base_path, site['folder'])
        if not os.path.exists(folder_path):
            missing.append(site['folder'])

    if missing:
        print(f"Note: {len(missing)} site folder(s) not found and will be created:")
        for m in missing:
            print(f"  - {m}")
        print()

    total_all = 0
    results_summary = []

    for i, site in enumerate(SITES):
        print(f"\n[{i+1}/30] {site['name']}")
        print("-" * 40)

        # Skip sites that already have a credits.json (already harvested)
        credits_file = os.path.join(base_path, site['folder'], 'credits.json')
        if os.path.exists(credits_file):
            with open(credits_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            prev_count = existing.get('total_images', 0)
            print(f"    Already harvested ({prev_count} images) — skipping")
            total_all += prev_count
            results_summary.append((site['name'], prev_count))
            continue

        count = harvest_site(site, base_path)
        total_all += count
        results_summary.append((site['name'], count))

        print(f"    Done — {count} images downloaded")

        # Pause between sites
        if i < len(SITES) - 1:
            time.sleep(1)

    # Final summary
    print("\n" + "=" * 60)
    print("HARVEST COMPLETE")
    print("=" * 60)
    print(f"\nTotal images: {total_all}")
    print(f"Output directory: {base_path}\n")

    print("Per-site breakdown:")
    for name, count in results_summary:
        bar = "█" * min(count, 50)
        print(f"  {name:35s} {count:4d}  {bar}")

    print(f"\n{'='*60}")
    print(f"NEXT STEPS")
    print(f"{'='*60}")
    print(f"  1. Browse each site folder and delete images you don't want")
    print(f"  2. Run selected images through Nano Banana (Atlas house look)")
    print(f"  3. Credits are logged in credits.json and credits_summary.txt")
    print(f"  4. Deploy treated images + credits to your Atlas project")
    print()


if __name__ == "__main__":
    main()
