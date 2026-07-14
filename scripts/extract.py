#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ppt-to-md 第一階段：機械式忠實抽取（不靠提示詞、不查外部、可重現）

用法:
    python extract.py <輸入.pptx> [輸出.md]

目標：盡量真實還原「簡報本身的內容」，不做任何論點考證或外部查證。

處理:
    1. 投影片本文：依 shape tree 順序抽取，保留閱讀順序、逐字不改寫
    2. 表格：還原 Markdown 表格，合併儲存格留白不填補
    3. 原生圖表：從 ppt/charts 抽出底層數據（類別/數列/數值），還原成數據表（無損）
       並標示原始圖型；散佈圖以 x/y 值成對還原；僅長條圖附 Mermaid 渲染
    4. SmartArt：逐字抽出圖形內文字（階層與版面未還原）；抽不到時明確標示
    5. 講者備註：依 rels 正確對應投影片；跨頁重複標為制式引註、唯一標為本頁專屬口述
    6. 圖片出處：抽出 deck 自標的出處字樣（如「Adapted from…」）逐字保留，僅標示不查證
    7. 雜訊：清掉純頁碼與 PowerPoint「Present Slide」介面殘留

設計原則：機械可驗證的才做；一切原文逐字；不猜、不填補、不查外部文獻。
"""
import sys, os, re, glob, zipfile, tempfile, shutil, posixpath, datetime
from xml.etree import ElementTree as ET

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
C = '{http://schemas.openxmlformats.org/drawingml/2006/chart}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
D = '{http://schemas.openxmlformats.org/drawingml/2006/diagram}'
def a(t): return f'{A}{t}'
def p_(t): return f'{P}{t}'
def c_(t): return f'{C}{t}'
def d_(t): return f'{D}{t}'
def _sn(path): return int(re.search(r'slide(\d+)\.xml', path).group(1))


def unpack(pptx_path):
    tmp = tempfile.mkdtemp(prefix='deckx_')
    with zipfile.ZipFile(pptx_path) as z:
        z.extractall(tmp)
    return tmp


# ---------- rels ----------
def load_rels(root_dir, n):
    """回傳 slideN 的 {rId: 絕對路徑}。"""
    relp = os.path.join(root_dir, f'ppt/slides/_rels/slide{n}.xml.rels')
    out = {}
    if os.path.exists(relp):
        for r in ET.parse(relp).getroot():
            rid = r.get('Id')
            tgt = r.get('Target', '')
            norm = posixpath.normpath(posixpath.join('ppt/slides', tgt))
            out[rid] = os.path.join(root_dir, norm)
    return out


def note_file_for(root_dir, n):
    relp = os.path.join(root_dir, f'ppt/slides/_rels/slide{n}.xml.rels')
    if os.path.exists(relp):
        for r in ET.parse(relp).getroot():
            if 'notesSlide' in r.get('Target', ''):
                return os.path.basename(r.get('Target'))
    return None


# ---------- notes ----------
def note_text(root_dir, fname):
    if not fname:
        return ''
    fp = os.path.join(root_dir, 'ppt', 'notesSlides', fname)
    if not os.path.exists(fp):
        return ''
    root = ET.parse(fp).getroot()
    paras = []
    for para in root.iter(a('p')):
        line = ''.join(t.text for t in para.iter(a('t')) if t.text).strip()
        if line:
            paras.append(line)
    txt = '\n'.join(paras).strip()
    txt = re.sub(r'^Present Slide\.?\s*', '', txt).strip()
    if re.fullmatch(r'\d{1,3}', txt):
        return ''
    txt = re.sub(r'\n\s*\d{1,3}\s*$', '', txt).strip()
    return txt


# ---------- tables ----------
def cell_text(tc):
    parts = []
    for para in tc.iter(a('p')):
        line = ''.join(t.text for t in para.iter(a('t')) if t.text).strip()
        if line:
            parts.append(line)
    return ' '.join(parts).strip()


def _md_table(grid, protected=None):
    """protected：與 grid 同形的布林格；True 的格子屬於原檔合併儲存格，
       其所在欄/列即使全空也保留（合併留白＝原檔結構，不是可丟棄的雜訊）。"""
    if not grid:
        return ''
    ncol = max(len(r) for r in grid)
    grid = [list(r) + [''] * (ncol - len(r)) for r in grid]
    if protected is None:
        protected = [[False] * ncol for _ in grid]
    else:
        protected = [list(r) + [False] * (ncol - len(r)) for r in protected]
    keep = [c for c in range(ncol)
            if any(str(grid[r][c]).strip() or protected[r][c] for r in range(len(grid)))]
    grid = [[r[c] for c in keep] for r in grid]
    protected = [[r[c] for c in keep] for r in protected]
    rows = [(g, m) for g, m in zip(grid, protected)
            if any(str(x).strip() for x in g) or any(m)]
    grid = [g for g, _ in rows]
    if not grid:
        return ''
    ncol = len(grid[0])
    esc = lambda s: (str(s) if s not in (None, '') else ' ').replace('|', '\\|').replace('\n', ' ')
    out = ['| ' + ' | '.join(esc(x) for x in grid[0]) + ' |',
           '| ' + ' | '.join(['---'] * ncol) + ' |']
    for row in grid[1:]:
        out.append('| ' + ' | '.join(esc(x) for x in row) + ' |')
    return '\n'.join(out)


def table_to_md(tbl):
    grid, merged = [], []
    for tr in tbl.iter(a('tr')):
        row, mrow = [], []
        for tc in tr.iter(a('tc')):
            row.append(cell_text(tc))
            mrow.append(bool(tc.get('gridSpan') or tc.get('rowSpan')
                             or tc.get('hMerge') or tc.get('vMerge')))
        grid.append(row)
        merged.append(mrow)
    return _md_table(grid, merged)


# ---------- native charts ----------
def _num(v):
    """清掉浮點雜訊：32.799999999999997 -> 32.8；非數字原樣回傳。"""
    if v is None:
        return ''
    try:
        return f'{float(v):g}'
    except (ValueError, TypeError):
        return v


def _cache_points(ref_el):
    pts = {}
    for pt in ref_el.iter(c_('pt')):
        idx = pt.get('idx')
        v = pt.find(c_('v'))
        if v is not None and idx is not None:
            pts[int(idx)] = v.text
    return pts


def _chart_to_mermaid(title, series, cats_master, idxs):
    """把原生圖表數據轉成 Obsidian 可渲染的 Mermaid xychart-beta 長條圖區塊。
       數據完全來自圖表底層（無 confabulation）；表格仍為 canonical，本區塊為附加渲染。"""
    import math
    cats = [str(cats_master.get(i, i)) for i in idxs]

    def qx(s):  # x-axis 標籤：去引號與方括號，加雙引號
        s = str(s).replace('"', "'").replace('[', ' ').replace(']', ' ').strip()
        return f'"{s}"'

    mx = 0.0
    arrays = []
    for nm, vals in series:
        arr = []
        for i in idxs:
            try:
                fv = float(vals.get(i))
            except (TypeError, ValueError):
                fv = 0.0
            arr.append(fv)
            mx = max(mx, fv)
        arrays.append(arr)
    ymax = math.ceil(mx * 1.15) if mx > 0 else 1

    t = (title or '').replace('"', "'").replace('\n', ' ').strip()
    lines = ['```mermaid', 'xychart-beta']
    if t:
        lines.append(f'    title "{t}"')
    lines.append('    x-axis [' + ', '.join(qx(c) for c in cats) + ']')
    lines.append(f'    y-axis 0 --> {ymax}')
    for arr in arrays:
        lines.append('    bar [' + ', '.join(f'{v:g}' for v in arr) + ']')
    lines.append('```')
    names = [nm if nm else f'數列{k+1}' for k, (nm, _) in enumerate(series)]
    caption = (f'（各長條數列對應上表欄位順序：{" / ".join(names)}；'
               f'xychart-beta 無圖例，數列對應與數值一切以上表為準）')
    return '\n'.join(lines) + '\n' + caption


CHART_KIND_ZH = {
    'barChart': '長條圖', 'bar3DChart': '立體長條圖',
    'lineChart': '折線圖', 'line3DChart': '立體折線圖',
    'pieChart': '圓餅圖', 'pie3DChart': '立體圓餅圖', 'doughnutChart': '環圈圖',
    'areaChart': '面積圖', 'area3DChart': '立體面積圖',
    'scatterChart': '散佈圖', 'bubbleChart': '泡泡圖',
    'radarChart': '雷達圖', 'stockChart': '股價圖', 'surfaceChart': '曲面圖',
}
_BAR_KINDS = ('barChart', 'bar3DChart')


def extract_chart_data(chart_path, emit_mermaid=True):
    """從 chartN.xml 抽底層數據，還原成 Markdown 數據表（無損），並標示原始圖型；
       散佈圖／泡泡圖（xVal/yVal）以 x 值當索引、y 值當數值成對還原；
       emit_mermaid=True 時「僅長條圖」附加 Mermaid xychart-beta（表格仍為 canonical；
       折線/圓餅等畫成長條會誤導趨勢，故不附）。"""
    if not os.path.exists(chart_path):
        return ''
    root = ET.parse(chart_path).getroot()
    title = ''
    t = root.find(f'.//{c_("title")}')
    if t is not None:
        title = ''.join(x.text for x in t.iter(a('t')) if x.text).strip()

    kinds = []
    plot = root.find(f'.//{c_("plotArea")}')
    if plot is not None:
        for el in plot:
            tag = el.tag.split('}')[-1]
            if tag.endswith('Chart') and tag not in kinds:
                kinds.append(tag)

    series = []
    cats_master = {}
    used_xy = False
    for ser in root.iter(c_('ser')):
        name = ''
        tx = ser.find(c_('tx'))
        if tx is not None:
            name = ''.join(x.text for x in tx.iter(c_('v')) if x.text).strip()
        cat_el = ser.find(c_('cat'))
        val_el = ser.find(c_('val'))
        if val_el is None and ser.find(c_('yVal')) is not None:
            cat_el = ser.find(c_('xVal'))
            val_el = ser.find(c_('yVal'))
            used_xy = True
        cats = _cache_points(cat_el) if cat_el is not None else {}
        vals = _cache_points(val_el) if val_el is not None else {}
        for k, v in cats.items():
            cats_master.setdefault(k, v)
        series.append((name, vals))

    if not series:
        return ''
    idxs = sorted(cats_master.keys()) if cats_master else \
        sorted({i for _, v in series for i in v.keys()})

    headers = ['X值' if used_xy else '類別']
    for i, (nm, _) in enumerate(series, 1):
        headers.append(nm if nm else f'數列{i}')
    grid = [headers]
    for idx in idxs:
        cat = cats_master.get(idx, str(idx))
        row = [_num(cat) if used_xy else cat]
        for _, vals in series:
            row.append(_num(vals.get(idx, '')))
        grid.append(row)

    md = _md_table(grid)
    if not md:
        return ''
    kind_zh = '、'.join(CHART_KIND_ZH.get(k, k) for k in kinds)
    label = ('**[原生圖表數據' + (f'（{kind_zh}）' if kind_zh else '')
             + (f'：{title}' if title else '') + ']**')
    out = label + '\n\n' + md
    if emit_mermaid and any(k in _BAR_KINDS for k in kinds):
        out += '\n\n' + _chart_to_mermaid(title, series, cats_master, idxs)
    return out


# ---------- SmartArt (diagram) ----------
def extract_diagram_text(data_path):
    """從 SmartArt 的 ppt/diagrams/data*.xml 逐字抽出文字節點（依檔內順序）。
       只取文字，不還原階層與版面關係；抽不到回傳 None（由呼叫端明確標示，不靜默遺失）。"""
    if not data_path or not os.path.exists(data_path):
        return None
    try:
        root = ET.parse(data_path).getroot()
    except ET.ParseError:
        return None
    lines = []
    for pt in root.iter(d_('pt')):
        if pt.get('type') in ('parTrans', 'sibTrans'):  # 轉場節點＝模板殘留，非內容
            continue
        t_el = pt.find(d_('t'))
        if t_el is None:
            continue
        for para in t_el.iter(a('p')):
            line = ''.join(t.text for t in para.iter(a('t')) if t.text).strip()
            if line:
                lines.append(line)
    return lines or None


# ---------- provenance labels (抽取，不查證) ----------
PROVENANCE_PATTERNS = [
    r'adapted from[^\n]*',
    r'modified from[^\n]*',
    r'reproduced[^\n]*from[^\n]*',
    r'image[^\n]*(?:from|permission)[^\n]*',
    r'source\s*[:：][^\n]*',
    r'\(figure\s*\d+[^\)]*\)',
    r'\bfig(?:ure)?\.?\s*\d+\b[^\n]{0,150}',
]
_PROV_RE = re.compile('|'.join(PROVENANCE_PATTERNS), re.IGNORECASE)


def find_provenance(blocks, note):
    hits = []
    haystack = '\n'.join(c for _, c in blocks)
    if note:
        haystack += '\n' + note
    for m in _PROV_RE.finditer(haystack):
        s = m.group(0).strip()
        gran = 'figure' if re.search(r'fig', s, re.IGNORECASE) else 'paper'
        hits.append((gran, s))
    seen, out = set(), []
    for g, s in hits:
        if s not in seen:
            seen.add(s); out.append((g, s))
    return out


# ---------- body noise cleaning ----------
_PURENUM = re.compile(r'^-?\d{1,4}(\.\d+)?%?$')


def _is_axis_like(run):
    """判斷純數字串是否為座標軸刻度：需含一段 ≥5 個「等距」數值（等差級數）——
       這是刻度尺的特徵。散落、不等距的數據值（如 58.5/53.4/18.9/26.4）不會被誤判。"""
    vals = []
    for s in run:
        try:
            vals.append(float(str(s).replace('%', '').replace(',', '')))
        except ValueError:
            return False
    uniq = sorted(set(vals))
    if len(uniq) < 5:
        return False
    diffs = [round(uniq[k + 1] - uniq[k], 6) for k in range(len(uniq) - 1)]
    best = cur = 1
    for k in range(1, len(diffs)):
        if abs(diffs[k] - diffs[k - 1]) < 1e-6:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best >= 4   # ≥4 個相同差 ⇒ ≥5 個等距值


def clean_body_blocks(blocks, slide_num):
    """本文層雜訊清理（只動 text 塊，不碰 table/chart 內容）：
       (a) 折疊「座標軸刻度」串——需為等距刻度尺（見 _is_axis_like），避免誤傷散落數據；
       (b) 刪掉整塊只是該頁頁碼的文字塊。
       回傳 (cleaned, n_axis_collapsed, n_pagenum_dropped)。"""
    # (a) 折疊座標軸刻度串
    step1, i, n_axis = [], 0, 0
    while i < len(blocks):
        kind, content = blocks[i]
        if kind == 'text' and _PURENUM.match(content.strip()):
            j, run = i, []
            while j < len(blocks) and blocks[j][0] == 'text' and _PURENUM.match(blocks[j][1].strip()):
                run.append(blocks[j][1].strip()); j += 1
            if len(run) >= 5 and _is_axis_like(run):
                step1.append(('axis', f'〔圖表座標軸刻度：{", ".join(run)}〕'))
                n_axis += 1
            else:
                step1.extend(blocks[i:j])
            i = j
        else:
            step1.append((kind, content)); i += 1
    # (b) 剝除等於頁碼的孤立數字塊
    cleaned, n_page = [], 0
    for kind, content in step1:
        if kind == 'text' and content.strip() == str(slide_num):
            n_page += 1; continue
        cleaned.append((kind, content))
    return cleaned, n_axis, n_page


# ---------- slide walk ----------
def _para_line_and_size(para):
    """回傳 (段落文字, 該段最大字級pt)。字級取自 run 的 rPr@sz（單位 1/100 pt）。"""
    texts, max_sz = [], 0
    for r in para.iter(a('r')):
        t = r.find(a('t'))
        if t is None or not t.text:
            continue
        texts.append(t.text)
        rpr = r.find(a('rPr'))
        if rpr is not None and rpr.get('sz'):
            try:
                max_sz = max(max_sz, int(rpr.get('sz')) // 100)
            except ValueError:
                pass
    line = ''.join(texts).strip()
    if not line:  # 後備：run 以外的 a:t
        line = ''.join(t.text for t in para.iter(a('t')) if t.text).strip()
    return line, max_sz


def extract_slide(path, rels, emit_mermaid=True):
    """依 shape tree 順序回傳 [(kind, content)]，kind ∈ {'text','table','chart'}。
       字級明顯大於該頁內文者標為粗體（保留原檔視覺強調層次；純機械，不做語意判斷）。"""
    root = ET.parse(path).getroot()
    spTree = root.find(f'.//{p_("cSld")}/{p_("spTree")}')
    blocks = []

    # 先算全頁字級中位數，據以定強調門檻
    all_sz = []
    for r in (spTree.iter(a('r')) if spTree is not None else []):
        t = r.find(a('t')); rpr = r.find(a('rPr'))
        if t is not None and t.text and t.text.strip() and rpr is not None and rpr.get('sz'):
            try:
                all_sz.append(int(rpr.get('sz')) // 100)
            except ValueError:
                pass
    body_sz = sorted(all_sz)[len(all_sz) // 2] if all_sz else 18
    emph_thr = max(24, body_sz * 1.6)   # 保守：需同時 ≥24pt 且 ≥1.6×內文

    def emph(line, size):
        return f'**{line}**' if line and size and size >= emph_thr else line

    def paras_from(tf, use_runs=True):
        out = []
        for para in tf.iter(a('p')):
            if use_runs:
                line, size = _para_line_and_size(para)
            else:
                line = ''.join(t.text for t in para.iter(a('t')) if t.text).strip()
                size = 0
            if line:
                out.append(emph(line, size))
        return out

    def walk(el):
        if el is None:
            return
        for child in el:
            tag = child.tag.split('}')[-1]
            if tag == 'sp':
                tf = child.find(p_('txBody'))
                if tf is None:
                    tf = child.find(a('txBody'))
                if tf is not None:
                    paras = paras_from(tf)
                    if paras:
                        blocks.append(('text', '\n'.join(paras)))
            elif tag == 'graphicFrame':
                tbl = child.find(f'.//{a("tbl")}')
                chart_ref = child.find(f'.//{c_("chart")}')
                dgm_rel = child.find(f'.//{d_("relIds")}')
                if tbl is not None:
                    md = table_to_md(tbl)
                    if md:
                        blocks.append(('table', md))
                elif chart_ref is not None:
                    rid = chart_ref.get(f'{R}id')
                    cpath = rels.get(rid)
                    if cpath:
                        md = extract_chart_data(cpath, emit_mermaid)
                        if md:
                            blocks.append(('chart', md))
                elif dgm_rel is not None:
                    dm = dgm_rel.get(f'{R}dm')
                    lines = extract_diagram_text(rels.get(dm)) if dm else None
                    if lines:
                        body = '\n'.join(f'- {ln}' for ln in lines)
                        blocks.append(('smartart',
                            '**[SmartArt 圖形文字（逐字抽取；階層與版面關係未還原，請回看原圖確認）]**\n\n' + body))
                    else:
                        blocks.append(('smartart',
                            '_（此處有 SmartArt 圖形，文字無法抽取，請回看原檔）_'))
                else:
                    paras = paras_from(child)
                    if paras:
                        blocks.append(('text', '\n'.join(paras)))
            elif tag == 'grpSp':
                walk(child)
    walk(spTree)
    return blocks


# ---------- assemble ----------
def convert(pptx_path, out_path=None, emit_mermaid=True, frontmatter=False):
    root_dir = unpack(pptx_path)
    try:
        base = os.path.splitext(os.path.basename(pptx_path))[0]
        if out_path is None:
            out_path = os.path.join(os.path.dirname(os.path.abspath(pptx_path)), base + '.md')

        notes_map = {}
        for s in sorted(glob.glob(os.path.join(root_dir, 'ppt/slides/slide*.xml')), key=_sn):
            n = _sn(s)
            notes_map[n] = note_file_for(root_dir, n)
        norm = {}
        for n, f in notes_map.items():
            t = note_text(root_dir, f)
            if t:
                norm.setdefault(t.strip(), []).append(n)
        boiler = {k for k, v in norm.items() if len(v) > 1}
        boiler_first = {k: min(v) for k, v in norm.items() if len(v) > 1}

        head = []
        if frontmatter:
            today = datetime.date.today().isoformat()
            # 語意欄位（type/domain/stage/aliases）留白供下游流程補填；date/source 機械預填
            head = ['---', 'type: ', 'domain: ', 'stage: ', 'aliases: ',
                    f'date: {today}', f'source: "{base}.pptx"', '---', '']
        out = head + [f'# {base}', '',
               '> 來源：學術簡報（.pptx）第一階段機械抽取。目標為忠實還原簡報內容，未做任何論點考證或外部查證。',
               '> 本文與備註逐字保留、未改寫。表格與原生圖表以原始結構還原；表格空白格＝原檔合併儲存格，未填補。',
               '> 「原生圖表數據」為從圖表底層無損取出的類別/數值；貼上的點陣圖（截圖式分析圖）無法讀數，僅保留其周邊文字與出處字樣。',
               '> 備註分兩類：「本頁專屬口述論點」＝講者對該頁的口述；「制式引註」＝跨頁重複的模板殘留。',
               '> ⚠️ 線性順序來自版面座標，不等於講者口說順序；並列/對照的視覺區塊會被攤平，閱讀時需回看原圖。',
               '> 雜訊處理：孤立的頁碼數字已剝除；圖表座標軸刻度（僅限等距刻度尺）折疊為一行摘要，散落數據值保留；跨頁重複的制式引註全文只顯示一次，後續頁指回首次出現處。',
               '> **粗體**＝原檔以明顯大字級強調的文字（保留視覺重點層次；依字級機械判定，非語意判斷）。',
               '> 原生圖表以數據表還原並標示原始圖型（長條/折線/圓餅/散佈…）；僅長條圖另附 Mermaid xychart-beta（Obsidian 1.4+ 可直接渲染，無需圖檔）；表格為準，圖為附加渲染。',
               '> SmartArt 圖形內的文字逐字抽出（階層與版面關係未還原）；無法抽取時明確標示，不靜默遺失。',
               '', '---', '']

        slides = sorted(glob.glob(os.path.join(root_dir, 'ppt/slides/slide*.xml')), key=_sn)
        n_tables = n_charts = n_speaker = n_boiler = n_prov = 0
        n_axis = n_pagenum = n_smartart = 0
        for s in slides:
            n = _sn(s)
            rels = load_rels(root_dir, n)
            blocks = extract_slide(s, rels, emit_mermaid)
            blocks, na, npg = clean_body_blocks(blocks, n)
            n_axis += na
            n_pagenum += npg
            out.append(f'## 投影片 {n}\n')
            if not blocks:
                out.append('_（此頁無可擷取文字，可能為純圖像）_\n')
            for kind, content in blocks:
                if kind == 'table':
                    n_tables += 1
                elif kind == 'chart':
                    n_charts += 1
                elif kind == 'smartart':
                    n_smartart += 1
                out.append(content + '\n')

            nt = note_text(root_dir, notes_map.get(n))
            prov = find_provenance(blocks, nt)
            if prov:
                n_prov += 1
                out.append('> **圖片出處字樣（deck 自標，逐字，未查證）：**')
                for gran, txt in prov:
                    tag = '含圖號' if gran == 'figure' else '論文層'
                    out.append(f'> - 〔{tag}〕{txt}')
                out.append('')
            if nt:
                key = nt.strip()
                if key in boiler:
                    n_boiler += 1
                    first = boiler_first[key]
                    if n == first:
                        out.append('> **〔備註欄・跨頁重複的制式引註（全文首次出現，後續頁指回此處）〕**')
                        for line in nt.splitlines():
                            out.append('> ' + line if line.strip() else '>')
                        out.append('')
                    else:
                        out.append(f'> **〔備註欄・制式引註，內容同投影片 {first}，此處略〕**')
                        out.append('')
                else:
                    n_speaker += 1
                    out.append('> **講者備註（本頁專屬口述論點）：**')
                    for line in nt.splitlines():
                        out.append('> ' + line if line.strip() else '>')
                    out.append('')
            out.append('---\n')

        md = '\n'.join(out)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)

        print(f'[ppt-to-md] 完成：{out_path}')
        smart = f' ｜ SmartArt {n_smartart} 處' if n_smartart else ''
        print(f'  投影片 {len(slides)} 頁 ｜ 表格 {n_tables} 張 ｜ 原生圖表 {n_charts} 張{smart} ｜ '
              f'本頁專屬口述 {n_speaker} 則 ｜ 制式引註 {n_boiler} 則 ｜ 圖片出處字樣 {n_prov} 頁')
        print(f'  雜訊清理：折疊座標軸刻度 {n_axis} 處 ｜ 剝除頁碼 {n_pagenum} 處')
        return out_path
    finally:
        shutil.rmtree(root_dir, ignore_errors=True)


if __name__ == '__main__':
    args = [x for x in sys.argv[1:]]
    emit_mermaid = True
    frontmatter = False
    if '--no-mermaid' in args:
        emit_mermaid = False
        args = [x for x in args if x != '--no-mermaid']
    if '--frontmatter' in args:
        frontmatter = True
        args = [x for x in args if x != '--frontmatter']
    if len(args) < 1:
        print('用法: python extract.py <輸入.pptx> [輸出.md] [--no-mermaid] [--frontmatter]')
        sys.exit(1)
    inp = args[0]
    outp = args[1] if len(args) > 1 else None
    if not inp.lower().endswith('.pptx'):
        print('注意：僅支援 .pptx。舊版 .ppt 請先轉檔：')
        print('  soffice --headless --convert-to pptx 你的檔案.ppt')
    convert(inp, outp, emit_mermaid=emit_mermaid, frontmatter=frontmatter)
