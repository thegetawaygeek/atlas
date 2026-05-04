#!/usr/bin/env python3
"""
ATLAS Record Section Patcher
Extracts 'The Record' text for all 30 sites from the PDF and patches sites.js.
"""

import re
import sys
import pypdf

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITES_JS = r"C:\Users\jaysc\Downloads\ATLAS\src\data\sites.js"
PDF_PATH = r"C:\Users\jaysc\Downloads\ATLAS\The NEW Mystery_Perspective Sections Plus The Record - 30 Sites.pdf"

# Order matches the PDF sequence exactly
SITE_ORDER = [
    ('Poverty Point',           'poverty-point'),
    ('Teotihuacan',             'teotihuacan'),
    ('Palenque',                'palenque'),
    ('Chichén Itzá',            'chichen-itza'),
    ('Chavín de Huántar',       'chavin'),
    ('Nazca Lines',             'nazca'),
    ('Machu Picchu',            'machupicchu'),
    ('Saqsaywaman',             'saqsaywaman'),
    ('Tiwanaku and Puma Punku', 'tiwanaku'),
    ('Skara Brae',              'skara-brae'),
    ('Rosslyn Chapel',          'rosslyn-chapel'),
    ('Newgrange',               'newgrange'),
    ('Stonehenge',              'stonehenge'),
    ('Goseck Circle',           'goseck'),
    ('Ġgantija Temples',        'ggantija'),
    ('Ħal Saflieni Hypogeum',   'hal-saflieni'),
    ('Great Zimbabwe',          'great-zimbabwe'),
    ('Derinkuyu',               'derinkuyu'),
    ('Göbekli Tepe',            'gobekli-tepe'),
    ('Karahan Tepe',            'karahan-tepe'),
    ('Petra',                   'petra'),
    ('Great Pyramid',           'giza'),
    ('Dendera',                 'dendera'),
    ('Karnak',                  'karnak'),
    ('Mohenjo-daro',            'mohenjo-daro'),
    ('Kailasa Temple at Ellora','ellora'),
    ('Vitthala Temple at Hampi','hampi'),
    ('Borobudur',               'borobudur'),
    ('Angkor Wat',              'angkor-wat'),
    ('Longyou Caves',           'longyou'),
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


def extract_records(clean_text):
    pattern = re.compile(
        r'The Record\s*\n(.*?)(?=\nThe Mystery|\nThe Getaway Geek Perspective|\Z)',
        re.DOTALL
    )
    matches = list(pattern.finditer(clean_text))
    records = {}
    for idx, m in enumerate(matches):
        content = m.group(1).strip()
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = '\n'.join(l.strip() for l in content.split('\n'))
        content = content.strip()
        _, site_id = SITE_ORDER[idx]
        records[site_id] = content
    return records


def escape_for_js(text):
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace('\n', '\\n')
    return text


def patch_record(js_text, site_id, record_text):
    """Add or replace a 'record' field in the site entry, placed before 'mystery'."""
    site_pattern = re.compile(
        r'(  \{[^{]*?id:\s*"' + re.escape(site_id) + r'".*?  \},)',
        re.DOTALL
    )
    match = site_pattern.search(js_text)
    if not match:
        print(f'  ERROR: site entry not found for {site_id}')
        return js_text, False

    site_block = match.group(1)
    escaped = escape_for_js(record_text)
    new_field = f'    record: "{escaped}",\n'

    # Remove existing record field if present
    site_block = re.sub(r'    record: "(?:[^"\\]|\\.)*",\n', '', site_block)

    # Insert before 'mystery:' line
    mystery_match = re.search(r'    mystery:', site_block)
    if not mystery_match:
        print(f'  ERROR: mystery field not found for {site_id}')
        return js_text, False

    insert_pos = mystery_match.start()
    new_site_block = site_block[:insert_pos] + new_field + site_block[insert_pos:]

    return js_text[:match.start()] + new_site_block + js_text[match.end():], True


def main():
    print('=' * 60)
    print('ATLAS Record Section Patcher — 30 sites')
    print('=' * 60)

    print('Extracting Record sections from PDF...')
    clean_text = clean_pdf_text(PDF_PATH)
    records = extract_records(clean_text)
    print(f'Extracted {len(records)} Record sections\n')

    print('Patching sites.js...')
    with open(SITES_JS, 'r', encoding='utf-8') as f:
        js_text = f.read()

    success, failed = [], []
    for _, site_id in SITE_ORDER:
        text = records.get(site_id, '')
        if not text:
            print(f'  SKIP {site_id} — no content')
            failed.append(site_id)
            continue
        js_text, ok = patch_record(js_text, site_id, text)
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

    # Preview first site
    if success:
        first = success[0]
        print(f'\nPreview — {first}:')
        print(records[first][:300])


if __name__ == '__main__':
    main()
