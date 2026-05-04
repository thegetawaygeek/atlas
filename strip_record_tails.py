#!/usr/bin/env python3
"""Strip trailing \\n escape sequences from all record fields in sites.js."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITES_JS = r"C:\Users\jaysc\Downloads\ATLAS\src\data\sites.js"

with open(SITES_JS, 'r', encoding='utf-8') as f:
    js_text = f.read()

site_pattern = re.compile(r'(  \{[^{]*?id:\s*"([^"]+)".*?  \},)', re.DOTALL)
record_re    = re.compile(r'(    record: ")((?:[^"\\]|\\.)*)"')

fixed, clean = [], []

def replacer(sm):
    block, site_id = sm.group(1), sm.group(2)
    rec = record_re.search(block)
    if not rec:
        return block
    raw = rec.group(2)
    # Strip trailing \n escape sequences (\\n in the raw JS string)
    stripped = raw.rstrip('\\n') if raw.endswith('\\n') else raw
    # rstrip won't work cleanly on the literal two-char sequence; use regex
    stripped = re.sub(r'(\\n)+$', '', raw)
    if stripped == raw:
        clean.append(site_id)
        return block
    new_block = block[:rec.start()] + rec.group(1) + stripped + '"' + block[rec.end():]
    fixed.append(site_id)
    return new_block

new_js = site_pattern.sub(replacer, js_text)

with open(SITES_JS, 'w', encoding='utf-8') as f:
    f.write(new_js)

print(f'Stripped trailing \\n from {len(fixed)} sites: {fixed}')
print(f'Already clean ({len(clean)} sites): {clean}')
