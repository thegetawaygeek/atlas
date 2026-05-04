#!/usr/bin/env python3
"""
ATLAS Master Wiring Script — All 26 remaining sites
=====================================================
Reads each site's Final Choices folder, copies images to public/images/,
looks up photo credits, and outputs a patch dict for sites.js.

Run from the ATLAS root folder.
"""

import json
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════

ATLAS_ROOT       = r"C:\Users\jaysc\Downloads\ATLAS"
PUBLIC_IMAGES    = os.path.join(ATLAS_ROOT, "public", "images")
IMAGES_SRC       = os.path.join(ATLAS_ROOT, "Images")

# ═══════════════════════════════════════════════════════════════
# SITE MAP
# site_id: (fc_folder_name, target_public_folder, Images_src_folder)
# fc_folder_name  = subfolder inside public/images/ that has Final Choices
# target_public   = subfolder inside public/images/ to write hero/gallery to
# images_src      = subfolder inside Images/ that has the credits JSON files
# ═══════════════════════════════════════════════════════════════

SITES = [
    # site_id          fc_public_folder          target_public     images_src_folder
    ("stonehenge",     "stonehenge",              "stonehenge",     "Stonehenge"),
    ("machupicchu",    "machupicchu",             "machupicchu",    "Machu Picchu"),
    ("giza",           "great pyramid of giza",   "giza",           "Great Pyramid of Giza"),
    ("teotihuacan",    "teotihuacan",             "teotihuacan",    "Teotihuacan"),
    ("gobekli-tepe",   "gobekli-tepe",            "gobekli-tepe",   "Gobekli Tepe"),
    ("petra",          "petra",                   "petra",          "Petra"),
    ("nazca",          "nazca",                   "nazca",          "Nazca Lines"),
    ("borobudur",      "borobudur",               "borobudur",      "Borobudur"),
    ("chichen-itza",   "chichen-itza",            "chichen-itza",   "Chichen Itza"),
    ("karnak",         "karnak",                  "karnak",         "Karnak"),
    ("palenque",       "palenque",                "palenque",       "Palenque"),
    ("derinkuyu",      "derinkuyu",               "derinkuyu",      "Derinkuya"),
    ("tiwanaku",       "tiwanaku - puma punku",   "tiwanaku",       "Tiwanaku & Puma Punku"),
    ("newgrange",      "newgrange",               "newgrange",      "Newgrange"),
    ("ellora",         "ellora",                  "ellora",         "Ellora - Kailasa Temple"),
    ("skara-brae",     "skara-brae",              "skara-brae",     "Skara Brae"),
    ("dendera",        "dendera",                 "dendera",        "Dendera"),
    ("ggantija",       "ggantija",                "ggantija",       "Ggantija"),
    ("hal-saflieni",   "hal-saflieni",            "hal-saflieni",   "Hal Saflieni Hypogeum"),
    ("poverty-point",  "poverty-point",           "poverty-point",  "Poverty Point"),
    ("karahan-tepe",   "karahan-tepe",            "karahan-tepe",   "Karahan Tepe"),
    ("longyou",        "longyou",                 "longyou",        "Longyou Caves"),
    ("chavin",         "chavin",                  "chavin",         "Chavin de Huantar"),
    ("hampi",          "hampi",                   "hampi",          "Hampi"),
    ("goseck",         "goseck",                  "goseck",         "Goseck Circle"),
    ("great-zimbabwe", "great-zimbabwe",          "great-zimbabwe", "Great Zimbabwe"),
]

# ═══════════════════════════════════════════════════════════════
# NOTES: which img_XXX files come from Pexels vs Pixabay
# (all others with img_ prefix default to checking parent credits.json)
# ═══════════════════════════════════════════════════════════════

PEXELS_FILES = {
    "borobudur":    {"img_011"},
    "chichen-itza": {"img_008"},
    "derinkuyu":    {"img_002"},
    "ellora":       {"img_009", "img_010", "img_011", "img_013"},
    "gobekli-tepe": {"img_003", "img_004", "img_007", "img_012"},
    "karnak":       {"img_002", "img_003", "img_004", "img_008"},
}

