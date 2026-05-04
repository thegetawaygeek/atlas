#!/usr/bin/env python3
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Users\jaysc\Downloads\ATLAS\src\data\sites.js', 'r', encoding='utf-8') as f:
    content = f.read()

site_pattern = re.compile(r'(  \{[^{]*?id:\s*"([^"]+)".*?  \},)', re.DOTALL)
field_re = re.compile(r'    (mystery|perspective):\s*"((?:[^"\\]|\\.)*)"')

for sm in site_pattern.finditer(content):
    block, site_id = sm.group(1), sm.group(2)
    if site_id not in ('poverty-point', 'giza', 'longyou'):
        continue
    for fm in field_re.finditer(block):
        field, raw = fm.group(1), fm.group(2)
        print(f'--- {site_id} / {field} ---')
        print(repr(raw[:500]))
        print()
