# -*- coding: utf-8 -*-
"""測試用 fixture 產生器：以最小 OOXML 片段程式化組出 .pptx。

extract.py 只讀取 ppt/slides/、ppt/notesSlides/、ppt/charts/、ppt/diagrams/
四類部件，因此 fixture 不需要完整的簡報封裝（presentation.xml 等），
保持產生器小而可讀。
"""
import zipfile

NS_A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS_C = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
NS_R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS_DGM = 'http://schemas.openxmlformats.org/drawingml/2006/diagram'
NS_PKG_REL = 'http://schemas.openxmlformats.org/package/2006/relationships'

REL_NOTES = ('http://schemas.openxmlformats.org/officeDocument/2006/'
             'relationships/notesSlide')
REL_CHART = ('http://schemas.openxmlformats.org/officeDocument/2006/'
             'relationships/chart')
REL_DIAGRAM_DATA = ('http://schemas.openxmlformats.org/officeDocument/2006/'
                    'relationships/diagramData')


# ---------- slide 內容片段 ----------
def text_sp(lines):
    """文字 shape。lines: list of str 或 (str, 字級pt)。"""
    paras = []
    for item in lines:
        text, sz = item if isinstance(item, tuple) else (item, None)
        rpr = f'<a:rPr lang="en-US" sz="{sz * 100}"/>' if sz else ''
        paras.append(f'<a:p><a:r>{rpr}<a:t>{text}</a:t></a:r></a:p>')
    return f'<p:sp><p:txBody><a:bodyPr/>{"".join(paras)}</p:txBody></p:sp>'


def _table_cell(spec):
    """spec: str，或 dict{text, gridSpan, rowSpan, hMerge, vMerge}。"""
    if isinstance(spec, str):
        spec = {'text': spec}
    attrs = ''.join(f' {k}="{spec[k]}"'
                    for k in ('gridSpan', 'rowSpan', 'hMerge', 'vMerge')
                    if spec.get(k))
    text = spec.get('text', '')
    para = f'<a:p><a:r><a:t>{text}</a:t></a:r></a:p>' if text else '<a:p/>'
    return f'<a:tc{attrs}><a:txBody><a:bodyPr/>{para}</a:txBody></a:tc>'


def table_frame(rows):
    trs = ''.join('<a:tr h="370840">' + ''.join(_table_cell(c) for c in row)
                  + '</a:tr>' for row in rows)
    return ('<p:graphicFrame><a:graphic>'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
            f'<a:tbl>{trs}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>')


def chart_frame(rid):
    return ('<p:graphicFrame><a:graphic>'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">'
            f'<c:chart r:id="{rid}"/></a:graphicData></a:graphic></p:graphicFrame>')


def diagram_frame(rid):
    return ('<p:graphicFrame><a:graphic>'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/diagram">'
            f'<dgm:relIds r:dm="{rid}" r:lo="" r:qs="" r:cs=""/>'
            '</a:graphicData></a:graphic></p:graphicFrame>')


# ---------- 部件 XML ----------
def slide_xml(body):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:sld xmlns:p="{NS_P}" xmlns:a="{NS_A}" xmlns:r="{NS_R}"'
            f' xmlns:c="{NS_C}" xmlns:dgm="{NS_DGM}">'
            f'<p:cSld><p:spTree>{body}</p:spTree></p:cSld></p:sld>')


def notes_xml(lines):
    paras = ''.join(f'<a:p><a:r><a:t>{t}</a:t></a:r></a:p>' for t in lines)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:notes xmlns:p="{NS_P}" xmlns:a="{NS_A}">'
            f'<p:cSld><p:spTree><p:sp><p:txBody><a:bodyPr/>{paras}'
            '</p:txBody></p:sp></p:spTree></p:cSld></p:notes>')


def rels_xml(entries):
    rels = ''.join(f'<Relationship Id="{rid}" Type="{typ}" Target="{tgt}"/>'
                   for rid, typ, tgt in entries)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{NS_PKG_REL}">{rels}</Relationships>')


def _pts(values):
    return ''.join(f'<c:pt idx="{i}"><c:v>{v}</c:v></c:pt>'
                   for i, v in enumerate(values))