PIXABAY_FILES = {
    "machupicchu": {"img_002", "img_014"},
}


# ═══════════════════════════════════════════════════════════════
# CREDIT LOOKUP
# ═══════════════════════════════════════════════════════════════

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def basename_no_hero(filename):
    """Strip (HERO) marker and return base filename with extension."""
    return filename.replace('(HERO)', '').strip()


def name_stem(filename):
    """Return filename stem without extension, e.g. wiki_003 from wiki_003.jpg"""
    return os.path.splitext(basename_no_hero(filename))[0]


def is_personal_photo(filename):
    """Timestamp-format filenames are Jason's personal photos."""
    stem = name_stem(filename)
    return bool(re.match(r'^\d{8}_\d{6}', stem))


def lookup_credit(site_id, filename, images_src_path):
    """
    Return a credit dict {photographer, license, license_url, source} or None.
    """
    if is_personal_photo(filename):
        return None   # personal photo — no credit needed

    stem = name_stem(filename)   # e.g. "wiki_003" or "img_011"

    if stem.startswith('wiki_'):
        # Wikimedia credits JSON
        wiki_credits_path = os.path.join(images_src_path, 'wikimedia', 'credits.json')
        data = load_json(wiki_credits_path)
        for img in data.get('images', []):
            local = img.get('local_file', '').replace('\\', '/')
            # match by stem anywhere in the local_file path
            if f'/{stem}.' in local or local.endswith(f'/{stem}.jpg') or local.endswith(f'/{stem}.png'):
                return img
        # fallback: match by stem in filename portion
        for img in data.get('images', []):
            local = img.get('local_file', '')
            if stem in os.path.basename(local.replace('\\', '/')):
                return img

    elif stem.startswith('img_'):
        # Check parent credits.json (has pexels + pixabay entries)
        parent_credits_path = os.path.join(images_src_path, 'credits.json')
        data = load_json(parent_credits_path)

        # Determine which subfolder to look in
        pexels_set  = PEXELS_FILES.get(site_id, set())
        pixabay_set = PIXABAY_FILES.get(site_id, set())

        if stem in pexels_set:
            subfolder_hint = 'pexels'
        elif stem in pixabay_set:
            subfolder_hint = 'pixabay'
        else:
            subfolder_hint = None

        for img in data.get('images', []):
            local = img.get('local_file', '').replace('\\', '/')
            local_stem = os.path.splitext(os.path.basename(local))[0]
            if local_stem != stem:
                continue
            if subfolder_hint and subfolder_hint not in local:
                continue
            return img

        # fallback: any match by stem
        for img in data.get('images', []):
            local = img.get('local_file', '').replace('\\', '/')
            if os.path.splitext(os.path.basename(local))[0] == stem:
                return img

    return None


def format_credit_entry(credit):
    """Format one credit entry as 'Photographer / License (Source)'."""
    if credit is None:
        return None
    photographer = credit.get('photographer', 'Unknown')
    # Clean HTML tags and collapse newlines/tabs
    photographer = re.sub(r'<[^>]+>', '', photographer)
    photographer = re.sub(r'[\r\n\t]+', ' ', photographer).strip()
    license_name = credit.get('license', '')
    source = credit.get('source', 'Wikimedia Commons')

    parts = [photographer, license_name]
    if source == 'Wikimedia Commons':
        parts.append('(Wikimedia Commons)')
    elif source == 'Pexels':
        parts[-1] = 'Pexels License'
    elif source == 'Pixabay':
        parts[-1] = 'Pixabay Content License'

    return ' / '.join(p for p in parts if p)


