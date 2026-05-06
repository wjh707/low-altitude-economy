#!/usr/bin/env python3
"""
低空经济科研数据自动更新脚本
每周运行一次，从OpenAlex API获取最新论文数据，更新分析结果和看板
"""

import json, urllib.request, urllib.error, ssl, time, os, sys
from collections import Counter, defaultdict

# ===== CONFIG =====
DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(DASHBOARD_DIR, 'data')
SCRIPTS_DIR = os.path.join(DASHBOARD_DIR, 'scripts')
DASHBOARD_HTML = os.path.join(DASHBOARD_DIR, 'dashboard', 'research.html')

# Search queries (5 groups covering low-altitude economy research)
QUERIES = [
    "low altitude economy",
    "urban air mobility",
    "eVTOL electric vertical takeoff",
    "unmanned aerial vehicle low altitude",
    "drone delivery logistics"
]

API_BASE = "https://api.openalex.org/works"
MAX_PER_QUERY = 200  # max papers per query

USER_AGENT = "LowAltEconResearchBot/1.0 (mailto:research@example.com)"


def fetch_openalex(query, per_page=200, pages=1):
    """Fetch papers from OpenAlex API"""
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    all_results = []

    for page in range(1, pages + 1):
        url = (f"{API_BASE}?search={encoded_query}"
               f"&sort=cited_by_count:desc"
               f"&per_page={min(per_page, 200)}"
               f"&page={page}"
               f"&select=id,title,authorships,publication_year,primary_location,cited_by_count,keywords,doi,abstract_inverted_index")
        
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                data = json.loads(resp.read().decode())
                results = data.get('results', [])
                all_results.extend(results)
                if len(results) < per_page:
                    break
            time.sleep(0.3)  # rate limiting
        except Exception as e:
            print(f"  ⚠️  Page {page} error: {e}")
            break

    return all_results


def rebuild_abstract(inverted_index):
    """Rebuild abstract text from OpenAlex inverted index"""
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return ' '.join(w for _, w in word_positions)


def transform_paper(raw):
    """Transform OpenAlex paper to our format"""
    authors = []
    for a in raw.get('authorships', []):
        author_info = a.get('author', {})
        name = author_info.get('display_name', '')
        if name:
            authors.append(name)
    
    journal = ''
    loc = raw.get('primary_location')
    if loc and loc.get('source'):
        journal = loc['source'].get('display_name', '')
    
    keywords = [k.get('display_name', '') for k in raw.get('keywords', []) if k.get('display_name')]
    
    abstract = rebuild_abstract(raw.get('abstract_inverted_index'))
    
    return {
        'title': raw.get('title', ''),
        'authors': authors,
        'year': raw.get('publication_year'),
        'journal': journal,
        'cited_by_count': raw.get('cited_by_count', 0),
        'keywords': keywords,
        'doi': raw.get('doi', ''),
        'url': raw.get('doi', ''),
        'abstract': abstract[:500] if abstract else ''
    }


def deduplicate(papers):
    """Remove duplicates by DOI first, then by title similarity"""
    seen_dois = set()
    seen_titles = set()
    unique = []
    
    for p in papers:
        doi = p.get('doi', '') or ''
        title = (p.get('title', '') or '').lower().strip()
        
        # Dedup by DOI
        if doi and doi in seen_dois:
            continue
        if doi:
            seen_dois.add(doi)
        
        # Dedup by title
        if title and title in seen_titles:
            continue
        if title:
            seen_titles.add(title)
        
        unique.append(p)
    
    return unique


