#!/usr/bin/env python3
"""
THE GETAWAY GEEK ATLAS — Wikimedia Harvester v1.0
==================================================
Wikimedia Commons ONLY. Slow and polite.
Targets the 27 V1 sites that are NOT prototype sites.
(Excludes: Saqsaywaman, Mohenjo-daro, Rosslyn Chapel)

Downloads preview-quality images into existing ATLAS/Images folders.
Logs full credit metadata.

IMPORTANT: This script runs SLOWLY on purpose.
It waits 3 seconds between each image download and 10 seconds
between sites to avoid triggering Wikimedia's rate limiter.
Expected runtime: approximately 45-60 minutes for all 27 sites.

USAGE:
  Run from your ATLAS folder:
    python3 wikimedia_harvester.py
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

# Fix Windows console Unicode encoding (handles characters like Ġ in Ġgantija)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Path to your ATLAS/Images folder
ATLAS_IMAGES_PATH = r"C:\Users\jaysc\Downloads\ATLAS\Images"

# Max images to pull per site
MAX_IMAGES_PER_SITE = 20

# Delay between individual image downloads (seconds)
DOWNLOAD_DELAY = 3

# Delay between sites (seconds)
SITE_DELAY = 10

# Delay between search queries for the same site (seconds)
QUERY_DELAY = 2

# ═══════════════════════════════════════════════════════════════
# 27 SITES (excluding Saqsaywaman, Mohenjo-daro, Rosslyn Chapel)
# ═══════════════════════════════════════════════════════════════

SITES = [
    {
        "name": "Angkor Wat",
        "folder": "Angkor Wat",
        "queries": ["Angkor Wat temple", "Angkor Wat Cambodia", "Angkor Thom ruins"]
    },
    {
        "name": "Borobudur",
        "folder": "Borobudur",
        "queries": ["Borobudur temple", "Borobudur Java", "Borobudur stupa"]
    },
    {
        "name": "Chavín de Huántar",
        "folder": "Chavin de Huantar",
        "queries": ["Chavín de Huántar", "Chavin de Huantar ruins", "Lanzon Chavin"]
    },
    {
        "name": "Chichén Itzá",
        "folder": "Chichen Itza",
        "queries": ["Chichén Itzá", "El Castillo Chichen Itza", "Kukulkan pyramid Chichen"]
    },
    {
        "name": "Dendera",
        "folder": "Dendera",
        "queries": ["Dendera temple", "Hathor temple Dendera", "Dendera ceiling zodiac"]
    },
    {
        "name": "Derinkuyu",
        "folder": "Derinkuya",
        "queries": ["Derinkuyu underground city", "Derinkuyu Cappadocia"]
    },
    {
        "name": "Ellora / Kailasa Temple",
        "folder": "Ellora - Kailasa Temple",
        "queries": ["Kailasa temple Ellora", "Ellora caves", "Kailash temple monolithic"]
    },
    {
        "name": "Ġgantija",
        "folder": "Ggantija",
        "queries": ["Ġgantija temples", "Ggantija Malta", "Ggantija Gozo megalithic"]
    },
    {
        "name": "Göbekli Tepe",
        "folder": "Gobekli Tepe",
        "queries": ["Göbekli Tepe", "Gobekli Tepe pillars", "Göbekli Tepe excavation"]
    },
    {
        "name": "Goseck Circle",
        "folder": "Goseck Circle",
        "queries": ["Goseck Circle", "Goseck solar observatory", "Sonnenobservatorium Goseck"]
    },
    {
        "name": "Great Pyramid of Giza",
        "folder": "Great Pyramid of Giza",
        "queries": ["Great Pyramid Giza", "Pyramid of Khufu", "Giza pyramids complex"]
    },
    {
        "name": "Great Zimbabwe",
        "folder": "Great Zimbabwe",
        "queries": ["Great Zimbabwe ruins", "Great Zimbabwe walls", "Great Zimbabwe enclosure tower"]
    },
    {
        "name": "Ħal Saflieni Hypogeum",
        "folder": "Hal Saflieni Hypogeum",
        "queries": ["Hal Saflieni Hypogeum", "Hypogeum Malta", "Hypogeum underground temple"]
    },
    {
        "name": "Hampi",
        "folder": "Hampi",
        "queries": ["Hampi ruins", "Hampi Vijayanagara", "Hampi temple Karnataka"]
    },
    {
        "name": "Karahan Tepe",
        "folder": "Karahan Tepe",
        "queries": ["Karahan Tepe", "Karahan Tepe pillars", "Karahan Tepe excavation"]
    },
    {
        "name": "Karnak",
        "folder": "Karnak",
        "queries": ["Karnak temple", "Hypostyle Hall Karnak", "Karnak Luxor temple"]
    },
    {
        "name": "Longyou Caves",
        "folder": "Longyou Caves",
        "queries": ["Longyou Caves", "Longyou Grottoes", "Longyou caverns China"]
    },
    {
        "name": "Machu Picchu",
        "folder": "Machu Picchu",
        "queries": ["Machu Picchu", "Machu Picchu ruins", "Machu Picchu Inca citadel"]
    },
    {
        "name": "Nazca Lines",
        "folder": "Nazca Lines",
        "queries": ["Nazca Lines", "Nazca geoglyphs aerial", "Nazca Lines Peru"]
    },
    {
        "name": "Newgrange",
        "folder": "Newgrange",
        "queries": ["Newgrange", "Newgrange passage tomb", "Newgrange Ireland megalithic"]
    },
    {
        "name": "Palenque",
        "folder": "Palenque",
        "queries": ["Palenque ruins", "Palenque Maya", "Temple of Inscriptions Palenque"]
    },
    {
        "name": "Petra",
        "folder": "Petra",
        "queries": ["Petra Jordan", "Al-Khazneh Treasury Petra", "Petra ancient city Nabataean"]
    },
    {
        "name": "Poverty Point",
        "folder": "Poverty Point",
        "queries": ["Poverty Point Louisiana", "Poverty Point mounds", "Poverty Point earthworks"]
    },
    {
        "name": "Skara Brae",
        "folder": "Skara Brae",
        "queries": ["Skara Brae", "Skara Brae Orkney", "Skara Brae Neolithic"]
    },
    {
        "name": "Stonehenge",
        "folder": "Stonehenge",
        "queries": ["Stonehenge", "Stonehenge monument", "Stonehenge Wiltshire stones"]
    },
    {
        "name": "Teotihuacan",
        "folder": "Teotihuacan",
        "queries": ["Teotihuacan", "Pyramid of the Sun Teotihuacan", "Avenue of the Dead Teotihuacan"]
    },
    {
        "name": "Tiwanaku & Puma Punku",
        "folder": "Tiwanaku & Puma Punku",
        "queries": ["Tiwanaku ruins", "Puma Punku", "Tiahuanaco Bolivia", "Puma Punku H blocks"]
    },
]


# ═══════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def make_request(url, max_retries=3):
    """Make an HTTP request with retry logic."""
    ctx = ssl.create_default_context()

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'TheGetawayGeekAtlas/1.0 (archaeological site atlas; polite single-user harvester; contact: getawaygeek)')

            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (attempt + 1)
                print(f"    Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    HTTP Error {e.code}: {e.reason}")
                return None
        except Exception as e:
            print(f"    Request error: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
    return None


def download_image(url, filepath, max_retries=3):
    """Download an image to a local file."""
    ctx = ssl.create_default_context()

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'TheGetawayGeekAtlas/1.0 (archaeological site atlas; polite single-user harvester)')

            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                with open(filepath, 'wb') as f:
                    f.write(response.read())
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (attempt + 1)
                print(f"    Rate limited on download. Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    Download HTTP Error {e.code}")
                return False
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                print(f"    Download failed: {e}")
    return False


def search_wikimedia(query, max_results=20):
    """Search Wikimedia Commons for images."""
    results = []

    params = {
        'action': 'query',
        'generator': 'search',
        'gsrnamespace': '6',
        'gsrsearch': f'{query} filetype:bitmap',
        'gsrlimit': str(min(max_results, 50)),
        'prop': 'imageinfo',
        'iiprop': 'url|extmetadata|size|mime',
        'iiurlwidth': '1280',
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

        mime = info.get('mime', '')
        if mime not in ['image/jpeg', 'image/png', 'image/webp']:
            continue

        width = info.get('width', 0)
        height = info.get('height', 0)
        if width < 800 or height < 600:
            continue

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

    return results


def harvest_site(site, base_path):
    """Harvest Wikimedia images for a single site."""
    site_dir = os.path.join(base_path, site['folder'])
    wiki_dir = os.path.join(site_dir, 'wikimedia')
    os.makedirs(wiki_dir, exist_ok=True)

    # Collect results across all queries, deduplicated
    seen_urls = set()
    all_results = []

    for query in site['queries']:
        print(f"    Searching: {query}")
        results = search_wikimedia(query, max_results=MAX_IMAGES_PER_SITE)
        print(f"    Found {len(results)} results")

        for r in results:
            if r['preview_url'] not in seen_urls:
                seen_urls.add(r['preview_url'])
                all_results.append(r)

        time.sleep(QUERY_DELAY)

    # Cap total
    all_results = all_results[:MAX_IMAGES_PER_SITE]
    print(f"    {len(all_results)} unique images to download")

    # Download
    all_credits = []
    downloaded = 0

    for i, result in enumerate(all_results):
        ext = '.jpg'
        if '.png' in result['preview_url'].lower():
            ext = '.png'

        filename = f"wiki_{i+1:03d}{ext}"
        filepath = os.path.join(wiki_dir, filename)

        print(f"    Downloading {filename} ({i+1}/{len(all_results)})...")
        if download_image(result['preview_url'], filepath):
            result['local_file'] = os.path.join(site['folder'], 'wikimedia', filename)
            all_credits.append(result)
            downloaded += 1

        # SLOW — this is intentional
        time.sleep(DOWNLOAD_DELAY)

    # Save credits
    credits_path = os.path.join(wiki_dir, 'credits.json')
    with open(credits_path, 'w', encoding='utf-8') as f:
        json.dump({
            'site_name': site['name'],
            'source': 'Wikimedia Commons',
            'harvested_date': time.strftime('%Y-%m-%d'),
            'total_images': downloaded,
            'images': all_credits
        }, f, indent=2, ensure_ascii=False)

    # Human-readable credits
    summary_path = os.path.join(wiki_dir, 'credits_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"THE GETAWAY GEEK ATLAS — Wikimedia Image Credits\n")
        f.write(f"Site: {site['name']}\n")
        f.write(f"Harvested: {time.strftime('%Y-%m-%d')}\n")
        f.write(f"Total images: {downloaded}\n")
        f.write(f"{'='*60}\n\n")

        for img in all_credits:
            f.write(f"File: {img.get('local_file', 'N/A')}\n")
            f.write(f"Photographer: {img['photographer']}\n")
            f.write(f"License: {img['license']}\n")
            if img.get('license_url'):
                f.write(f"License URL: {img['license_url']}\n")
            f.write(f"Page: {img['page_url']}\n")
            f.write(f"Original size: {img['width']}x{img['height']}\n")
            if img.get('attribution_required'):
                f.write(f">>> ATTRIBUTION REQUIRED <<<\n")
            if img.get('description'):
                f.write(f"Description: {img['description']}\n")
            f.write(f"\n{'-'*40}\n\n")

    return downloaded


def main():
    print("=" * 60)
    print("THE GETAWAY GEEK ATLAS — Wikimedia Harvester")
    print("Wikimedia Commons only | 27 sites | Slow and polite")
    print("=" * 60)
    print()

    base_path = os.path.abspath(ATLAS_IMAGES_PATH)
    print(f"Target folder: {base_path}")

    if not os.path.exists(base_path):
        print(f"\nERROR: Folder not found: {base_path}")
        print(f"Update ATLAS_IMAGES_PATH in this script.")
        sys.exit(1)

    print(f"Sites to harvest: {len(SITES)}")
    print(f"Max images per site: {MAX_IMAGES_PER_SITE}")
    print(f"Download delay: {DOWNLOAD_DELAY}s between images")
    print(f"Site delay: {SITE_DELAY}s between sites")
    print(f"Estimated runtime: 45-60 minutes")
    print()

    total_all = 0
    results_summary = []

    for i, site in enumerate(SITES):
        print(f"\n[{i+1}/{len(SITES)}] {site['name']}")
        print("-" * 40)

        # Skip sites that already have a full harvest (15+ images in wikimedia folder)
        wiki_dir = os.path.join(base_path, site['folder'], 'wikimedia')
        if os.path.isdir(wiki_dir):
            existing = [f for f in os.listdir(wiki_dir) if f.lower().endswith(('.jpg','.jpeg','.png','.gif','.webp'))]
            if len(existing) >= 15:
                print(f"    Skipping — {len(existing)} images already downloaded")
                results_summary.append((site['name'], len(existing)))
                total_all += len(existing)
                continue

        count = harvest_site(site, base_path)
        total_all += count
        results_summary.append((site['name'], count))

        print(f"    Done — {count} images")

        if i < len(SITES) - 1:
            print(f"    Waiting {SITE_DELAY}s before next site...")
            time.sleep(SITE_DELAY)

    # Summary
    print("\n" + "=" * 60)
    print("HARVEST COMPLETE")
    print("=" * 60)
    print(f"\nTotal images: {total_all}")
    print(f"\nPer-site breakdown:")
    for name, count in results_summary:
        bar = "█" * min(count, 50)
        print(f"  {name:35s} {count:4d}  {bar}")

    print(f"\nNext steps:")
    print(f"  1. Browse each site's wikimedia folder")
    print(f"  2. Delete images you don't want")
    print(f"  3. Credits logged in each wikimedia/credits_summary.txt")


if __name__ == "__main__":
    main()
