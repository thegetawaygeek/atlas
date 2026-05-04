#!/usr/bin/env python3
"""
THE GETAWAY GEEK ATLAS — Palenque Supplemental Harvester
=========================================================
Searches Wikimedia Commons using four specific terms:
  - Temple of the Inscriptions
  - The Palace Palenque
  - Temple of the Cross Palenque
  - Temple of the Count Palenque

Downloads new images into the existing wikimedia subfolder for Palenque.
Starts numbering from wiki_021. Appends to existing credits.json.

USAGE:
  python3 palenque_supplemental_harvester.py
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

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

WIKI_DIR = r"C:\Users\jaysc\Downloads\ATLAS\Images\Palenque\wikimedia"
SITE_NAME = "Palenque"
SITE_FOLDER = "Palenque"

QUERIES = [
    "Temple of the Inscriptions Palenque",
    "The Palace Palenque Maya",
    "Temple of the Cross Palenque",
    "Temple of the Count Palenque",
]

MAX_PER_QUERY = 20
DOWNLOAD_DELAY = 3
QUERY_DELAY = 2


# ═══════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def make_request(url, max_retries=3):
    ctx = ssl.create_default_context()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'TheGetawayGeekAtlas/1.0 (archaeological site atlas; polite harvester)')
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
    ctx = ssl.create_default_context()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'TheGetawayGeekAtlas/1.0 (archaeological site atlas; polite harvester)')
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


def load_existing_credits(credits_path):
    if not os.path.exists(credits_path):
        return []
    with open(credits_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('images', [])


def save_credits(credits_path, all_images):
    data = {
        'site_name': SITE_NAME,
        'source': 'Wikimedia Commons',
        'harvested_date': time.strftime('%Y-%m-%d'),
        'total_images': len(all_images),
        'images': all_images,
    }
    with open(credits_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    summary_path = os.path.join(os.path.dirname(credits_path), 'credits_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("THE GETAWAY GEEK ATLAS — Wikimedia Image Credits\n")
        f.write(f"Site: {SITE_NAME}\n")
        f.write(f"Updated: {time.strftime('%Y-%m-%d')}\n")
        f.write(f"Total images: {len(all_images)}\n")
        f.write("=" * 60 + "\n\n")
        for img in all_images:
            f.write(f"File: {img.get('local_file', 'N/A')}\n")
            f.write(f"Photographer: {img['photographer']}\n")
            f.write(f"License: {img['license']}\n")
            if img.get('license_url'):
                f.write(f"License URL: {img['license_url']}\n")
            f.write(f"Page: {img['page_url']}\n")
            f.write(f"Original size: {img['width']}x{img['height']}\n")
            if img.get('attribution_required'):
                f.write(">>> ATTRIBUTION REQUIRED <<<\n")
            if img.get('description'):
                f.write(f"Description: {img['description']}\n")
            f.write("\n" + "-" * 40 + "\n\n")


def next_wiki_number(wiki_dir):
    existing = [f for f in os.listdir(wiki_dir) if re.match(r'wiki_\d+', f)]
    if not existing:
        return 1
    nums = [int(re.search(r'wiki_(\d+)', f).group(1)) for f in existing]
    return max(nums) + 1


def main():
    print("=" * 60)
    print("Palenque — Supplemental Wikimedia Harvester")
    print("Queries: Temple of the Inscriptions | The Palace")
    print("         Temple of the Cross | Temple of the Count")
    print("=" * 60)
    print()

    os.makedirs(WIKI_DIR, exist_ok=True)
    credits_path = os.path.join(WIKI_DIR, 'credits.json')

    existing_credits = load_existing_credits(credits_path)
    seen_urls = set(img['preview_url'] for img in existing_credits)
    print(f"Existing images in credits.json: {len(existing_credits)}")
    print()

    new_results = []
    for query in QUERIES:
        print(f"Searching: {query}")
        results = search_wikimedia(query, max_results=MAX_PER_QUERY)
        print(f"  Found {len(results)} results from Wikimedia")
        added = 0
        for r in results:
            if r['preview_url'] not in seen_urls:
                seen_urls.add(r['preview_url'])
                new_results.append(r)
                added += 1
        print(f"  {added} new (not already in collection)")
        time.sleep(QUERY_DELAY)

    print(f"\n{len(new_results)} new images to download")
    print()

    if not new_results:
        print("Nothing new to download. Done.")
        return

    start_num = next_wiki_number(WIKI_DIR)
    newly_downloaded = []

    for i, result in enumerate(new_results):
        num = start_num + i
        ext = '.png' if '.png' in result['preview_url'].lower() else '.jpg'
        filename = f"wiki_{num:03d}{ext}"
        filepath = os.path.join(WIKI_DIR, filename)

        print(f"  Downloading {filename} ({i+1}/{len(new_results)}) — {result['photographer'][:50]}")
        if download_image(result['preview_url'], filepath):
            result['local_file'] = os.path.join(SITE_FOLDER, 'wikimedia', filename)
            newly_downloaded.append(result)
        else:
            print(f"    FAILED — skipping")

        time.sleep(DOWNLOAD_DELAY)

    all_images = existing_credits + newly_downloaded
    save_credits(credits_path, all_images)

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)
    print(f"New images downloaded:  {len(newly_downloaded)}")
    print(f"Total in credits.json:  {len(all_images)}")
    print(f"Folder: {WIKI_DIR}")

    print("\nNew files:")
    for img in newly_downloaded:
        fname = os.path.basename(img['local_file'])
        print(f"  {fname}  —  {img['photographer'][:50]}  ({img['license']})")
        if img.get('description'):
            print(f"          {img['description'][:80]}")


if __name__ == "__main__":
    main()