def analyze(papers):
    """Perform analysis on paper data"""
    # TOP 10 papers by citation
    top10 = sorted(papers, key=lambda p: p.get('cited_by_count', 0), reverse=True)[:10]
    
    # Author analysis
    author_cites = defaultdict(int)
    author_count = defaultdict(int)
    for p in papers:
        for name in p.get('authors', []):
            if name and len(name) > 1:
                author_cites[name] += p.get('cited_by_count', 0)
                author_count[name] += 1
    
    top_authors_cite = sorted(author_cites.items(), key=lambda x: x[1], reverse=True)[:10]
    top_authors_count = sorted(author_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Keyword counting
    all_keywords = []
    for p in papers:
        for kw in p.get('keywords', []):
            if kw and isinstance(kw, str):
                all_keywords.append(kw)
    kw_counter = Counter(all_keywords)
    # Filter generic
    generic = {'computer science', 'engineering', 'key (lock)', 'telecommunications', 'mathematics', 'geography'}
    kw_filtered = [(k, c) for k, c in kw_counter.most_common(50) if k.lower() not in generic]
    
    # Theme clustering
    themes = {
        "AI/优化方法": ['reinforcement learning', 'deep learning', 'neural', 'optimization', 'scheduling', 'resource allocation', 'AI', 'machine learning'],
        "低空经济/综述": ['low altitude economy', 'economy', 'review', 'survey', 'overview', 'perspective', 'roadmap'],
        "无人机系统": ['UAV', 'drone', 'unmanned aerial', 'UAS', 'quadrotor', 'multi-rotor'],
        "UAM/城市空中交通": ['urban air mobility', 'UAM', 'air taxi', 'vertiport', 'air mobility', 'flying car'],
        "ISAC/通信感知": ['ISAC', 'integrated sensing', 'communication', 'MIMO', 'beamforming', 'radar', '6G', 'wireless'],
        "电池/能源": ['battery', 'energy', 'charging', 'power', 'fuel', 'electric', 'hydrogen'],
        "eVTOL/飞行器": ['eVTOL', 'electric vertical', 'VTOL', 'aircraft', 'propulsion', 'aerodynamic', 'rotor'],
        "空域管理": ['air traffic', 'airspace', 'traffic management', 'UTM', 'air traffic control'],
        "安全/隐私": ['security', 'privacy', 'safety', 'cyber', 'authentication', 'jamming'],
        "物流配送": ['delivery', 'logistics', 'package', 'cargo', 'last-mile', 'transportation'],
        "路径规划": ['path planning', 'trajectory', 'navigation', 'localization', 'positioning'],
        "法规/适航": ['certification', 'regulation', 'policy', 'standard', 'airworthiness', 'governance'],
        "遥感/农业": ['remote sensing', 'crop', 'agriculture', 'mapping', 'inspection', 'monitoring'],
        "噪声/环境": ['noise', 'environment', 'public acceptance', 'acoustic', 'sustainability']
    }
    
    theme_results = {}
    for theme, terms in themes.items():
        matched = []
        for p in papers:
            combined = (p.get('title', '') + ' ' + ' '.join(p.get('keywords', []))).lower()
            if any(t.lower() in combined for t in terms):
                matched.append(p)
        theme_results[theme] = matched
    
    # Year distribution (2016-2026)
    year_dist = Counter(p.get('year', 0) for p in papers)
    
    # Journal distribution
    journals = Counter(p.get('journal', 'Unknown') for p in papers if p.get('journal'))
    
    # Latest 5 papers
    latest = sorted([p for p in papers if p.get('year')], key=lambda p: p.get('year', 0), reverse=True)[:5]
    
    total_citations = sum(p.get('cited_by_count', 0) for p in papers)
    years = [p.get('year') for p in papers if p.get('year')]
    year_range = f"{min(years)} - {max(years)}" if years else "N/A"
    
    return {
        "total_papers": len(papers),
        "total_citations": total_citations,
        "year_range": year_range,
        "updated_at": time.strftime("%Y-%m-%d"),
        "year_distribution": [{"year": y, "count": year_dist.get(y, 0)} for y in range(2016, 2027)],
        "top10_papers": [{
            "rank": i + 1,
            "title": p['title'],
            "authors": p.get('authors', [])[:5],
            "year": p.get('year'),
            "journal": p.get('journal', ''),
            "cited_by_count": p.get('cited_by_count', 0),
            "doi": p.get('doi', ''),
            "keywords": p.get('keywords', [])
        } for i, p in enumerate(top10)],
        "top10_authors_by_citation": [
            {"rank": i + 1, "name": n, "citations": c, "papers": author_count[n]}
            for i, (n, c) in enumerate(top_authors_cite)
        ],
        "top10_authors_by_paper_count": [
            {"rank": i + 1, "name": n, "papers": c, "citations": author_cites[n]}
            for i, (n, c) in enumerate(top_authors_count)
        ],
        "top30_keywords": [{"keyword": kw, "count": cnt} for kw, cnt in kw_filtered[:30]],
        "theme_clusters": [
            {"theme": t, "count": len(pl), "total_citations": sum(p.get('cited_by_count', 0) for p in pl),
             "sample_papers": [p['title'] for p in pl[:3]]}
            for t, pl in sorted(theme_results.items(), key=lambda x: len(x[1]), reverse=True)
        ],
        "top20_journals": [{"journal": j, "count": c} for j, c in journals.most_common(20)],
        "latest_5_papers": [{
            "title": p['title'],
            "authors": p.get('authors', [])[:5],
            "year": p.get('year'),
            "journal": p.get('journal', ''),
            "cited_by_count": p.get('cited_by_count', 0),
            "doi": p.get('doi', ''),
            "abstract": (p.get('abstract') or '')[:300]
        } for p in latest]
    }


def update_dashboard_html(analysis_data):
    """Update the embedded data in research.html"""
    html_path = DASHBOARD_HTML
    if not os.path.exists(html_path):
        print(f"❌ Dashboard not found: {html_path}")
        return False
    
    with open(html_path, 'r') as f:
        html = f.read()
    
    # Find and replace embedded data
    old_embed_start = html.find('const EMBEDDED_ANALYSIS_DATA = {')
    old_embed_end = html.find('};', old_embed_start) + 2
    
    if old_embed_start == -1:
        print("❌ Could not find EMBEDDED_ANALYSIS_DATA in HTML")
        return False
    
    js_embed = json.dumps(analysis_data, ensure_ascii=False, indent=0)
    new_embed = f'const EMBEDDED_ANALYSIS_DATA = {js_embed};'
    
    html = html[:old_embed_start] + new_embed + html[old_embed_end:]
    
    with open(html_path, 'w') as f:
        f.write(html)
    
    print(f"✅ Dashboard updated: {html_path}")
    return True


def main():
    print("=" * 60)
    print("  🚁 低空经济科研数据自动更新")
    print("=" * 60)
    
    all_papers = []
    
    for i, query in enumerate(QUERIES):
        print(f"\n[{i+1}/{len(QUERIES)}] Searching: {query}")
        results = fetch_openalex(query, per_page=MAX_PER_QUERY, pages=5)
        papers = [transform_paper(r) for r in results if r.get('title')]
        print(f"  → Found {len(papers)} papers")
        all_papers.extend(papers)
        time.sleep(0.5)
    
    # Deduplicate
    print(f"\n📊 Total raw: {len(all_papers)}")
    all_papers = deduplicate(all_papers)
    all_papers.sort(key=lambda p: p.get('cited_by_count', 0), reverse=True)
    print(f"📊 After dedup: {len(all_papers)} papers")
    
    # Analyze
    print(f"\n🔍 Running analysis...")
    analysis = analyze(all_papers)
    print(f"   {analysis['total_papers']} papers, {analysis['total_citations']} citations")
    print(f"   {len(analysis['theme_clusters'])} research themes")
    
    # Save analysis data
    os.makedirs(DATA_DIR, exist_ok=True)
    analysis_path = os.path.join(DATA_DIR, 'analysis_data.json')
    with open(analysis_path, 'w') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"✅ Analysis saved: {analysis_path}")
    
    # Save full papers data
    papers_path = os.path.join(DATA_DIR, 'papers.json')
    # Trim abstract for storage
    paper_data = []
    for p in all_papers:
        paper_data.append({
            "title": p['title'],
            "authors": p.get('authors', []),
            "year": p.get('year'),
            "journal": p.get('journal', ''),
            "cited_by_count": p.get('cited_by_count', 0),
            "keywords": p.get('keywords', []),
            "abstract": str(p.get('abstract', ''))[:300],
            "doi": p.get('doi', ''),
        })
    with open(papers_path, 'w') as f:
        json.dump(paper_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Papers saved: {papers_path} ({len(paper_data)} papers)")
    
    # Update dashboard HTML
    update_dashboard_html(analysis)
    
    # Print summary
    print("\n" + "=" * 60)
    print("  📋 更新摘要")
    print("=" * 60)
    print(f"  论文总数:    {analysis['total_papers']}")
    print(f"  总被引次数:  {analysis['total_citations']:,}")
    print(f"  覆盖年份:    {analysis['year_range']}")
    print(f"  研究主题:    {len(analysis['theme_clusters'])} 个")
    print(f"  更新日期:    {analysis['updated_at']}")
    print(f"\n  TOP 3 论文:")
    for p in analysis['top10_papers'][:3]:
        print(f"    [{p['cited_by_count']} cites] {p['title'][:70]}...")
    print("\n✅ 更新完成!")


if __name__ == '__main__':
    main()
