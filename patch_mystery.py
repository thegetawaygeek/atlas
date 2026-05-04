#!/usr/bin/env python3
"""
ATLAS Mystery Section Patcher
Extracts updated 'The Mystery' text for all 30 sites from the PDF
and replaces the mystery field in sites.js.
"""

import re
import sys
import pypdf

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITES_JS = r"C:\Users\jaysc\Downloads\ATLAS\src\data\sites.js"
PDF_PATH = r"C:\Users\jaysc\Downloads\ATLAS\The NEW Mystery_Perspective Sections Plus The Record - 30 Sites.pdf"

# Order matches the PDF sequence exactly
SITE_ORDER = [
    ('Poverty Point',            'poverty-point'),
    ('Teotihuacan',              'teotihuacan'),
    ('Palenque',                 'palenque'),
    ('Chichén Itzá',             'chichen-itza'),
    ('Chavín de Huántar',        'chavin'),
    ('Nazca Lines',              'nazca'),
    ('Machu Picchu',             'machupicchu'),
    ('Saqsaywaman',              'saqsaywaman'),
    ('Tiwanaku and Puma Punku',  'tiwanaku'),
    ('Skara Brae',               'skara-brae'),
    ('Rosslyn Chapel',           'rosslyn-chapel'),
    ('Newgrange',                'newgrange'),
    ('Stonehenge',               'stonehenge'),
    ('Goseck Circle',            'goseck'),
    ('Ġgantija Temples',         'ggantija'),
    ('Ħal Saflieni Hypogeum',    'hal-saflieni'),
    ('Great Zimbabwe',           'great-zimbabwe'),
    ('Derinkuyu',                'derinkuyu'),
    ('Göbekli Tepe',             'gobekli-tepe'),
    ('Karahan Tepe',             'karahan-tepe'),
    ('Petra',                    'petra'),
    ('Great Pyramid',            'giza'),
    ('Dendera',                  'dendera'),
    ('Karnak',                   'karnak'),
    ('Mohenjo-daro',             'mohenjo-daro'),
    ('Kailasa Temple at Ellora', 'ellora'),
    ('Vitthala Temple at Hampi', 'hampi'),
    ('Borobudur',                'borobudur'),
    ('Angkor Wat',               'angkor-wat'),
    ('Longyou Caves',            'longyou'),
]


def clean_pdf_text(pdf_path):
    reader = pypdf.PdfReader(pdf_path)
    all_text = ''
    for page in reader.pages:
        all_text += (page.extract_text() or '') + '\n'
    all_text = re.sub(r'  +', ' ', all_text)
    lines = all_text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if (stripped and ' ' not in stripped and
                i + 1 < len(lines) and lines[i + 1].strip() == ''):
            if result and result[-1].strip() and not result[-1].strip().isupper():
                result[-1] = result[-1].rstrip() + ' ' + stripped
            else:
                result.append(stripped)
            i += 2
            continue
        result.append(line)
        i += 1
    return '\n'.join(result)


def extract_mysteries(clean_text):
    """Extract 'The Mystery' content for each site, in PDF order."""
    pattern = re.compile(
        r'The Mystery\s*\n(.*?)(?=\nThe Getaway Geek Perspective|\nThe Record|\Z)',
        re.DOTALL
    )
    matches = list(pattern.finditer(clean_text))
    print(f'  Found {len(matches)} Mystery sections in PDF')

    mysteries = {}
    for idx, m in enumerate(matches):
        content = m.group(1).strip()
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = '\n'.join(l.strip() for l in content.split('\n'))
        content = content.strip()
        _, site_id = SITE_ORDER[idx]
        mysteries[site_id] = content
    return mysteries


def escape_for_js(text):
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace('\n', '\\n')
    return text


def patch_mystery(js_text, site_id, mystery_text):
    """Replace the mystery field value in the site entry."""
    site_pattern = re.compile(
        r'(  \{[^{]*?id:\s*"' + re.escape(site_id) + r'".*?  \},)',
        re.DOTALL
    )
    match = site_pattern.search(js_text)
    if not match:
        print(f'  ERROR: site entry not found for {site_id}')
        return js_text, False

    site_block = match.group(1)
    escaped = escape_for_js(mystery_text)

    # Replace mystery field value — handles escaped quotes inside old value
    mystery_field_re = re.compile(r'(    mystery:\s*)"((?:[^"\\]|\\.)*)"')
    new_site_block, count = mystery_field_re.subn(
        lambda m: m.group(1) + '"' + escaped + '"',
        site_block
    )

    if count == 0:
        print(f'  ERROR: mystery field not found for {site_id}')
        return js_text, False

    return js_text[:match.start()] + new_site_block + js_text[match.end():], True


def main():
    print('=' * 60)
    print('ATLAS Mystery Section Patcher — 30 sites')
    print('=' * 60)

    print('\nExtracting Mystery sections from PDF...')
    clean_text = clean_pdf_text(PDF_PATH)
    mysteries = extract_mysteries(clean_text)
    print(f'  Extracted {len(mysteries)} Mystery sections\n')

    # Preview first few for spot-check before writing
    print('--- PREVIEW (first 3 sites) ---')
    for name, site_id in SITE_ORDER[:3]:
        text = mysteries.get(site_id, '')
        print(f'\n[{site_id}] ({len(text)} chars):')
        print(text[:300])
        print('...' if len(text) > 300 else '')

    print('\n--- LAST LINES (all 30 — check for stray trailing text) ---')
    for name, site_id in SITE_ORDER:
        text = mysteries.get(site_id, '')
        lines = [l for l in text.split('\n') if l.strip()]
        last = lines[-1] if lines else '(EMPTY)'
        print(f'  {site_id}: ...{last[-80:]}')

    print('\n' + '=' * 60)
    answer = input('Proceed with patching sites.js? [y/N] ').strip().lower()
    if answer != 'y':
        print('Aborted.')
        return

    print('\nPatching sites.js...')
    with open(SITES_JS, 'r', encoding='utf-8') as f:
        js_text = f.read()

    success, failed = [], []
    for _, site_id in SITE_ORDER:
        text = mysteries.get(site_id, '')
        if not text:
            print(f'  SKIP {site_id} — no content')
            failed.append(site_id)
            continue
        js_text, ok = patch_mystery(js_text, site_id, text)
        if ok:
            print(f'  [OK]  {site_id}')
            success.append(site_id)
        else:
            print(f'  [FAIL] {site_id}')
            failed.append(site_id)

    with open(SITES_JS, 'w', encoding='utf-8') as f:
        f.write(js_text)

    print()
    print('=' * 60)
    print(f'Done — {len(success)} updated, {len(failed)} failed')
    if failed:
        print(f'Failed: {failed}')
    print('=' * 60)


if __name__ == '__main__':
    main()
