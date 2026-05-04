#!/usr/bin/env python3
"""
ATLAS Travel Reality Patcher
Reads the PDF, cleans the word-per-line extraction artifacts,
parses all 30 sites' structured sections, and patches sites.js.
"""

import re
import sys
import pypdf

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITES_JS = r"C:\Users\jaysc\Downloads\ATLAS\src\data\sites.js"
PDF_PATH = r"C:\Users\jaysc\Downloads\ATLAS\Travel Reality First 30 Sites.pdf"

SECTION_HEADERS = [
    "HOW TO GET THERE",
    "WHAT TO EXPECT ON ARRIVAL",
    "HOW LONG TO SPEND",
    "BEST TIME TO VISIT",
    "PHYSICAL DEMANDS",
    "ESSENTIAL TIPS",
]

# Some PDF pages have "(Revised)" appended to certain headers.
# Normalize these back to the canonical names (case-insensitive match at parse time).
HEADER_ALIASES = {
    "WHAT TO EXPECT ON ARRIVAL (REVISED)": "WHAT TO EXPECT ON ARRIVAL",
    "ESSENTIAL TIPS (REVISED)": "ESSENTIAL TIPS",
    "HOW TO GET THERE (REVISED)": "HOW TO GET THERE",
    "HOW LONG TO SPEND (REVISED)": "HOW LONG TO SPEND",
    "BEST TIME TO VISIT (REVISED)": "BEST TIME TO VISIT",
    "PHYSICAL DEMANDS (REVISED)": "PHYSICAL DEMANDS",
}

# Map site names as they appear in the PDF → site IDs in sites.js
SITE_NAME_TO_ID = {
    "Great Pyramid of Giza": "giza",
    "Petra": "petra",
    "Stonehenge": "stonehenge",
    "Machu Picchu": "machupicchu",
    "Teotihuacan": "teotihuacan",
    "Göbekli Tepe": "gobekli-tepe",
    "Angkor Wat": "angkor-wat",
    "Nazca Lines": "nazca",
    "Borobudur": "borobudur",
    "Chichén Itzá": "chichen-itza",
    "Karnak": "karnak",
    "Palenque": "palenque",
    "Derinkuyu": "derinkuyu",
    "Tiwanaku & Puma Punku": "tiwanaku",
    "Newgrange": "newgrange",
    "Ellora / Kailasa Temple": "ellora",
    "Skara Brae": "skara-brae",
    "Dendera": "dendera",
    "Rosslyn Chapel": "rosslyn-chapel",
    "Ġgantija Temples": "ggantija",
    "Hal Saflieni Hypogeum": "hal-saflieni",
    "Poverty Point": "poverty-point",
    "Karahan Tepe": "karahan-tepe",
    "The Longyou Caves": "longyou",
    "Chavín de Huántar": "chavin",
    "Saqsaywaman": "saqsaywaman",
    "Temples of Hampi": "hampi",
    "Mohenjo-daro": "mohenjo-daro",
    "Goseck Circle": "goseck",
    "Great Zimbabwe": "great-zimbabwe",
}


def clean_pdf_text(pdf_path):
    """Extract and clean all PDF text, fixing word-per-line artifacts."""
    reader = pypdf.PdfReader(pdf_path)
    all_text = ''
    for page in reader.pages:
        all_text += (page.extract_text() or '') + '\n'

    # Step 1: Normalize double-spaces (PDF justification artifact)
    all_text = re.sub(r'  +', ' ', all_text)

    # Step 2: Fix word-per-line: single words on their own line followed by
    # a blank-space-only line are continuations of the previous paragraph.
    lines = all_text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Single word (no spaces) followed by a whitespace-only line?
        if (stripped and ' ' not in stripped and
                i + 1 < len(lines) and lines[i + 1].strip() == ''):
            # Attach to the previous line if it's a real content line
            if result and result[-1].strip() and not result[-1].strip().isupper():
                result[-1] = result[-1].rstrip() + ' ' + stripped
            else:
                result.append(stripped)
            i += 2  # skip the word + blank line
            continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def find_site_names_in_text(text):
    """
    Find all site name occurrences in the cleaned text.
    Returns list of (match_object, site_id, site_name) sorted by position.
    """
    sorted_names = sorted(SITE_NAME_TO_ID.keys(), key=len, reverse=True)
    pattern = re.compile(
        r'^(' + '|'.join(re.escape(n) for n in sorted_names) + r')\s*\([^)\n]+\)\s*$',
        re.MULTILINE
    )
    matches = []
    for m in pattern.finditer(text):
        site_name = m.group(1)
        site_id = SITE_NAME_TO_ID[site_name]
        matches.append((m, site_id, site_name))
    return matches


