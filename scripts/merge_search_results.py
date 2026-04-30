#!/usr/bin/env python3
"""Compare new search results with existing data and merge missing policies."""
import json

# Load existing data
with open('dashboard/policy_data.json') as f:
    existing = json.load(f)

# Load new search results
with open('data/search_results.json') as f:
    search_data = json.load(f)
    new_policies = search_data['policies']

# Build existing title set for dedup (fuzzy)
existing_titles = set()
existing_sources = set()
for p in existing:
    t = p['title'].replace(' ', '').replace('\n', '')[:40]
    existing_titles.add(t)
    if p.get('url') and p['url'].startswith('http'):
        existing_sources.add(p['url'].split('/')[2])

print(f"Existing policies: {len(existing)}")
print(f"New search results: {len(new_policies)}")

# Find truly new policies
new_entries = []
duplicates = []
for np in new_policies:
    title_key = np['title'].replace(' ', '').replace('\n', '')[:40]
    
    # Check if title partially matches
    found = False
    for et in existing_titles:
        # Check if either contains the other
        if title_key[:20] in et or et[:20] in title_key:
            found = True
            break
    
    # Also check source
    url = np.get('url', '')
    if not found and url and url.startswith('http'):
        domain = url.split('/')[2]
        if domain in existing_sources:
            found = True
    
    if found:
        duplicates.append(np['title'][:60])
    else:
        new_entries.append(np)

print(f"\n=== Duplicates ({len(duplicates)}) ===")
for d in duplicates:
    print(f"  ✗ {d}")

print(f"\n=== New Policies ({len(new_entries)}) ===")
for n in new_entries:
    print(f"  + {n['title'][:60]} | {n.get('publish_date','')} | {n.get('category','')}")
