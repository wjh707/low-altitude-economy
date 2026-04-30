#!/usr/bin/env python3
"""
generate_companies.py — Generate company statistics from companies.json

Usage:
    python scripts/generate_companies.py
    python scripts/generate_companies.py --input-dir data --output-dir data

Output:
    - data/company_stats.json  (or custom output-dir/company_stats.json)
    - Copies companies.json to dashboard/ if output-dir is data/

Statistics generated:
    - Summary: total, listed, unlisted, chain link count
    - by_chain_link: count, companies list, listed/unlisted counts per link
    - by_city: Top N cities by company count
    - by_province: province distribution with city breakdown
    - by_sub_category: sub-category aggregation
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime


def load_companies(input_dir):
    """Load companies from JSON file."""
    path = os.path.join(input_dir, 'companies.json')
    if not os.path.exists(path):
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        companies = json.load(f)
    print(f"Loaded {len(companies)} companies from {path}")
    return companies


def compute_stats(companies):
    """Compute all statistics from companies data."""
    # --- Summary ---
    total = len(companies)
    listed = sum(1 for c in companies if c.get('listed', False))
    unlisted = total - listed

    # Chain links
    chain_links_set = set()
    for c in companies:
        link = c.get('chain_link', '').strip()
        if link:
            chain_links_set.add(link)
    chain_link_count = len(chain_links_set)

    summary = {
        'total_companies': total,
        'listed_companies': listed,
        'unlisted_companies': unlisted,
        'chain_link_count': chain_link_count,
    }

    # --- by_chain_link ---
    by_chain_link = defaultdict(lambda: {'count': 0, 'companies': [], 'listed': 0, 'unlisted': 0})
    for c in companies:
        link = c.get('chain_link', '').strip()
        name = c.get('name', '')
        is_listed = c.get('listed', False)
        by_chain_link[link]['count'] += 1
        by_chain_link[link]['companies'].append(name)
        if is_listed:
            by_chain_link[link]['listed'] += 1
        else:
            by_chain_link[link]['unlisted'] += 1
    by_chain_link = dict(sorted(by_chain_link.items()))

    # --- by_city (Top 10) ---
    by_city_raw = defaultdict(lambda: {'count': 0, 'companies': []})
    for c in companies:
        city = c.get('city', '未知')
        name = c.get('name', '')
        by_city_raw[city]['count'] += 1
        by_city_raw[city]['companies'].append(name)
    by_city = dict(sorted(by_city_raw.items(), key=lambda x: -x[1]['count']))

    # --- by_province ---
    by_province_raw = defaultdict(lambda: {'count': 0, 'cities': set()})
    for c in companies:
        province = c.get('province', '未知')
        city = c.get('city', '未知')
        by_province_raw[province]['count'] += 1
        by_province_raw[province]['cities'].add(city)
    by_province = {}
    for prov in sorted(by_province_raw.keys(), key=lambda p: -by_province_raw[p]['count']):
        by_province[prov] = {
            'count': by_province_raw[prov]['count'],
            'cities': sorted(by_province_raw[prov]['cities'])
        }

    # --- by_sub_category ---
    by_sub_category = defaultdict(lambda: {'count': 0, 'companies': []})
    for c in companies:
        sub = c.get('sub_category', '未知').strip()
        name = c.get('name', '')
        if sub:
            by_sub_category[sub]['count'] += 1
            by_sub_category[sub]['companies'].append(name)
    by_sub_category = dict(sorted(by_sub_category.items(), key=lambda x: -x[1]['count']))

    # Assemble stats
    stats = {
        'summary': summary,
        'by_chain_link': by_chain_link,
        'by_city': by_city,
        'by_province': by_province,
        'by_sub_category': by_sub_category,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'version': '1.1.0',
    }
    return stats


def save_stats(stats, output_dir):
    """Save stats to JSON file and print summary."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, 'company_stats.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"Stats saved to {path}")

    # Print summary
    s = stats['summary']
    print(f"\n=== Company Statistics ===")
    print(f"Total companies: {s['total_companies']}")
    print(f"Listed: {s['listed_companies']}, Unlisted: {s['unlisted_companies']}")
    print(f"Chain links: {s['chain_link_count']}")
    print(f"\n--- By Chain Link ---")
    for link, info in stats['by_chain_link'].items():
        print(f"  {link}: {info['count']} companies ({info['listed']} listed, {info['unlisted']} unlisted)")
    print(f"\n--- Top Cities ---")
    for city, info in list(stats['by_city'].items())[:10]:
        print(f"  {city}: {info['count']} companies")
    print(f"\n--- By Province ---")
    for prov, info in stats['by_province'].items():
        print(f"  {prov}: {info['count']} companies | cities: {', '.join(info['cities'])}")
    print(f"\nGenerated at: {stats['generated_at']}")


def copy_to_dashboard(source_dir, dashboard_dir):
    """Copy companies.json to dashboard directory."""
    src = os.path.join(source_dir, 'companies.json')
    dst = os.path.join(dashboard_dir, 'companies.json')
    if os.path.exists(src):
        import shutil
        shutil.copy2(src, dst)
        print(f"Copied {src} -> {dst}")
    else:
        print(f"Warning: {src} not found, skipping copy")


def main():
    parser = argparse.ArgumentParser(
        description='Generate company statistics from companies.json'
    )
    parser.add_argument(
        '--input-dir', '-i',
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'),
        help='Input directory containing companies.json (default: ../data relative to script)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default=None,
        help='Output directory for company_stats.json (default: same as input-dir)'
    )
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)

    # If output-dir not specified, use input-dir
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
    else:
        output_dir = input_dir

    # Resolve dashboard path relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_dir = os.path.join(project_root, 'dashboard')

    companies = load_companies(input_dir)
    stats = compute_stats(companies)
    save_stats(stats, output_dir)

    # If output is data/, also copy to dashboard
    if os.path.basename(output_dir) == 'data' or output_dir == input_dir:
        copy_to_dashboard(input_dir, dashboard_dir)


if __name__ == '__main__':
    main()
