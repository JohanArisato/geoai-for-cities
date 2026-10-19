"""Build a site preview with Part 3 added. Reads the live site (geoai-for-cities/index.html) and the
Part 3 draft; writes site_preview/index.html. Does not touch the repository."""
import re
from pathlib import Path
R = Path(__file__).resolve().parents[1]
site = Path('/home/claude/geoai-for-cities/index.html').read_text()
draft = (R/'part3-preview.html').read_text()
css = draft[draft.index('<style>')+7:draft.index('</style>')]
body = draft[draft.index('<main>')+6:draft.index('</main>')]
scripts = ''.join(re.findall(r'<script>.*?</script>', draft[draft.index('</main>'):], re.S))
kf = re.search(r'<h2 id="kf-h">Key findings</h2>\s*<ul>(.*?)</ul>', body, re.S).group(1)
secs = body[body.index('<section aria-labelledby="s1">'):]
secs = re.sub(r'<span class="num">(\d+)\.</span>', r'\1. ', secs)
secs = secs.replace('<h2 id="s10">Sources</h2>', '<h2 id="s10">Data and sources</h2>')
words = len(re.sub(r'<[^>]+>', ' ', re.sub(r'<svg.*?</svg>', ' ', secs, flags=re.S)).split())
mins = max(1, round(words / 230))
# scope draft CSS under .p3: keep only rules for Part 3 components; tokens from :root become .p3 tokens
tok = re.search(r':root\{(.*?)\}', css, re.S).group(1)
rules = css[css.index('*{box-sizing'):]
rules = re.sub(r'(^|\})\s*(body|main|section|h1,h2,h3|h1|h2|h3|p|a|a:focus-visible,button:focus-visible|\*)\{[^}]*\}', r'\1', rules)
def scope(block):
    out = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', block):
        sel, decl = m.group(1).strip(), m.group(2)
        if sel.startswith('@'): continue
        out.append(','.join('.p3 ' + x.strip() for x in sel.split(',')) + '{' + decl + '}')
    return '\n'.join(out)
medias = re.findall(r'(@media[^{]*)\{((?:[^{}]*\{[^{}]*\})*[^{}]*)\}', rules)
medias = [(q, b) for q, b in medias if 'prefers-color-scheme' not in q]
flat = re.sub(r'@media[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}', '', rules)
dark = re.search(r':root\[data-theme="dark"\]\{(.*?)\}', css, re.S).group(1)
p3css = '\n/* ---- Part 3 components (scoped) ---- */\n.p3{' + tok + '}\n' + scope(flat) + '\n' + ''.join(q + '{' + scope(b) + '}\n' for q, b in medias) + '.p3 .case p,.p3 .who span{margin:0}\n.p3 section{display:grid;gap:12px;margin:0}\n.p3 section h2{margin:20px 0 0 !important}\n'
view = f'''<div class="page post-page" id="part-3-view" hidden>
    <a class="back" href="#blog">Back to research</a>
    <article class="ps p3">
      <span class="bs-pill">Part 3 of 3, about a {mins}-minute read</span>
      <p class="ps-meta">GeoAI for Cities, Part 3. Original study, working paper (October 2026)</p>
      <h1 class="page-title">Record Heat, Record Demand: Can GeoAI Predict Where the Grid Strains?</h1>
      <p class="ps-dek">In September 2026, San Diego’s grid hit its highest demand on record. I used utility meter data for 3.9 million households in New York and San Diego to see where summer electricity use climbs, what explains it, and whether a model built in one place can predict another.</p>
      <p class="byline">By Jhoven (Johan) Fernandez. Builds on <a href="#part-2">Part 2: Who Gets the Shade?</a> <a href="https://github.com/JohanArisato/geoai-for-cities/tree/main/research/part3" target="_blank" rel="noopener">The code, data and a note on how each dataset was pulled are on GitHub</a>.</p>
      <section class="abstract" aria-label="Summary">
        <div class="abs-col bs-kf"><h2 class="abs-h">Key findings</h2><ul>{kf}</ul></div>
      </section>
      {secs}
      <nav class="bs-pn" aria-label="More in this series"><a href="#part-2"><small>Previous: Part 2</small><strong>Who Gets the Shade? Ranking New York Neighborhoods</strong></a><a class="bs-next" href="#research"><small>Companion notes</small><strong>Research notes: questions, methods and data</strong></a></nav>
    </article>
  {scripts}
  <aside class="bs-rail" aria-label="Series navigation"><div class="bs-box"><h4>In this series</h4><ol><li><a href="#part-1" class=""><span>01</span>What Is GeoAI? Definitions, Foundations and Five Verbs</a></li><li><a href="#part-2" class=""><span>02</span>Who Gets the Shade? Ranking New York Neighborhoods</a></li><li><a href="#part-3" class="on"><span>03</span>Record Heat, Record Demand</a></li><li><a href="#research"><span>+</span>Research notes</a></li></ol></div><nav class="bs-toc"><h4>On this page</h4><ol></ol></nav></aside></div>
  '''
