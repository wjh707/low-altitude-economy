#!/usr/bin/env python3
"""Debug and fix integration issue."""
import json

with open('dashboard/talent.html') as f:
    html = f.read()

print("Looking for markers in current talent.html:")
print(f"  footer: {'<div class=\"footer\">' in html}")
print(f"  loadAll(): {'  loadAll();' in html}")
print(f"  end of file: ...{html[-80:]}")

# Check what 'loadAll()' patterns exist
import re
loadall_matches = list(re.finditer(r'loadAll\s*\(\s*\)\s*;', html))
print(f"\n  loadAll() matches: {len(loadall_matches)}")
for m in loadall_matches:
    print(f"    at pos {m.start()}: ...{html[m.start()-5:m.end()+5]}...")

# Try the replacement
html_orig = html
school_section = '\n<!-- School Section -->\n<div class="school-section">SCHOOL_SECTION_HERE</div>\n'

# Insert before footer
html = html_orig.replace('<div class="footer">', school_section + '<div class="footer">')
if html != html_orig:
    print("\n✅ School section HTML inserted before footer")
else:
    print("\n❌ Footer replacement failed")
    # Try different pattern
    html = html_orig.replace('<div class="footer">', school_section + '<div class="footer">')