def parse_sections(block):
    """
    Parse a site text block into {canonical_header: content}.
    Recognizes all 6 standard headers plus their '(Revised)' variants.
    """
    # Build all recognizable header strings (standard + Revised variants)
    all_headers = list(SECTION_HEADERS) + [
        h.title().replace('(revised)', '(Revised)') for h in HEADER_ALIASES
    ]
    # Match any of these headers on a line by themselves (case-insensitive)
    header_re = re.compile(
        r'^(' + '|'.join(re.escape(h) for h in all_headers) + r')\s*$',
        re.MULTILINE | re.IGNORECASE
    )

    sections = {}
    parts = header_re.split(block)
    # parts = [preamble, header1, content1, header2, content2, ...]
    i = 1
    while i < len(parts) - 1:
        raw_header = parts[i].strip().upper()
        # Resolve alias to canonical name
        canonical = HEADER_ALIASES.get(raw_header, raw_header)
        content = parts[i + 1]
        # Normalize whitespace in content
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = '\n'.join(l.strip() for l in content.split('\n'))
        content = content.strip()
        sections[canonical] = content
        i += 2

    return sections


def format_travel_reality(sections):
    """Format sections into a single string: HEADER\\ncontent, blocks joined by \\n\\n."""
    ordered = [
        "HOW TO GET THERE",
        "WHAT TO EXPECT ON ARRIVAL",
        "HOW LONG TO SPEND",
        "BEST TIME TO VISIT",
        "PHYSICAL DEMANDS",
        "ESSENTIAL TIPS",
    ]
    parts = []
    for header in ordered:
        content = sections.get(header, '').strip()
        if content:
            parts.append(f"{header}\n{content}")
    return '\n\n'.join(parts)


def escape_for_js(text):
    """Escape text for safe embedding in a JS double-quoted string."""
    text = text.replace('\\', '\\\\')   # backslash → \\
    text = text.replace('"', '\\"')      # " → \"
    text = text.replace('\n', '\\n')     # newline → \n
    return text


def patch_travel_reality(js_text, site_id, new_value):
    """
    Find the site entry and replace its travelReality field.
    Uses '(?:[^"\\\\]|\\\\.)*' to correctly handle escaped quotes inside the old value.
    """
    site_pattern = re.compile(
        r'(  \{[^{]*?id:\s*"' + re.escape(site_id) + r'".*?  \},)',
        re.DOTALL
    )
    match = site_pattern.search(js_text)
    if not match:
        print(f"  ERROR: site entry not found for '{site_id}'")
        return js_text, False

    site_block = match.group(1)

    # Correctly match JS double-quoted strings with backslash escapes:
    # "(?:[^"\\]|\\.)*"  — matches " then any number of (non-quote/non-backslash | backslash+any) then "
    tr_pattern = re.compile(
        r'(    travelReality:\s*)"(?:[^"\\]|\\.)*"',
        re.DOTALL
    )
    escaped = escape_for_js(new_value)

    def replacer(m):
        return m.group(1) + '"' + escaped + '"'

    new_site_block, count = tr_pattern.subn(replacer, site_block)

    if count == 0:
        print(f"  ERROR: travelReality field not found in entry for '{site_id}'")
        return js_text, False

    return js_text[:match.start()] + new_site_block + js_text[match.end():], True


def main():
    print("=" * 60)
    print("ATLAS Travel Reality Patcher")
    print("=" * 60)
    print()

    # Step 1: Clean PDF text
    print("Extracting and cleaning PDF text...")
    clean_text = clean_pdf_text(PDF_PATH)

    # Step 2: Find site name positions
    site_matches = find_site_names_in_text(clean_text)
    print(f"Found {len(site_matches)} site blocks in PDF")

    if not site_matches:
        print("ERROR: No site names found. Aborting.")
        sys.exit(1)

    # Step 3: Extract sections for each site
    sites_data = {}
    for idx, (match, site_id, site_name) in enumerate(site_matches):
        start = match.end()
        end = site_matches[idx + 1][0].start() if idx + 1 < len(site_matches) else len(clean_text)
        block = clean_text[start:end]
        sections = parse_sections(block)
        sites_data[site_id] = sections
        print(f"  [PARSED] {site_name} ({site_id}) — {len(sections)} sections: {list(sections.keys())}")

    print()

    # Step 4: Patch sites.js
    print("Patching sites.js...")
    with open(SITES_JS, 'r', encoding='utf-8') as f:
        js_text = f.read()

    success = []
    failed = []

    for site_id, sections in sites_data.items():
        formatted = format_travel_reality(sections)
        if not formatted.strip():
            print(f"  SKIP {site_id} — no content")
            failed.append(site_id)
            continue
        js_text, ok = patch_travel_reality(js_text, site_id, formatted)
        if ok:
            print(f"  [OK]  {site_id}")
            success.append(site_id)
        else:
            print(f"  [FAIL] {site_id}")
            failed.append(site_id)

    with open(SITES_JS, 'w', encoding='utf-8') as f:
        f.write(js_text)

    print()
    print("=" * 60)
    print(f"Done — {len(success)} updated, {len(failed)} failed")
    if failed:
        print(f"Failed: {failed}")
    print("=" * 60)

    # Step 5: Preview first site
    if success:
        first_id = success[0]
        print(f"\nPreview — {first_id}:")
        print("-" * 40)
        print(format_travel_reality(sites_data[first_id])[:600])
        print("...")

    # Report any mapping entries not found in PDF
    found_ids = set(sites_data.keys())
    all_ids = set(SITE_NAME_TO_ID.values())
    missing = all_ids - found_ids
    if missing:
        print(f"\nNOT FOUND IN PDF: {sorted(missing)}")


if __name__ == "__main__":
    main()
