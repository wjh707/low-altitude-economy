#!/usr/bin/env python3
"""Properly integrate school section into talent.html"""
import json

with open('dashboard/talent.html') as f:
    html = f.read()

# School data
with open('data/school_majors.json') as f:
    school_data = json.load(f)

with open('dashboard/school_stats.json') as f:
    school_stats = json.load(f)

# School section HTML
school_section = """
<!-- School Section -->
<div class="section-title" style="max-width:1400px;margin:0 auto;padding:20px 24px 0">
  <h2 style="font-size:18px;font-weight:600;color:#1a73e8">🎓 高校低空经济专业布局</h2>
  <p style="font-size:13px;color:#5f6368;margin-top:4px">全国高校低空经济相关专业开设情况，含本科、研究生及高职</p>
</div>
<div style="max-width:1400px;margin:0 auto;padding:0 24px 20px">
  <div class="stats-row" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:20px">
    <div class="stat-card"><div class="label">开设院校</div><div class="value" id="schTotal">-</div><div class="sublabel">覆盖全国</div></div>
    <div class="stat-card"><div class="label">本科专业</div><div class="value" id="schUndergrad">-</div><div class="sublabel">低空技术与工程</div></div>
    <div class="stat-card"><div class="label">研究生</div><div class="value" id="schGrad">-</div><div class="sublabel">交叉学科/博士点</div></div>
    <div class="stat-card"><div class="label">高职专业</div><div class="value" id="schVocation">-</div><div class="sublabel">无人机应用技术</div></div>
  </div>
  <div class="chart-row">
    <div class="chart-box">
      <h3>🏫 首批6所本科高校</h3>
      <div id="chartSchoolMap" class="chart" style="height:300px"></div>
    </div>
    <div class="chart-box">
      <h3>📊 层次分布</h3>
      <div id="chartSchoolLevel" class="chart" style="height:300px"></div>
    </div>
  </div>
  <div class="chart-box" style="margin-bottom:20px">
    <h3>📍 按省份分布</h3>
    <div id="chartSchoolProvince" class="chart" style="height:250px"></div>
  </div>
  <div class="chart-box">
    <h3>📜 高校专业名单</h3>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>学校</th>
            <th>专业</th>
            <th>层次</th>
            <th>状态</th>
            <th>年份</th>
            <th>城市</th>
            <th>省份</th>
          </tr>
        </thead>
        <tbody id="schoolTableBody"></tbody>
      </table>
    </div>
  </div>
</div>
"""

# Insert school section before footer
if '<div class="footer">' in html:
    html = html.replace('<div class="footer">', school_section + '<div class="footer">')
    print("✅ School section HTML inserted")
else:
    print("❌ Footer not found, aborting")
    exit(1)

# Now insert school JS before loadAll();
school_data_js = json.dumps(school_data, ensure_ascii=False)
school_stats_js = json.dumps(school_stats, ensure_ascii=False)