def build_photo_credits(hero_file, gallery_files, site_id, images_src_path):
    """
    Build the photoCredits string.
    Hero is listed first, then unique gallery credits (deduped by photographer).
    Personal photos are omitted entirely.
    """
    parts = []
    seen_photographers = set()

    # Hero
    hero_credit = lookup_credit(site_id, hero_file, images_src_path)
    if hero_credit:
        entry = format_credit_entry(hero_credit)
        if entry:
            parts.append(f"Hero: {entry}.")
            seen_photographers.add(hero_credit.get('photographer', ''))

    # Gallery
    gallery_credits = []
    for fname in gallery_files:
        c = lookup_credit(site_id, fname, images_src_path)
        if c is None:
            continue  # personal photo
        photographer = c.get('photographer', '')
        if photographer in seen_photographers:
            continue  # already credited
        entry = format_credit_entry(c)
        if entry:
            gallery_credits.append(entry)
            seen_photographers.add(photographer)

    if gallery_credits:
        parts.append("Gallery: " + "; ".join(gallery_credits) + ".")

    if not parts:
        return None   # all personal photos — no credits string needed

    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════
# MAIN PROCESSING
# ═══════════════════════════════════════════════════════════════

def process_site(site_id, fc_public_folder, target_public_folder, images_src_folder):
    """
    Process one site:
      - read Final Choices
      - copy images to target public folder
      - build credit string
    Returns dict with site_id, hero_path, gallery_paths, photo_credits.
    """
    fc_path      = os.path.join(PUBLIC_IMAGES, fc_public_folder, "Final Choices")
    target_path  = os.path.join(PUBLIC_IMAGES, target_public_folder)
    src_path     = os.path.join(IMAGES_SRC, images_src_folder)

    if not os.path.isdir(fc_path):
        print(f"  ERROR: Final Choices not found at {fc_path}")
        return None

    os.makedirs(target_path, exist_ok=True)

    # Collect image files (exclude json/txt)
    raw_files = [
        f for f in os.listdir(fc_path)
        if not f.endswith('.json') and not f.endswith('.txt')
    ]

    # Separate hero from gallery
    hero_files   = [f for f in raw_files if '(HERO)' in f]
    gallery_files = sorted([f for f in raw_files if '(HERO)' not in f])

    if not hero_files:
        print(f"  WARNING: No HERO image found for {site_id}")
        return None

    hero_file = hero_files[0]

    # Copy hero
    hero_src  = os.path.join(fc_path, hero_file)
    hero_dest = os.path.join(target_path, "hero.jpg")
    shutil.copy2(hero_src, hero_dest)

    # Copy gallery images
    gallery_dest_paths = []
    for i, fname in enumerate(gallery_files, start=1):
        src  = os.path.join(fc_path, fname)
        # Preserve original extension (some are .png)
        ext  = os.path.splitext(fname)[1].lower()
        dest_name = f"gallery-{i}{ext}"
        dest = os.path.join(target_path, dest_name)
        shutil.copy2(src, dest)
        gallery_dest_paths.append(f"/images/{target_public_folder}/{dest_name}")

    # Build credits
    photo_credits = build_photo_credits(hero_file, gallery_files, site_id, src_path)

    hero_url = f"/images/{target_public_folder}/hero.jpg"

    print(f"  hero:    {hero_file}  →  hero.jpg")
    for orig, url in zip(gallery_files, gallery_dest_paths):
        print(f"  gallery: {orig:30s}  →  {os.path.basename(url)}")
    if photo_credits:
        print(f"  credits: {photo_credits[:100]}{'...' if len(photo_credits) > 100 else ''}")
    else:
        print(f"  credits: (none — personal photos only)")

    return {
        "site_id":       site_id,
        "hero_url":      hero_url,
        "gallery_urls":  gallery_dest_paths,
        "photo_credits": photo_credits,
    }


def main():
    print("=" * 65)
    print("ATLAS Master Wiring Script — 26 sites")
    print("=" * 65)
    print()

    results = []

    for site_id, fc_folder, target_folder, src_folder in SITES:
        print(f"\n[{site_id}]")
        result = process_site(site_id, fc_folder, target_folder, src_folder)
        if result:
            results.append(result)
        else:
            print(f"  SKIPPED")

    # Write results JSON for the sites.js patch step
    out_path = os.path.join(ATLAS_ROOT, "wiring_results.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print(f"DONE — {len(results)}/{len(SITES)} sites processed")
    print(f"Results saved to: {out_path}")
    print("=" * 65)
    print("\nNext: run patch_sites_js.py to update sites.js")


if __name__ == "__main__":
    main()