def chart_xml(title, cats, series, kind='barChart', xy=False):
    """series: list of (數列名, 值列表)。xy=True 用 xVal/yVal（散佈圖）。"""
    sers = []
    for name, vals in series:
        tx = (f'<c:tx><c:strRef><c:strCache><c:pt idx="0"><c:v>{name}</c:v>'
              '</c:pt></c:strCache></c:strRef></c:tx>') if name else ''
        if xy:
            data = (f'<c:xVal><c:numRef><c:numCache>{_pts(cats)}</c:numCache>'
                    '</c:numRef></c:xVal>'
                    f'<c:yVal><c:numRef><c:numCache>{_pts(vals)}</c:numCache>'
                    '</c:numRef></c:yVal>')
        else:
            data = (f'<c:cat><c:strRef><c:strCache>{_pts(cats)}</c:strCache>'
                    '</c:strRef></c:cat>'
                    f'<c:val><c:numRef><c:numCache>{_pts(vals)}</c:numCache>'
                    '</c:numRef></c:val>')
        sers.append(f'<c:ser>{tx}{data}</c:ser>')
    title_xml = (f'<c:title><c:tx><c:rich><a:p><a:r><a:t>{title}</a:t></a:r>'
                 '</a:p></c:rich></c:tx></c:title>') if title else ''
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<c:chartSpace xmlns:c="{NS_C}" xmlns:a="{NS_A}" xmlns:r="{NS_R}">'
            f'<c:chart>{title_xml}<c:plotArea><c:layout/>'
            f'<c:{kind}>{"".join(sers)}</c:{kind}>'
            '</c:plotArea></c:chart></c:chartSpace>')


def diagram_data_xml(texts, with_transition_noise=True):
    """SmartArt data model。with_transition_noise 時混入 parTrans 節點驗證過濾。"""
    pts = ''.join(
        f'<dgm:pt modelId="{{0000000{i}}}"><dgm:t><a:bodyPr/>'
        f'<a:p><a:r><a:t>{t}</a:t></a:r></a:p></dgm:t></dgm:pt>'
        for i, t in enumerate(texts))
    if with_transition_noise:
        pts += ('<dgm:pt modelId="{99999999}" type="parTrans"><dgm:t>'
                '<a:p><a:r><a:t>TRANSITION_NOISE</a:t></a:r></a:p>'
                '</dgm:t></dgm:pt>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<dgm:dataModel xmlns:dgm="{NS_DGM}" xmlns:a="{NS_A}">'
            f'<dgm:ptLst>{pts}</dgm:ptLst></dgm:dataModel>')


# ---------- 打包 ----------
def build_pptx(path, slides, extra_files=None):
    """slides: list of dict：
       body   : spTree 內容 xml（用上面的片段函式組）
       rels   : list of (rId, Type, Target)，選用
       notes  : list of str → 自動產生 notesSlideN.xml 並掛 rels，選用
       charts / diagrams : {檔名: xml} → 寫進 ppt/charts/、ppt/diagrams/，選用
       extra_files: {zip 內路徑: 內容} 任意額外部件。"""
    with zipfile.ZipFile(path, 'w') as z:
        for i, sl in enumerate(slides, 1):
            z.writestr(f'ppt/slides/slide{i}.xml', slide_xml(sl.get('body', '')))
            rels = list(sl.get('rels', []))
            if 'notes' in sl:
                z.writestr(f'ppt/notesSlides/notesSlide{i}.xml',
                           notes_xml(sl['notes']))
                rels.append((f'rIdNotes{i}', REL_NOTES,
                             f'../notesSlides/notesSlide{i}.xml'))
            if rels:
                z.writestr(f'ppt/slides/_rels/slide{i}.xml.rels', rels_xml(rels))
            for name, xml in sl.get('charts', {}).items():
                z.writestr(f'ppt/charts/{name}', xml)
            for name, xml in sl.get('diagrams', {}).items():
                z.writestr(f'ppt/diagrams/{name}', xml)
        for arc, content in (extra_files or {}).items():
            z.writestr(arc, content)
