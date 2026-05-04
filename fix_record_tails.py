#!/usr/bin/env python3
"""
Remove trailing site-name artifacts from all record fields in sites.js.
Each record was extracted with the next site's name appended as stray text.
"""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITES_JS = r"C:\Users\jaysc\Downloads\ATLAS\src\data\sites.js"

# Trailing text found at end of each record (as it appears DECODED, i.e. after \n resolution).
# Key = site_id, value = the trailing string to strip (the stray site name line).
# Sites with clean endings (ggantija, longyou) are omitted.
TAILS = {
    'poverty-point':  'Teotihuacan',
    'teotihuacan':    'Palenque',
    'palenque':       'Chichén Itzá',
    'chichen-itza':   'Chavín de Huántar',
    'chavin':         'The Nazca Lines',
    'nazca':          'Machu Picchu',
    'machupicchu':    'Saqsaywaman',
    'saqsaywaman':    'Tiwanaku & Puma Punku',
    'tiwanaku':       'Skara Brae',
    'skara-brae':     'Rosslyn Chapel',
    'rosslyn-chapel': 'Newgrange',
    'newgrange':      'Stonehenge',
    'stonehenge':     'The Goseck Circle',
    'goseck':         'Ggantija Temples',
    'hal-saflieni':   'Great Zimbabwe',
    'great-zimbabwe': 'Derinkuyu',
    'derinkuyu':      'Göbekli Tepe',
    'gobekli-tepe':   'Karahan Tepe',
    'karahan-tepe':   'Petra',
    'petra':          'Great Pyramid of Giza',
    'giza':           'The Temple Complex of Dendera',
    'dendera':        'Karnak Temple Complex',
    'karnak':         'Mohenjo-daro',
    'mohenjo-daro':   'The Ellora Caves/Kailasa Temple',
    'ellora':         'The Temples of Hampi',
    'hampi':          'Borobudur',
    'borobudur':      'Angkor Wat',
    'angkor-wat':     'Longyou Caves',
}

site_pattern = re.compile(r'(  \{[^{]*?id:\s*"([^"]+)".*?  \},)', re.DOTALL)
record_pattern = re.compile(r'(    record: ")((?:[^"\\]|\\.)*)"')


def fix_record(block, site_id):
    tail = TAILS.get(site_id)
    if tail is None:
        return block, False  # nothing to do

    rec_match = record_pattern.search(block)
    if not rec_match:
        print(f'  ERROR: no record field for {site_id}')
        return block, False

    raw = rec_match.group(2)

    # The tail appears in the JS-escaped string as \n<tail text>
    # In the raw JS string, newlines are stored as the two chars \n
    escaped_tail = '\\n' + tail
    if not raw.endswith(escaped_tail):
        # Try with ggantija accent variant just in case
        print(f'  WARN: expected tail not found for {site_id}')
        print(f'    expected: {repr(escaped_tail)}')
        print(f'    actual end: {repr(raw[-60:])}')
        return block, False

    new_raw = raw[: -len(escaped_tail)]
    new_record_field = rec_match.group(1) + new_raw + '"'
    new_block = block[: rec_match.start()] + new_record_field + block[rec_match.end():]
    return new_block, True


def main():
    print('=' * 60)
    print('Record Tail Fixer')
    print('=' * 60)

    with open(SITES_JS, 'r', encoding='utf-8') as f:
        js_text = f.read()

    success, failed, skipped = [], [], []

    def replacer(m):
        site_id = m.group(2)
        block = m.group(1)
        if site_id not in TAILS:
            skipped.append(site_id)
            return block
        new_block, ok = fix_record(block, site_id)
        if ok:
            success.append(site_id)
            return new_block
        else:
            failed.append(site_id)
            return block

    new_js = site_pattern.sub(replacer, js_text)

    with open(SITES_JS, 'w', encoding='utf-8') as f:
        f.write(new_js)

    print(f'Fixed:   {len(success)} sites — {success}')
    print(f'Skipped: {len(skipped)} sites (no tail expected)')
    print(f'Failed:  {len(failed)} sites — {failed}')
    print('=' * 60)


if __name__ == '__main__':
    main()
