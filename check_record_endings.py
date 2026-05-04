#!/usr/bin/env python3
"""Check exact raw endings of record fields to spot trailing \n sequences."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITES_JS = r"C:\Users\jaysc\Downloads\ATLAS\src\data\sites.js"

with open(SITES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

site_pattern = re.compile(r'(  \{[^{]*?id:\s*"([^"]+)".*?  \},)', re.DOTALL)

for sm in site_pattern.finditer(content):
    block, site_id = sm.group(1), sm.group(2)
    rec = re.search(r'    record: "((?:[^"\\]|\\.)*)"', block)
    if not rec:
        continue
    raw = rec.group(1)
    # Show the last 60 raw chars (escaped) so we can see trailing \n sequences
    tail = raw[-60:]
    print(f'{site_id}: ...{repr(tail)}')
