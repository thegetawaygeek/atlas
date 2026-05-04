#!/usr/bin/env python3
"""
ATLAS sites.js Patcher
=======================
Reads wiring_results.json produced by wire_all_sites.py and updates
src/data/sites.js — replacing heroImage, galleryImages[], and
adding/updating photoCredits for each of the 26 sites.

Run from the ATLAS root folder after wire_all_sites.py succeeds.
"""

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ATLAS_ROOT    = r"C:\Users\jaysc\Downloads\ATLAS"
SITES_JS_PATH = os.path.join(ATLAS_ROOT, "src", "data", "sites.js")
RESULTS_PATH  = os.path.join(ATLAS_ROOT, "wiring_results.json")


def build_image_block(hero_url, gallery_urls, photo_credits):
    """
    Build the JS text block:
        heroImage: "...",
        galleryImages: [
          "...",
          ...
        ],
        photoCredits: "...",   ← only if credits exist
    """
    lines = []
    lines.append(f'    heroImage: "{hero_url}",')
    lines.append('    galleryImages: [')
    for url in gallery_urls:
        lines.append(f'      "{url}",')
    lines.append('    ],')
    if photo_credits:
        # Escape any double-quotes inside the credits string (shouldn't happen but safe)
        safe_credits = photo_credits.replace('"', '\\"')
        lines.append(f'    photoCredits: "{safe_credits}",')
    return '\n'.join(lines)


def patch_site_entry(js_text, site_id, hero_url, gallery_urls, photo_credits):
    """
    Find the entry for site_id in js_text and replace the heroImage /
    galleryImages / (optional) photoCredits block.

    The pattern matches from heroImage: through the closing ], and
    an optional existing photoCredits line.
    """
    new_block = build_image_block(hero_url, gallery_urls, photo_credits)

    # Pattern: matches heroImage through galleryImages closing ],
    # and optionally an existing photoCredits line
    pattern = (
        r'(    heroImage:\s*"[^"]*",\s*\n'
        r'    galleryImages:\s*\[\s*\n'
        r'(?:      "[^"]*",\s*\n)*'
        r'    \],)'
        r'(\s*\n    photoCredits:\s*"[^"]*",)?'
    )

    # We need to find this pattern only within the right site entry.
    # Strategy: locate the site entry first, then do the replacement inside it.

    # Find the site block boundaries by looking for id: "site_id"
    site_pattern = re.compile(
        r'(  \{[^{]*?id:\s*"' + re.escape(site_id) + r'".*?  \},)',
        re.DOTALL
    )

    match = site_pattern.search(js_text)
    if not match:
        print(f"  ERROR: Could not find site entry for '{site_id}'")
        return js_text

    site_block = match.group(1)
    original_start = match.start()
    original_end   = match.end()

    # Now replace within this block
    img_pattern = re.compile(pattern, re.DOTALL)
    new_site_block, count = img_pattern.subn(new_block, site_block)

    if count == 0:
        print(f"  WARNING: Image pattern not found in entry for '{site_id}'")
        return js_text

    return js_text[:original_start] + new_site_block + js_text[original_end:]


def main():
    print("=" * 65)
    print("ATLAS sites.js Patcher")
    print("=" * 65)
    print()

    if not os.path.exists(RESULTS_PATH):
        print(f"ERROR: wiring_results.json not found at {RESULTS_PATH}")
        print("Run wire_all_sites.py first.")
        sys.exit(1)

    with open(RESULTS_PATH, 'r', encoding='utf-8') as f:
        results = json.load(f)

    with open(SITES_JS_PATH, 'r', encoding='utf-8') as f:
        js_text = f.read()

    print(f"Loaded {len(results)} site results")
    print(f"sites.js: {len(js_text)} characters\n")

    patched = js_text
    success = 0

    for r in results:
        site_id      = r['site_id']
        hero_url     = r['hero_url']
        gallery_urls = r['gallery_urls']
        credits      = r.get('photo_credits')
        # Sanitize credits: collapse any newlines/tabs into a space
        if credits:
            credits = re.sub(r'[\r\n\t]+', ' ', credits).strip()

        print(f"  Patching [{site_id}] — {len(gallery_urls)} gallery images", end="")
        if credits:
            print(f", credits: {credits[:60]}{'...' if len(credits) > 60 else ''}")
        else:
            print(", no credits (personal photos)")

        patched = patch_site_entry(patched, site_id, hero_url, gallery_urls, credits)
        success += 1

    # Write patched file
    with open(SITES_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(patched)

    print(f"\n{'=' * 65}")
    print(f"DONE — {success}/{len(results)} sites patched in sites.js")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