school_js = f"""
  // ---- 高校专业渲染 ----
  const SCHOOL_DATA = {school_data_js};
  const SCHOOL_STATS = {school_stats_js};

  function renderSchoolStats() {{
    const s = SCHOOL_STATS;
    document.getElementById('schTotal').textContent = s.total_schools || '-';
    document.getElementById('schUndergrad').textContent = (s.by_level && s.by_level['本科']) || '-';
    document.getElementById('schGrad').textContent = (s.by_level && s.by_level['研究生']) || '-';
    document.getElementById('schVocation').textContent = (s.by_level && s.by_level['高职']) || '-';
  }}

  function renderSchoolLevelChart() {{
    const chart = echarts.init(document.getElementById('chartSchoolLevel'));
    const byLevel = SCHOOL_STATS.by_level || {{}};
    const items = [
      {{ name: '本科', value: byLevel['本科'] || 0, color: '#1a73e8' }},
      {{ name: '研究生', value: byLevel['研究生'] || 0, color: '#34a853' }},
      {{ name: '高职', value: byLevel['高职'] || 0, color: '#fbbc04' }}
    ].filter(i => i.value > 0);
    var option = {{
      tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}}所 ({{d}}%)' }},
      series: [{{
        type: 'pie', radius: ['40%', '70%'],
        label: {{ formatter: '{{b}}\\\\n{{c}}所', fontSize: 12 }},
        data: items
      }}]
    }};
    chart.setOption(option);
  }}

  function renderSchoolMapChart() {{
    const chart = echarts.init(document.getElementById('chartSchoolMap'));
    const undergrad = SCHOOL_DATA.filter(d => d.level === '本科' && d.type !== '计划中');
    var names = undergrad.map(d => d.school.replace(/大学|学院/g,'')).reverse();
    var majors = undergrad.map(d => d.major).reverse();
    chart.setOption({{
      tooltip: {{ trigger: 'item' }},
      grid: {{ containLabel: true, left: 20, right: 120, bottom: 20, top: 10 }},
      xAxis: {{ type: 'value', show: false }},
      yAxis: {{ type: 'category', data: names, axisLabel: {{ fontSize: 11 }} }},
      series: [{{
        type: 'bar', data: undergrad.map(function(){{return 1}}).reverse(),
        barWidth: 18,
        itemStyle: {{ color: new echarts.graphic.LinearGradient(0,0,1,0,[
          {{offset:0,color:'#1a73e8'}},{{offset:1,color:'#6ab7ff'}}
        ]), borderRadius: [0,4,4,0] }},
        label: {{ show: true, position: 'right', formatter: function(p){{return majors[p.dataIndex];}}, fontSize: 10, color: '#333' }}
      }}]
    }});
  }}

  function renderSchoolProvinceChart() {{
    const chart = echarts.init(document.getElementById('chartSchoolProvince'));
    var entries = Object.entries(SCHOOL_STATS.by_province || {{}}).sort(function(a,b){{return b[1]-a[1]}}).slice(0,15);
    chart.setOption({{
      tooltip: {{ trigger: 'axis' }},
      grid: {{ containLabel: true, left: 60, right: 20 }},
      xAxis: {{ type: 'value' }},
      yAxis: {{ type: 'category', data: entries.map(function(e){{return e[0]}}).reverse(), axisLabel: {{ fontSize: 11 }} }},
      series: [{{
        type: 'bar', data: entries.map(function(e){{return e[1]}}).reverse(),
        barWidth: 16,
        itemStyle: {{ color: new echarts.graphic.LinearGradient(0,0,1,0,[
          {{offset:0,color:'#7c3aed'}},{{offset:1,color:'#a78bfa'}}
        ]), borderRadius: [0,4,4,0] }}
      }}]
    }});
  }}

  function renderSchoolTable() {{
    var tbody = document.getElementById('schoolTableBody');
    if (!tbody) return;
    SCHOOL_DATA.forEach(function(d) {{
      var tr = document.createElement('tr');
      var typeLabel = d.type === '新增' ? '✅新增' : (d.type === '计划中' ? '⏳计划中' : '🏛️既有');
      tr.innerHTML = '<td>' + d.school + '</td><td>' + d.major + '</td><td>' + d.level + '</td><td>' + typeLabel + '</td><td>' + d.year + '</td><td>' + d.city + '</td><td>' + d.province + '</td>';
      tbody.appendChild(tr);
    }});
  }}

  function renderAllSchool() {{
    renderSchoolStats();
    renderSchoolLevelChart();
    renderSchoolMapChart();
    renderSchoolProvinceChart();
    renderSchoolTable();
  }}

  renderAllSchool();
"""

# Insert school JS before the last script block end or before loadAll
insert_marker = '  loadAll();'
if insert_marker in html:
    html = html.replace(insert_marker, school_js + '\n  loadAll();')
    print("✅ School JS inserted before loadAll()")
else:
    print("❌ Could not find loadAll() marker")
    exit(1)

# Write back
with open('dashboard/talent.html', 'w') as f:
    f.write(html)

# Also update root
with open('talent.html', 'w') as f:
    # Same content but adjust paths
    root_html = html.replace("fetch('talent_data.json'", "fetch('dashboard/talent_data.json'")
    root_html = root_html.replace("fetch('talent_stats.json'", "fetch('dashboard/talent_stats.json'")
    f.write(root_html)

# Verify
with open('dashboard/talent.html') as f:
    final = f.read()
assert 'SCHOOL_DATA' in final, "❌ SCHOOL_DATA not found in dashboard/talent.html"
assert 'SCHOOL_STATS' in final, "❌ SCHOOL_STATS not found"
assert 'renderAllSchool' in final, "❌ renderAllSchool not found"
assert 'schTotal' in final, "❌ schTotal element not found"

import os
print(f"\n✅ All checks passed!")
print(f"dashboard/talent.html: {os.path.getsize('dashboard/talent.html')} bytes")
print(f"talent.html: {os.path.getsize('talent.html')} bytes")
