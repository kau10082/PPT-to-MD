# -*- coding: utf-8 -*-
"""extract.py 端到端與單元測試（僅標準庫，python -m unittest discover -s tests）。

每個測試都對應一條「忠實還原」的行為承諾：改壞任何一條保真規則，
這裡就會亮紅燈。fixture 由 fixtures.py 程式化產生，不依賴外部檔案。
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'scripts'))
import extract  # noqa: E402

from fixtures import (  # noqa: E402
    REL_CHART, REL_DIAGRAM_DATA, REL_NOTES,
    build_pptx, chart_frame, chart_xml, diagram_data_xml, diagram_frame,
    notes_xml, table_frame, text_sp,
)


class ConvertTestCase(unittest.TestCase):
    """共用：組 pptx → convert → 回傳 markdown 全文。"""

    def _convert(self, slides, extra_files=None, **kwargs):
        tmp = tempfile.mkdtemp(prefix='ppt2md_test_')
        self.addCleanup(shutil.rmtree, tmp, True)
        pptx = os.path.join(tmp, 'deck.pptx')
        build_pptx(pptx, slides, extra_files)
        out = os.path.join(tmp, 'deck.md')
        with contextlib.redirect_stdout(io.StringIO()):
            extract.convert(pptx, out, **kwargs)
        with open(out, encoding='utf-8') as f:
            return f.read()


class BodyTextTests(ConvertTestCase):

    def test_text_extracted_verbatim_in_order(self):
        md = self._convert([{'body': text_sp(['第一段文字']) + text_sp(['第二段文字'])}])
        self.assertIn('第一段文字', md)
        self.assertIn('第二段文字', md)
        self.assertLess(md.index('第一段文字'), md.index('第二段文字'))

    def test_empty_slide_marked_explicitly(self):
        md = self._convert([{'body': ''}])
        self.assertIn('此頁無可擷取文字', md)

    def test_large_font_marked_bold(self):
        body = text_sp([('大標題強調', 40), ('一般內文一', 18), ('一般內文二', 18)])
        md = self._convert([{'body': body}])
        self.assertIn('**大標題強調**', md)
        self.assertIn('一般內文一', md)
        self.assertNotIn('**一般內文一**', md)

    def test_page_number_block_stripped(self):
        md = self._convert([{'body': text_sp(['真正的內容']) + text_sp(['1'])}])
        self.assertIn('真正的內容', md)
        self.assertNotIn('\n1\n', md)

    def test_axis_ticks_collapsed_only_when_equidistant(self):
        ticks = ''.join(text_sp([t]) for t in ['0', '10', '20', '30', '40'])
        md = self._convert([{'body': ticks}])
        self.assertIn('〔圖表座標軸刻度：0, 10, 20, 30, 40〕', md)

    def test_scattered_data_values_not_collapsed(self):
        vals = ['58.5', '53.4', '18.9', '26.4', '7.2']
        md = self._convert([{'body': ''.join(text_sp([v]) for v in vals)}])
        self.assertNotIn('〔圖表座標軸刻度', md)  # 檔頭說明含此詞，檢查折疊標記本身
        for v in vals:
            self.assertIn(v, md)


class TableTests(ConvertTestCase):

    def test_merged_cell_blank_column_preserved(self):
        # 兩列都是「gridSpan=2 + hMerge 接續格」：第 2 欄全空，
        # 但那是原檔合併結構，欄位必須保留、留白不填補。
        rows = [
            [{'text': '合併標題', 'gridSpan': '2'}, {'hMerge': '1'}, 'C欄'],
            [{'text': '甲', 'gridSpan': '2'}, {'hMerge': '1'}, '數值'],
        ]
        md = self._convert([{'body': table_frame(rows)}])
        self.assertIn('| 合併標題 |   | C欄 |', md)
        self.assertIn('| 甲 |   | 數值 |', md)

    def test_truly_empty_unmerged_column_dropped(self):
        rows = [['A', '', 'B'], ['1', '', '2']]
        md = self._convert([{'body': table_frame(rows)}])
        self.assertIn('| A | B |', md)
        self.assertIn('| 1 | 2 |', md)

    def test_table_structure_roundtrip(self):
        rows = [['指標', '組別A', '組別B'], ['ORR', '58.5%', '32.8%']]
        md = self._convert([{'body': table_frame(rows)}])
        self.assertIn('| 指標 | 組別A | 組別B |', md)
        self.assertIn('| ORR | 58.5% | 32.8% |', md)


class ChartTests(ConvertTestCase):

    def _chart_slide(self, xml):
        return {'body': chart_frame('rId1'),
                'rels': [('rId1', REL_CHART, '../charts/chart1.xml')],
                'charts': {'chart1.xml': xml}}

    def test_bar_chart_data_lossless_with_mermaid(self):
        xml = chart_xml('療效比較', ['A組', 'B組'],
                        [('ORR', ['32.799999999999997', '5'])])
        md = self._convert([self._chart_slide(xml)])
        self.assertIn('原生圖表數據（長條圖）：療效比較', md)
        self.assertIn('| A組 | 32.8 |', md)   # 浮點雜訊清理
        self.assertIn('| B組 | 5 |', md)
        self.assertIn('```mermaid', md)
        self.assertIn('bar [32.8, 5]', md)

    def test_no_mermaid_flag_respected(self):
        xml = chart_xml('T', ['A'], [('S', ['1'])])
        md = self._convert([self._chart_slide(xml)], emit_mermaid=False)
        self.assertIn('原生圖表數據', md)
        self.assertNotIn('```mermaid', md)

    def test_line_chart_labeled_and_no_bar_mermaid(self):
        xml = chart_xml('趨勢', ['W1', 'W2'], [('PFS', ['1', '2'])],
                        kind='lineChart')
        md = self._convert([self._chart_slide(xml)])
        self.assertIn('原生圖表數據（折線圖）：趨勢', md)
        self.assertIn('| W1 | 1 |', md)
        # 折線畫成長條會誤導趨勢 → 不附 Mermaid，表格為準
        self.assertNotIn('```mermaid', md)

    def test_scatter_chart_xy_pairs_extracted(self):
        xml = chart_xml('相關性', ['1', '2', '3'],
                        [('反應', ['2.5', '4.5', '6.5'])],
                        kind='scatterChart', xy=True)
        md = self._convert([self._chart_slide(xml)])
        self.assertIn('原生圖表數據（散佈圖）：相關性', md)
        self.assertIn('| X值 | 反應 |', md)
        self.assertIn('| 1 | 2.5 |', md)
        self.assertIn('| 3 | 6.5 |', md)
        self.assertNotIn('```mermaid', md)


class SmartArtTests(ConvertTestCase):

    def test_smartart_text_extracted_verbatim(self):
        slide = {'body': diagram_frame('rId1'),
                 'rels': [('rId1', REL_DIAGRAM_DATA, '../diagrams/data1.xml')],
                 'diagrams': {'data1.xml': diagram_data_xml(['篩選', '隨機分派', '追蹤'])}}
        md = self._convert([slide])
        self.assertIn('SmartArt 圖形文字', md)
        for t in ('篩選', '隨機分派', '追蹤'):
            self.assertIn(f'- {t}', md)
        # parTrans 轉場節點＝模板殘留，不得混入內容
        self.assertNotIn('TRANSITION_NOISE', md)

    def test_smartart_unreadable_marked_not_silent(self):
        slide = {'body': diagram_frame('rId1'),
                 'rels': [('rId1', REL_DIAGRAM_DATA, '../diagrams/missing.xml')]}
        md = self._convert([slide])
        self.assertIn('SmartArt 圖形，文字無法抽取', md)


class NotesTests(ConvertTestCase):

    def test_notes_mapped_via_rels_not_by_number(self):
        # notesSlide 檔名編號 ≠ 投影片編號：slide1 掛 notesSlide7.xml
        slide = {'body': text_sp(['本文']),
                 'rels': [('rId1', REL_NOTES, '../notesSlides/notesSlide7.xml')]}
        extra = {'ppt/notesSlides/notesSlide7.xml':
                 notes_xml(['這是掛在第七號備註檔的口述內容'])}
        md = self._convert([slide], extra_files=extra)
        self.assertIn('講者備註（本頁專屬口述論點）', md)
        self.assertIn('這是掛在第七號備註檔的口述內容', md)

    def test_boilerplate_notes_deduplicated_across_slides(self):
        boiler = ['參考文獻：Smith et al. NEJM 2020']
        slides = [
            {'body': text_sp(['頁一']), 'notes': boiler},
            {'body': text_sp(['頁二']), 'notes': ['只有這一頁才有的口述論點']},
            {'body': text_sp(['頁三']), 'notes': boiler},
        ]
        md = self._convert(slides)
        self.assertIn('制式引註（全文首次出現', md)
        self.assertIn('內容同投影片 1，此處略', md)
        self.assertEqual(md.count('Smith et al. NEJM 2020'), 1)
        self.assertIn('講者備註（本頁專屬口述論點）', md)
        self.assertIn('只有這一頁才有的口述論點', md)


class ProvenanceTests(ConvertTestCase):

    def test_deck_labeled_provenance_extracted_verbatim(self):
        md = self._convert([{'body': text_sp(
            ['Adapted from Smith et al. NEJM 2020;383:1234'])}])
        self.assertIn('圖片出處字樣（deck 自標，逐字，未查證）', md)
        self.assertIn('〔論文層〕Adapted from Smith et al. NEJM 2020;383:1234', md)

    def test_figure_level_provenance_tagged(self):
        md = self._convert([{'body': text_sp(['Figure 3. Kaplan-Meier curve'])}])
        self.assertIn('〔含圖號〕', md)


class OutputOptionTests(ConvertTestCase):

    def test_frontmatter_option(self):
        md = self._convert([{'body': text_sp(['內容'])}], frontmatter=True)
        self.assertTrue(md.startswith('---'))
        self.assertIn('source: "deck.pptx"', md)
        self.assertIn('type: ', md)

    def test_no_frontmatter_by_default(self):
        md = self._convert([{'body': text_sp(['內容'])}])
        self.assertTrue(md.startswith('# deck'))


class UnitTests(unittest.TestCase):

    def test_num_cleans_float_noise(self):
        self.assertEqual(extract._num('32.799999999999997'), '32.8')
        self.assertEqual(extract._num('5'), '5')
        self.assertEqual(extract._num('N/A'), 'N/A')
        self.assertEqual(extract._num(None), '')

    def test_is_axis_like(self):
        self.assertTrue(extract._is_axis_like(['0', '10', '20', '30', '40']))
        self.assertFalse(extract._is_axis_like(['58.5', '53.4', '18.9', '26.4', '7.2']))
        self.assertFalse(extract._is_axis_like(['0', '10', '20', '30']))  # <5 個

    def test_md_table_keeps_protected_empty_column(self):
        grid = [['A', '', 'B'], ['1', '', '2']]
        protected = [[False, True, False], [False, True, False]]
        md = extract._md_table(grid, protected)
        self.assertIn('| A |   | B |', md)

    def test_md_table_drops_unprotected_empty_column(self):
        md = extract._md_table([['A', '', 'B'], ['1', '', '2']])
        self.assertIn('| A | B |', md)


if __name__ == '__main__':
    unittest.main()
