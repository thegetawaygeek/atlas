#!/usr/bin/env python3
"""Inspect last line of each record field in sites.js."""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITES_JS = r"C:\Users\jaysc\Downloads\ATLAS\src\data\sites.js"

with open(SITES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

site_pattern = re.compile(r'(  \{[^{]*?id:\s*"([^"]+)".*?  \},)', re.DOTALL)

for sm in site_pattern.finditer(content):
    block = sm.group(1)
    site_id = sm.group(2)
    rec_match = re.search(r'    record: "((?:[^"\\]|\\.)*)"', block)
    if not rec_match:
        print(f'{site_id}: NO RECORD FIELD')
        continue
    raw = rec_match.group(1)
    # Decode \n escapes to find actual last line
    text = raw.replace('\\n', '\n')
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    last = lines[-1] if lines else ''
    second_last = lines[-2] if len(lines) >= 2 else ''
    print(f'{site_id}:')
    print(f'  LAST:        {repr(last)}')
    print(f'  SECOND LAST: {repr(second_last)}')
