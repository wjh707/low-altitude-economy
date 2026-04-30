#!/usr/bin/env python3
"""Insert school/major section into talent.html and embed data."""
import json

# Read existing talent.html
with open('dashboard/talent.html') as f:
    html = f.read()

# Read school data and stats
with open('data/school_majors.json') as f:
    school_data = json.load(f)

with open('dashboard/school_stats.json') as f:
    school_stats = json.load(f)

# Convert to JS constant strings
school_data_js = json.dumps(school_data, ensure_ascii=False)
school_stats_js = json.dumps(school_stats, ensure_ascii=False)

# School section HTML - insert between main container end and footer
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
      <h3>🏫 本科层次布局（首批6所双一流）</h3>
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
          </tr>
        </thead>
        <tbody id="schoolTableBody"></tbody>
      </table>
    </div>
  </div>
</div>
<style>
  .stat-card.school { border-left-color: #7c3aed; }
  .stat-card.school .value { color: #7c3aed; }
</style>
"""

# Insert before footer
html = html.replace('<div class="footer">', school_section + '<div class="footer">')

# Insert school data into JS
js_insert = f"""
  // === 高校专业数据 ===
  const SCHOOL_DATA = {school_data_js};
  const SCHOOL_STATS = {school_stats_js};

  function renderSchoolStats(stats) {{
    document.getElementById('schTotal').textContent = stats.total_schools || '-';
    document.getElementById('schUndergrad').textContent = (stats.by_level && stats.by_level['本科']) || '-';
    document.getElementById('schGrad').textContent = (stats.by_level && stats.by_level['研究生']) || '-';
    document.getElementById('schVocation').textContent = (stats.by_level && stats.by_level['高职']) || '-';
  }}

  function renderSchoolLevelChart(data, stats) {{
    const chart = echarts.init(document.getElementById('chartSchoolLevel'));
    const byLevel = stats.by_level || {{}};
    const levels = ['本科', '研究生', '高职', '本科/研究生'];
    const colors = ['#1a73e8', '#34a853', '#fbbc04', '#ea4335'];
    chart.setOption({{
      tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}}所 ({{d}}%)' }},
      series: [{{
        type: 'pie', radius: ['40%', '70%'], center: ['50%', '55%'],
        label: {{ formatter: '{{b}}\\n{{c}}所', fontSize: 12 }},
        data: levels.filter(l => byLevel[l]).map((l, i) => ({{ value: byLevel[l], name: l, itemStyle: {{ color: colors[i] }} }}))
      }}]
    }});
  }}

  function renderSchoolMapChart(data) {{
    const chart = echarts.init(document.getElementById('chartSchoolMap'));
    const undergrad = data.filter(d => d.level === '本科' && d.type !== '计划中');
    chart.setOption({{
      tooltip: {{ trigger: 'item' }},
      grid: {{ containLabel: true, left: 20, right: 20, bottom: 20, top: 10 }},
      xAxis: {{ type: 'value', show: false }},
      yAxis: {{ type: 'category', data: undergrad.map(d => d.school.replace(/(大学|学院)$/,'')).reverse(), axisLabel: {{ fontSize: 11 }} }},
      series: [{{
        type: 'bar', data: undergrad.map(() => 1).reverse(),
        barWidth: 18,
        itemStyle: {{
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {{ offset: 0, color: '#1a73e8' }}, {{ offset: 1, color: '#6ab7ff' }}
          ]),
          borderRadius: [0, 4, 4, 0]
        }},
        label: {{ show: true, position: 'right', formatter: function(p) {{
          const d = undergrad[undergrad.length - 1 - p.dataIndex];
          return d.major;
        }}, fontSize: 10, color: '#333' }}
      }}]
    }});
  }}

  function renderSchoolProvinceChart(stats) {{
    const chart = echarts.init(document.getElementById('chartSchoolProvince'));
    const byProvince = stats.by_province || {{}};
    const entries = Object.entries(byProvince).sort((a,b) => b[1]-a[1]).slice(0, 15);
    chart.setOption({{
      tooltip: {{ trigger: 'axis' }},
      grid: {{ containLabel: true, left: 60, right: 20 }},
      xAxis: {{ type: 'value' }},
      yAxis: {{ type: 'category', data: entries.map(e => e[0]).reverse(), axisLabel: {{ fontSize: 11 }} }},
      series: [{{
        type: 'bar', data: entries.map(e => e[1]).reverse(),
        barWidth: 16,
        itemStyle: {{
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {{ offset: 0, color: '#7c3aed' }}, {{ offset: 1, color: '#a78bfa' }}
          ]),
          borderRadius: [0, 4, 4, 0]
        }}
      }}]
    }});
  }}

  function renderSchoolTable(data) {{
    const tbody = document.getElementById('schoolTableBody');
    data.forEach(d => {{
      const tr = document.createElement('tr');
      const typeLabel = d.type === '新增' ? '✅新增' : (d.type === '计划中' ? '⏳计划中' : '🏛️既有');
      tr.innerHTML = `<td>${{d.school}}</td><td>${{d.major}}</td><td>${{d.level}}</td><td>${{typeLabel}}</td><td>${{d.year}}</td><td>${{d.city}}</td>`;
      tbody.appendChild(tr);
    }});
  }}

  // School rendering in loadAll
  const origInit = loadAll;
  loadAll = function() {{
    origInit();
    // Will be called after stats loaded
  }};
"""

# Find where to insert school JS - after the last render function and before loadAll()
# Let's find the loadAll() call line
insert_point = "// ---- Start ----\n  loadAll();"
js_insert_block = f"""
  // ---- 高校专业渲染 ----
  function renderAllSchool() {{
    if (!SCHOOL_DATA || !SCHOOL_STATS) return;
    renderSchoolStats(SCHOOL_STATS);
    renderSchoolLevelChart(SCHOOL_DATA, SCHOOL_STATS);
    renderSchoolMapChart(SCHOOL_DATA);
    renderSchoolProvinceChart(SCHOOL_STATS);
    renderSchoolTable(SCHOOL_DATA);
  }}

  renderAllSchool();
"""

html = html.replace(insert_point, js_insert_block + insert_point)

with open('dashboard/talent.html', 'w') as f:
    f.write(html)

# Also update root talent.html
with open('talent.html', 'w') as f:
    f.write(html)

assert 'SCHOOL_DATA' in html, "School data not embedded!"
assert 'SCHOOL_STATS' in html, "School stats not embedded!"

print("✅ 高校专业板块已集成到人才看板")
