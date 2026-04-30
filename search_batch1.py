#!/opt/anaconda3/bin/python3.12
"""
Search batch1 policies using DuckDuckGo and find official source URLs.
Focus on .gov.cn, caac.gov.cn, pkulaw.com and other authoritative sources.
"""
import json
import re
import sys
import time
from duckduckgo_search import DDGS

INPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch1.json"
OUTPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch1_result.json"

# List of authoritative source indicators
AUTHORITY_KEYWORDS = [
    "gov.cn", "caac.gov.cn", "pkulaw.com", "std.samr.gov.cn",
    "中华人民共和国中央人民政府", "中国民用航空局", "国务院",
    "北大法宝", "国家标准", "交通运输部"
]

def clean_title(title):
    """Clean title by removing trailing dots, page numbers, and sub_category artifacts."""
    # Remove trailing dots/whitespace
    t = re.sub(r'[.。\s]+$', '', title)
    # Remove page number artifacts like ".... 417"
    t = re.sub(r'\.{2,}\s*\d+$', '', t)
    t = re.sub(r'\.{2,}\s*1228地的指导意见.*$', '地的指导意见》的通知', t)
    t = re.sub(r'\.{2,}\s*1231一、地方性法规.*$', '', t)
    return t.strip()

def extract_search_keyword(item):
    """Extract the best search keywords from the item."""
    title = item["title"]
    region = item["region"]
    category = item["category"]
    
    # Clean the title first
    clean = clean_title(title)
    
    # Build keyword with region if not "全国"
    if region and region != "全国":
        return f"{clean} {region}"
    return clean

def is_authoritative(url, title_text, snippet):
    """Check if a result is from an authoritative source."""
    url_lower = url.lower()
    combined = url_lower + " " + (title_text or "").lower() + " " + (snippet or "").lower()
    
    for kw in AUTHORITY_KEYWORDS:
        if kw.lower() in combined:
            return True
    return False

def search_policy(keyword, max_retries=3):
    """Search for a policy and return results."""
    for attempt in range(max_retries):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(keyword, max_results=10, region='cn-zh'))
            return results
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return []

def determine_best_result(results, keyword):
    """From search results, find the best official URL."""
    if not results:
        return None, None
    
    # First pass: look for authoritative sources
    for r in results:
        title = r.get("title", "")
        url = r.get("href", "")
        snippet = r.get("body", "")
        
        if is_authoritative(url, title, snippet):
            # Extract source name
            found_at = extract_source_name(url, title)
            return url, found_at
    
    # Second pass: take any .gov.cn or caac.gov.cn result
    for r in results:
        url = r.get("href", "")
        if "gov.cn" in url.lower() or "caac.gov.cn" in url.lower():
            found_at = extract_source_name(url, r.get("title", ""))
            return url, found_at
    
    # Third pass: check for pkulaw
    for r in results:
        url = r.get("href", "")
        if "pkulaw.com" in url.lower():
            return url, "北大法宝"
    
    return None, None

def extract_source_name(url, title):
    """Extract a human-readable source name from URL/title."""
    url_lower = url.lower()
    
    if "caac.gov.cn" in url_lower:
        return "中国民用航空局"
    elif "www.gov.cn" in url_lower:
        return "中华人民共和国中央人民政府"
    elif "gov.cn" in url_lower:
        return "政府网站"
    elif "pkulaw.com" in url_lower:
        return "北大法宝"
    elif "std.samr.gov.cn" in url_lower:
        return "全国标准信息公共服务平台"
    elif "mof.gov.cn" in url_lower:
        return "财政部"
    elif "miit.gov.cn" in url_lower:
        return "工业和信息化部"
    elif "mot.gov.cn" in url_lower:
        return "交通运输部"
    else:
        return title[:40] if title else url[:40]

def main():
    # Read input
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print(f"Loaded {len(items)} items to search")
    
    results = []
    
    for idx, item in enumerate(items):
        keyword = extract_search_keyword(item)
        print(f"\n[{idx+1}/{len(items)}] Searching: {keyword[:80]}...")
        
        search_results = search_policy(keyword)
        
        best_url, found_at = determine_best_result(search_results, keyword)
        
        clean = clean_title(item["title"])
        
        if best_url:
            print(f"  FOUND: {best_url}")
            result = {
                "title": clean,
                "search_keyword": keyword,
                "url": best_url,
                "status": "found",
                "found_at": found_at
            }
        else:
            print(f"  NOT FOUND")
            result = {
                "title": clean,
                "search_keyword": keyword,
                "url": "",
                "status": "not_found",
                "found_at": ""
            }
        
        results.append(result)
        
        # Rate limiting - be gentle with DDG
        if idx < len(items) - 1:
            time.sleep(1.5)
    
    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    found_count = sum(1 for r in results if r["status"] == "found")
    print(f"\n\nDone! Found: {found_count}/{len(results)}. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