s = site
# 1. view after part-2 view (before projects index)
anchor = '<div class="page pj-index" id="projects-view"'
s = s.replace(anchor, view + anchor, 1)
# 2. route
s = s.replace("PAGE_OF['part-2'] = 'part-2-view';", "PAGE_OF['part-2'] = 'part-2-view'; PAGE_OF['part-3'] = 'part-3-view';", 1)
# 3. rails in parts 1 and 2: add Part 3 entry
s = s.replace('<li><a href="#part-2" class="on"><span>02</span>Who Gets the Shade? Ranking New York Neighborhoods</a></li><li><a href="#research">',
              '<li><a href="#part-2" class="on"><span>02</span>Who Gets the Shade? Ranking New York Neighborhoods</a></li><li><a href="#part-3" class=""><span>03</span>Record Heat, Record Demand</a></li><li><a href="#research">')
s = s.replace('<li><a href="#part-2" class=""><span>02</span>Who Gets the Shade? Ranking New York Neighborhoods</a></li><li><a href="#research">',
              '<li><a href="#part-2" class=""><span>02</span>Who Gets the Shade? Ranking New York Neighborhoods</a></li><li><a href="#part-3" class=""><span>03</span>Record Heat, Record Demand</a></li><li><a href="#research">')
# 4. Part 2 next link -> Part 3
s = s.replace('<a href="#part-1"><small>Previous: Part 1</small><strong>What Is GeoAI? Definitions, Foundations and Five Verbs</strong></a><a class="bs-next" href="#research"><small>Companion notes</small><strong>Research notes: questions, methods and data</strong></a>',
              '<a href="#part-1"><small>Previous: Part 1</small><strong>What Is GeoAI? Definitions, Foundations and Five Verbs</strong></a><a class="bs-next" href="#part-3"><small>Next: Part 3</small><strong>Record Heat, Record Demand: Can GeoAI Predict Where the Grid Strains?</strong></a>')
# 5. series index entry + stats
item = '''<li class="bl-item">
          <a href="#part-3">
            <span class="bs-n" aria-hidden="true">03</span>
            <span class="bl-meta">Part 3, working paper, October 2026</span>
            <span class="bl-title">Record Heat, Record Demand: Can GeoAI Predict Where the Grid Strains?</span>
            <span class="bl-dek">Utility meter data for 3.9 million households in New York and San Diego, plus Phoenix, Chicago and Los Angeles. Where summer electricity demand climbs, what explains it, what it costs, and whether a model built in one place can predict another.</span>
            <span class="bl-topics">Original study, energy, prediction testing</span>
          </a>
        </li>
        '''
s = s.replace('<ol class="bl-list bs-num">\n        <li class="bl-item">\n          <a href="#part-2">', '<ol class="bl-list bs-num">\n        ' + item + '<li class="bl-item">\n          <a href="#part-2">', 1)
s = s.replace('<span><b>2</b> parts published</span><span><b>1</b> companion</span><span>Part 3 in preparation</span>', '<span><b>3</b> parts published</span><span><b>1</b> companion</span>')
s = s.replace('Part 1 of 2, about a 30-minute read', 'Part 1 of 3, about a 30-minute read').replace('Part 2 of 2, about a 9-minute read', 'Part 2 of 3, about a 9-minute read')
# 6. CSS into main stylesheet
t = s.find('<title>'); e = s.index('</style>', t if t >= 0 else 0); s = s[:e] + p3css + s[e:]
(R/'site_preview').mkdir(exist_ok=True); (R/'site_preview/index.html').write_text(s)
checks = {k: (k in s) for k in ["PAGE_OF['part-3']", 'id="part-3-view"', 'href="#part-3"', '<b>3</b> parts published', 'Next: Part 3', 'Part 2 of 3']}
print(checks, 'minutes', mins, 'rails with part-3:', s.count('<span>03</span>Record Heat'))
