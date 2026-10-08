#!/usr/bin/env python3
"""
Sinh docs/Khoa_luan_tot_nghiep.docx — bản thảo khóa luận tốt nghiệp.

Định dạng theo "Quy định về trình bày đồ án tốt nghiệp" của Trường Đại học Công nghệ,
ĐHQGHN: giấy A4, chữ 13pt Times New Roman, dãn dòng 1,3 lines, lề trên 2,5 cm, lề dưới 3 cm,
lề trái 3 cm, lề phải 2 cm, hai đoạn cách nhau 6pt, thụt đầu dòng 1 cm; số trang đánh liên tục
từ phần Mở đầu, đặt giữa chân trang; chương/mục đánh bằng số Ả Rập; tiêu đề bảng đặt TRÊN bảng,
tiêu đề hình đặt DƯỚI hình.

Cần python-docx. Máy không có pip; cách đã dùng: tải wheel python_docx từ PyPI, giải nén vào một
thư mục X rồi chạy:  PYTHONPATH=X python3 docs/tools/build_thesis_docx.py
"""

import os
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

WS = os.path.expanduser('~/ros2_closed_loop_ws')
FIG = os.path.join(WS, 'docs', 'figures')
OUT = os.path.join(WS, 'docs', 'Khoa_luan_tot_nghiep.docx')
FONT = 'Times New Roman'
MONO = 'Consolas'
BODY_PT = 13

doc = Document()

# ------------------------------------------------------------------ danh mục hình và bảng
# Khai báo theo đúng thứ tự xuất hiện trong bài; hàm IMG/T tra cứu ở đây để số hiệu và danh mục
# không bao giờ lệch nhau (cuối script có kiểm tra mọi mục đều đã được dùng đúng một lần).
FIGURES = [
    ('2.1', 'Sơ đồ hình học một chân của robot delta dạng quay', 'delta_leg_diagram.png', 13.0),
    ('3.1', 'Kiến trúc tổng thể của hệ thống', 'system_architecture.png', 16.0),
    ('3.2', 'Sơ đồ các node và topic ROS 2 khi chạy pick_place.launch.py', 'ros_graph.png', 16.0),
    ('5.1', 'Ảnh camera mô phỏng với sáu marker ArUco đã được nhận dạng trong quá trình '
            'hiệu chuẩn', 'calibration_markers.png', 14.0),
    ('5.2', 'Kết quả ước lượng vị trí ba vật thể (đơn vị mm, hệ tọa độ robot) chiếu lên ảnh '
            'camera', 'vision_objects_mm.png', 14.0),
    ('7.1', 'Bản đồ sai số ước lượng vị trí theo vị trí vật trên mặt bàn',
     'vision_error_map.png', 16.0),
    ('7.2', 'Độ bền của khối thị giác với nhiễu Gauss và với thay đổi độ sáng',
     'vision_robustness.png', 16.0),
    ('8.1', 'Ảnh camera thật với sáu marker, vùng xét giới hạn theo hình học và ba lon đã được '
            'nhận dạng', 'real_camera_detections.png', 16.0),
    ('8.2', 'So sánh hai cách tách vật khỏi nền trên cùng một khung hình: (a) lấy ngưỡng theo màu '
            'và độ sáng, (b) trừ theo ảnh nền tham chiếu', 'foreground_comparison.png', 16.0),
    ('9.1', 'Tọa độ cùng một vật nhìn từ ba chỗ: đo trên bàn thật, quy về cảnh ảo, và vị trí vật '
            'ảo đang nằm trong Gazebo', 'twin_coordinates.png', 15.0),
]
TABLES = [
    ('1.1', 'Các bước thực hiện đề tài và trạng thái tại thời điểm viết khóa luận'),
    ('2.1', 'Thông số hình học của robot delta trích từ mô hình URDF'),
    ('2.2', 'Bán kính vùng làm việc theo mọi hướng tại từng cao độ'),
    ('3.1', 'Các vật thể và khay trong môi trường mô phỏng (hệ tọa độ robot)'),
    ('3.2', 'Các node ROS 2 trong hệ thống và chức năng'),
    ('3.3', 'Các topic và dịch vụ chính'),
    ('3.4', 'Hệ số thời gian thực (RTF) của mô phỏng theo cấu hình đồ họa'),
    ('4.1', 'Tham số của node điều khiển Descartes'),
    ('4.2', 'Các lệnh cấp cao của giao diện dòng lệnh'),
    ('4.3', 'Sai lệch quỹ đạo đo trên Gazebo'),
    ('5.1', 'Thông số camera mô phỏng'),
    ('5.2', 'Ngưỡng phân đoạn màu trong không gian HSV'),
    ('5.3', 'Kết quả hiệu chuẩn ngoại tham số camera'),
    ('6.1', 'Hai nguồn vị trí vật và cách kiểm chứng tương ứng'),
    ('7.1', 'Sai lệch giữa vị trí đặt và vị trí đo được trên Gazebo'),
    ('7.2', 'Tổng hợp sai số ước lượng vị trí bằng thị giác (172 mẫu)'),
    ('7.3', 'Ảnh hưởng của việc robot che khuất vật'),
    ('7.4', 'So sánh trước và sau khi áp dụng ước lượng có xét che khuất'),
    ('7.5', 'Độ bền với nhiễu Gauss'),
    ('7.6', 'Độ bền với thay đổi độ sáng'),
    ('7.7', 'Kết quả thí nghiệm gắp–thả trên 10 bố trí ngẫu nhiên'),
    ('7.8', 'Thống kê kiểm thử tự động của package delta_controller'),
    ('7.9', 'Đối chiếu yêu cầu đặt ra và kết quả đạt được'),
    ('8.1', 'Thiết bị và thông số bố trí thực nghiệm với camera thật'),
    ('8.2', 'Kết quả hiệu chuẩn nội tham số camera Logitech C270'),
    ('8.3', 'Kết quả hiệu chuẩn ngoại tham số trên bàn thật'),
    ('8.4', 'Hai cơ chế hỏng của phương pháp lấy ngưỡng theo điều kiện chiếu sáng'),
    ('8.5', 'Sai số định vị trên bàn thật: khớp mép đáy so với khớp mép trên (18 phép đo)'),
    ('8.6', 'Đối chiếu kết quả giữa môi trường mô phỏng và bàn thật'),
    ('8.7', 'Kết quả tách vùng gộp khi hai lon đứng chạm nhau trong ảnh'),
    ('9.1', 'Ba mức tích hợp giữa thế giới thật và mô hình số theo Kritzinger'),
    ('9.2', 'Các lớp lọc của bản sao số và căn cứ của từng lớp'),
    ('9.3', 'Kết quả điều khiển bám theo vật'),
    ('A.1', 'Thông số hình học và giới hạn khớp của robot'),
    ('A.2', 'Thông số môi trường làm việc'),
    ('C.1', 'Các tệp mã nguồn của package delta_controller'),
    ('D.1', 'Đối chiếu thuật ngữ Việt – Anh dùng trong khóa luận'),
]
FIG_USED, TAB_USED = set(), set()
_FIG_MAP = {k: (cap, fn, w) for k, cap, fn, w in FIGURES}
_TAB_MAP = dict(TABLES)


# ------------------------------------------------------------------ định dạng chung
def _insert_ordered(parent, element, after_tags):
    """Chèn element vào parent đúng vị trí: trước phần tử đầu tiên thuộc after_tags."""
    for child in parent:
        if child.tag.split('}')[1] in after_tags:
            child.addprevious(element)
            return
    parent.append(element)


_AFTER_PGNUM = {'cols', 'formProt', 'vAlign', 'noEndnote', 'titlePg', 'textDirection',
                'bidi', 'rtlGutter', 'docGrid', 'printerSettings', 'footnotePr', 'endnotePr'}


def page_setup(sec):
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(2.5), Cm(3)
    sec.left_margin, sec.right_margin = Cm(3), Cm(2)


def setup():
    page_setup(doc.sections[0])
    st = doc.styles['Normal']
    st.font.name = FONT
    st.font.size = Pt(BODY_PT)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    pf = st.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing = 1.3
    pf.first_line_indent = Cm(1)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for level, size in ((1, 15), (2, 14), (3, 13)):
        h = doc.styles[f'Heading {level}']
        h.font.name = FONT
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.color.rgb = RGBColor(0, 0, 0)   # quy định không cho dùng màu lạ
        h.font.italic = False
        h.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
        hp = h.paragraph_format
        hp.space_before = Pt(12 if level == 1 else 10)
        hp.space_after = Pt(6)
        hp.first_line_indent = Cm(0)
        hp.line_spacing = 1.3
        hp.keep_with_next = True
    for name in ('List Bullet', 'List Number', 'List Bullet 2', 'List Number 2'):
        s = doc.styles[name]
        s.font.name = FONT
        s.font.size = Pt(BODY_PT)
        s.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
        s.paragraph_format.space_after = Pt(3)
        s.paragraph_format.line_spacing = 1.3
    # Word tự cập nhật mục lục khi mở file
    settings = doc.settings.element
    upd = OxmlElement('w:updateFields')
    upd.set(qn('w:val'), 'true')
    _insert_ordered(settings, upd, {
        'hdrShapeDefaults', 'footnotePr', 'endnotePr', 'compat', 'docVars', 'rsids',
        'mathPr', 'attachedSchema', 'themeFontLang', 'clrSchemeMapping',
        'doNotIncludeSubdocsInStats', 'doNotAutoCompressPictures', 'forceUpgrade',
        'captions', 'readModeInkLockDown', 'smartTagType', 'schemaLibrary',
        'shapeDefaults', 'doNotEmbedSmartTags', 'decimalSymbol', 'listSeparator'})
    for zoom in settings.iter(qn('w:zoom')):   # mẫu mặc định của python-docx thiếu w:percent
        if zoom.get(qn('w:percent')) is None:
            zoom.set(qn('w:percent'), '100')


def field(paragraph, code):
    run = paragraph.add_run()
    for kind, text in (('begin', None), (None, code), ('separate', None), ('end', None)):
        if kind:
            el = OxmlElement('w:fldChar')
            el.set(qn('w:fldCharType'), kind)
        else:
            el = OxmlElement('w:instrText')
            el.set(qn('xml:space'), 'preserve')
            el.text = text
        run._r.append(el)


def start_numbered_body():
    """Mở phần nội dung: section mới, số trang đánh lại từ 1 và đặt giữa chân trang."""
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    page_setup(sec)
    sec.footer.is_linked_to_previous = False
    pg = OxmlElement('w:pgNumType')
    pg.set(qn('w:start'), '1')
    _insert_ordered(sec._sectPr, pg, _AFTER_PGNUM)
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    field(p, 'PAGE')
    return sec


INLINE = re.compile(r'(\*\*.+?\*\*|\*.+?\*|`.+?`)')


def add_runs(p, text, size=None, color=None):
    """Hỗ trợ **đậm**, *nghiêng* và `mã` trong câu."""
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            r = p.add_run(part[2:-2])
            r.bold = True
        elif part.startswith('*') and part.endswith('*') and len(part) > 2:
            r = p.add_run(part[1:-1])
            r.italic = True
        elif part.startswith('`') and part.endswith('`'):
            r = p.add_run(part[1:-1])
            r.font.name = MONO
            r.element.rPr.rFonts.set(qn('w:eastAsia'), MONO)
            r.font.size = Pt((size or BODY_PT) - 2)
            continue
        else:
            r = p.add_run(part)
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = color
    return p


def H1(t, page_break=True):
    if page_break:
        BREAK()
    doc.add_heading(t, 1)


def H2(t):
    doc.add_heading(t, 2)


def H3(t):
    doc.add_heading(t, 3)


def CENTER(text, size=BODY_PT, bold=False, italic=False, space_after=6, caps=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text.upper() if caps else text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    r.font.name = FONT
    return p


def FRONT_HEAD(text):
    """Tiêu đề các phần đầu (không vào mục lục)."""
    p = CENTER(text.upper(), size=14, bold=True, space_after=12)
    p.paragraph_format.space_before = Pt(6)
    return p


def P(t, indent=True, size=None):
    p = doc.add_paragraph()
    add_runs(p, t, size=size)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if not indent:
        p.paragraph_format.first_line_indent = Cm(0)
    return p


def B(items, style='List Bullet'):
    for it in items:
        p = doc.add_paragraph(style=style)
        p.paragraph_format.first_line_indent = Cm(0)
        add_runs(p, it)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def N(items):
    B(items, 'List Number')


_AFTER_SHD_PPR = {'tabs', 'suppressAutoHyphens', 'kinsoku', 'wordWrap', 'overflowPunct',
                  'topLinePunct', 'autoSpaceDE', 'autoSpaceDN', 'bidi', 'adjustRightInd',
                  'snapToGrid', 'spacing', 'ind', 'contextualSpacing', 'mirrorIndents',
                  'suppressOverlap', 'jc', 'textDirection', 'textAlignment', 'textboxTightWrap',
                  'outlineLvl', 'divId', 'cnfStyle', 'rPr', 'sectPr', 'pPrChange'}
_AFTER_SHD_TCPR = {'noWrap', 'tcMar', 'textDirection', 'tcFitText', 'vAlign', 'hideMark'}


def shade(obj, hex_color, is_cell=True):
    el = obj._tc.get_or_add_tcPr() if is_cell else obj._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    _insert_ordered(el, shd, _AFTER_SHD_TCPR if is_cell else _AFTER_SHD_PPR)


def T(key, header, rows, widths=None, size=12):
    """Bảng có tiêu đề đặt TRÊN bảng theo quy định."""
    caption = _TAB_MAP[key]
    assert key not in TAB_USED, f'Bảng {key} dùng hai lần'
    TAB_USED.add(key)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    add_runs(p, f'**Bảng {key}.** {caption}', size=12)
    table = doc.add_table(rows=1, cols=len(header))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = table.rows[0].cells[i]
        c.text = ''
        add_runs(c.paragraphs[0], f'**{h}**', size=size)
        shade(c, 'E8E8E8')
    for row in rows:
        cells = table.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ''
            add_runs(cells[i].paragraphs[0], str(v), size=size)
    if widths:
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    for row in table.rows:
        for c in row.cells:
            for pp in c.paragraphs:
                pp.paragraph_format.space_after = Pt(2)
                pp.paragraph_format.space_before = Pt(2)
                pp.paragraph_format.line_spacing = 1.0
                pp.paragraph_format.first_line_indent = Cm(0)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def IMG(key):
    """Hình có tiêu đề đặt DƯỚI hình theo quy định."""
    caption, filename, width = _FIG_MAP[key]
    assert key not in FIG_USED, f'Hình {key} dùng hai lần'
    FIG_USED.add(key)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(os.path.join(FIG, filename), width=Cm(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.first_line_indent = Cm(0)
    c.paragraph_format.space_after = Pt(10)
    add_runs(c, f'**Hình {key}.** {caption}', size=12)


def CODE(lines):
    for ln in lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run(ln if ln else ' ')
        r.font.name = MONO
        r.element.rPr.rFonts.set(qn('w:eastAsia'), MONO)
        r.font.size = Pt(10.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def EQ(text, number=None):
    """Công thức căn giữa; number là số hiệu đặt bên phải (vd. '2.3')."""
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.font.name = 'Cambria Math'
    r.element.rPr.rFonts.set(qn('w:eastAsia'), 'Cambria Math')
    r.font.size = Pt(13)
    if number:
        r2 = p.add_run(f'\t\t({number})')
        r2.font.size = Pt(13)
    return p


def BREAK():
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_break(WD_BREAK.PAGE)


def TOC(code):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    field(p, code)
    return p


# ============================================================================ PHẦN ĐẦU
setup()

TITLE = 'ỨNG DỤNG THỊ GIÁC MÁY TÍNH TRONG ĐIỀU KHIỂN ROBOT DELTA'
STUDENT = '<Họ và tên sinh viên>'
MAJOR = '<Ghi đúng tên ngành đào tạo>'
SUPERVISOR = '<Học hàm, học vị và họ tên cán bộ hướng dẫn>'
YEAR = '2026'


def cover(with_supervisor):
    CENTER('ĐẠI HỌC QUỐC GIA HÀ NỘI', size=12, bold=True, space_after=0)
    CENTER('TRƯỜNG ĐẠI HỌC CÔNG NGHỆ', size=12, bold=True, space_after=6)
    for _ in range(4):
        doc.add_paragraph()
    CENTER(STUDENT, size=14, bold=True, space_after=6)
    for _ in range(3):
        doc.add_paragraph()
    CENTER(TITLE, size=18, bold=True, space_after=6)
    for _ in range(3):
        doc.add_paragraph()
    CENTER('ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC HỆ CHÍNH QUY', size=14, bold=True, space_after=6)
    CENTER(f'Ngành: {MAJOR}', size=14, bold=True, space_after=6)
    if with_supervisor:
        for _ in range(3):
            doc.add_paragraph()
        p = CENTER(f'Cán bộ hướng dẫn: {SUPERVISOR}', size=14, bold=True, space_after=6)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for _ in range(4 if with_supervisor else 6):
        doc.add_paragraph()
    CENTER(f'HÀ NỘI – {YEAR}', size=12, bold=True, space_after=0)
    BREAK()


cover(with_supervisor=False)
cover(with_supervisor=True)

# ---------------------------------------------------------------- tóm tắt
FRONT_HEAD('Tóm tắt')
for t in [
    'Robot delta là cơ cấu song song ba bậc tự do được dùng rộng rãi trong các dây chuyền gắp–thả '
    'tốc độ cao. Để robot làm việc được với vật thể có vị trí không biết trước, hệ điều khiển phải '
    'nhận vị trí vật từ một cảm biến ngoài, mà phổ biến nhất là camera. Khóa luận này xây dựng một '
    'hệ thống hoàn chỉnh trong đó thị giác máy tính cung cấp vị trí vật thể cho robot delta hoạt '
    'động trong môi trường mô phỏng ROS 2 Jazzy và Gazebo Harmonic.',
    'Nội dung đã thực hiện gồm bốn nhóm. Thứ nhất, xây dựng và kiểm chứng mô hình động học của '
    'robot: công thức động học ngược dạng đóng giải bằng phép thế Weierstrass kèm tiêu chí chọn '
    'nhánh khuỷu ra ngoài, và công thức động học thuận bằng phép giao ba mặt cầu; vòng lặp động '
    'học ngược – thuận trên 5 424 điểm cho sai số dưới 5×10⁻¹³ m, còn trên mô phỏng vật lý sai '
    'lệch vị trí bàn máy nhỏ hơn 1 mm. Thứ hai, xây dựng môi trường tương tác gồm bàn, ba vật thể '
    'màu, khay ba ô và một giác hút ảo, kèm bộ quy hoạch quỹ đạo biên dạng bậc năm và lớp lệnh '
    'cấp cao gắp–thả có kiểm chứng kết quả. Thứ ba, xây dựng khối thị giác: phân đoạn màu trong '
    'không gian HSV, hiệu chuẩn ngoại tham số camera bằng sáu marker ArUco với sai số vị trí '
    '0,35 mm, chuyển tọa độ ảnh sang tọa độ robot bằng phép giao tia với mặt phẳng, và một bộ '
    'ước lượng có xét che khuất dựa trên hình bóng dự đoán của vật. Thứ tư, tích hợp và đánh giá: '
    'trên bộ dữ liệu 172 ảnh có vị trí thật làm đối chứng, sai số ngang trung bình trong vùng '
    'robot gắp được là 1,13 mm; trong mười bố trí ngẫu nhiên, robot điều khiển hoàn toàn bằng '
    'camera gắp và thả đúng 30/30 vật, bằng với khi dùng vị trí thật từ mô phỏng.',
    'Thứ năm, hệ thống được chuyển sang dùng camera thật quan sát lon nước ngọt đặt trên bàn '
    'thật, với thế giới thật được thu nhỏ ba lần khi đưa vào mô phỏng. Phép đo trên bàn thật cho '
    'sai số định vị trung bình 4,50 mm và lớn nhất 6,31 mm quy đổi, toàn bộ nằm trong dung sai '
    'gắp 12 mm. Vị trí vật thật được chép tự động sang mô phỏng với sai lệch dưới 1 mm, và robot '
    'bám theo vật đang di chuyển với sai lệch 3 – 4 mm.',
    'Kết quả cho thấy độ chính xác của khối thị giác đủ cho yêu cầu gắp–thả và các cơ chế xử lý '
    'che khuất là yếu tố quyết định độ tin cậy của hệ thống. Quá trình chuyển sang camera thật '
    'làm lộ ra ba vấn đề không tồn tại trong mô phỏng — ngưỡng phân đoạn cố định không bền với '
    'thay đổi chiếu sáng, mặt bàn phản chiếu vật, và các vùng ảnh giả mạo mà phép kiểm tra dựa '
    'trên diện tích về nguyên tắc không phát hiện được — cùng cách khắc phục từng vấn đề.',
]:
    p = P(t, size=12)
    p.paragraph_format.line_spacing = 1.2

p = doc.add_paragraph()
p.paragraph_format.first_line_indent = Cm(0)
r = p.add_run('Từ khóa: ')
r.bold = True
r.italic = True
r.font.size = Pt(12)
r = p.add_run('robot delta, thị giác máy tính, ROS 2, hiệu chuẩn camera.')
r.font.size = Pt(12)
BREAK()

FRONT_HEAD('Abstract')
for t in [
    'The delta robot is a three degree-of-freedom parallel mechanism widely used in high-speed '
    'pick-and-place lines. In order to handle objects whose positions are not known in advance, '
    'the controller must obtain those positions from an external sensor, most commonly a camera. '
    'This thesis builds a complete system in which computer vision supplies object positions to a '
    'delta robot running in a ROS 2 Jazzy and Gazebo Harmonic simulation.',
    'The work covers four parts. First, a closed-form inverse kinematics solution obtained through '
    'the Weierstrass substitution with an elbow-out branch criterion, and a forward kinematics '
    'solution obtained by three-sphere trilateration; the inverse–forward round trip over 5,424 '
    'points agrees to within 5×10⁻¹³ m, and the platform position measured in the physics '
    'simulation differs from the commanded one by less than 1 mm. Second, an interactive '
    'environment with a table, three coloured objects, a three-slot bin and a virtual suction '
    'gripper, together with a quintic (minimum-jerk) trajectory generator and a verified '
    'high-level pick-and-place command layer. Third, the vision pipeline: HSV colour '
    'segmentation, extrinsic camera calibration from six ArUco markers with a position error of '
    '0.35 mm, image-to-robot conversion by ray–plane intersection, and an occlusion-aware '
    'estimator based on a predicted object silhouette. Fourth, integration and evaluation: over a '
    'dataset of 172 images with ground truth, the mean horizontal error inside the reachable '
    'workspace is 1.13 mm; over ten random layouts the camera-driven robot picked and placed '
    '30 out of 30 objects, matching the ground-truth baseline.',
    'Fifth, the system is moved to a real camera observing drink cans on a real table, with the '
    'real world scaled down by a factor of three as it enters the simulation. Measured against '
    'marked positions on the table, the mean localisation error is 4.50 mm and the worst case '
    '6.31 mm in scaled units, all within the 12 mm grasping tolerance. Real object positions are '
    'mirrored into the simulation to within 1 mm, and the robot tracks a moving can to within '
    '3-4 mm.',
    'The results show that the accuracy of the vision pipeline is sufficient for the '
    'pick-and-place task, and that occlusion handling is the decisive factor for reliability. '
    'Moving to a real camera exposed three problems absent from simulation — a fixed '
    'segmentation threshold that cannot survive a change of lighting, a table that reflects the '
    'objects, and spurious image regions that an area-based check is structurally unable to '
    'reject — together with a remedy for each.',
]:
    p = P(t, size=12)
    p.paragraph_format.line_spacing = 1.2

p = doc.add_paragraph()
p.paragraph_format.first_line_indent = Cm(0)
r = p.add_run('Keywords: ')
r.bold = True
r.italic = True
r.font.size = Pt(12)
r = p.add_run('delta robot, computer vision, ROS 2, camera calibration.')
r.font.size = Pt(12)
BREAK()

# ---------------------------------------------------------------- lời cam đoan
FRONT_HEAD('Lời cam đoan')
P('Tôi xin cam đoan rằng đồ án tốt nghiệp với đề tài “Ứng dụng thị giác máy tính trong điều khiển '
  'robot delta” là công trình do tôi thực hiện dưới sự hướng dẫn của ' + SUPERVISOR + '.')
P('Các công thức động học, thuật toán xử lý ảnh, chương trình điều khiển và toàn bộ số liệu thực '
  'nghiệm trình bày trong đồ án đều do tôi tự xây dựng, tự chạy và tự đo trên hệ thống mô phỏng '
  'của mình. Mọi kết quả được nêu đều kèm theo cách đo và điều kiện đo tương ứng, có thể lặp lại '
  'bằng các chương trình đính kèm trong phụ lục.')
P('Mô hình robot mạch động học kín dùng làm nền cho phần mô phỏng được kế thừa từ một dự án mã '
  'nguồn mở và đã được ghi rõ trong phần tài liệu tham khảo. Mọi tài liệu, hình vẽ, công thức hay '
  'ý tưởng của tác giả khác được sử dụng trong đồ án đều được trích dẫn đầy đủ. Tôi không sao chép '
  'tài liệu hay công trình nghiên cứu của người khác mà không chỉ rõ trong phần tài liệu tham khảo.')
P('Tôi xin chịu hoàn toàn trách nhiệm về lời cam đoan này.')
doc.add_paragraph()
p = CENTER('Hà Nội, ngày ..... tháng ..... năm ' + YEAR, italic=True, space_after=0)
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
p = CENTER('Sinh viên thực hiện', bold=True, space_after=0)
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
for _ in range(3):
    doc.add_paragraph()
p = CENTER(STUDENT, space_after=0)
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
BREAK()

# ---------------------------------------------------------------- lời cảm ơn
FRONT_HEAD('Lời cảm ơn')
P('Trước hết, tôi xin bày tỏ lòng biết ơn sâu sắc tới ' + SUPERVISOR + ' đã định hướng đề tài, '
  'theo sát tiến độ và cho tôi những góp ý quan trọng trong suốt quá trình thực hiện đồ án. Thầy '
  'cũng là người đã tạo điều kiện về thiết bị để tôi có thể chuyển hệ thống từ mô phỏng sang '
  'camera thật ở giai đoạn tiếp theo.')
P('Tôi xin cảm ơn các thầy cô Trường Đại học Công nghệ, Đại học Quốc gia Hà Nội đã trang bị cho '
  'tôi nền tảng kiến thức về toán học, cơ học, điều khiển và xử lý ảnh — những kiến thức được sử '
  'dụng trực tiếp trong đồ án này.')
P('Tôi cũng xin cảm ơn cộng đồng mã nguồn mở ROS 2, Gazebo và OpenCV, cùng nhóm tác giả của dự án '
  'mô phỏng robot mạch động học kín đã công bố mô hình robot được dùng làm nền cho phần mô phỏng '
  'của đồ án.')
P('Cuối cùng, tôi xin cảm ơn gia đình và bạn bè đã luôn động viên tôi trong thời gian học tập và '
  'thực hiện đồ án.')
BREAK()

# ---------------------------------------------------------------- mục lục
FRONT_HEAD('Mục lục')
P('(Mục lục dưới đây là trường tự động của Microsoft Word. Khi mở tệp, Word sẽ tự cập nhật; nếu '
  'cần cập nhật lại sau khi chỉnh sửa, nhấn Ctrl+A rồi F9 và chọn “Update entire table”.)',
  size=11).runs[0].italic = True
TOC(r'TOC \o "1-3" \h \z \u')
BREAK()

# ---------------------------------------------------------------- danh mục viết tắt
FRONT_HEAD('Danh mục ký hiệu và chữ viết tắt')
ABBR = [
    ('ArUco', 'Augmented Reality University of Cordoba — thư viện và bộ từ điển marker vuông '
              'dùng để xác định tư thế camera'),
    ('DOF', 'Degree Of Freedom — bậc tự do'),
    ('FK', 'Forward Kinematics — động học thuận'),
    ('HSV', 'Hue – Saturation – Value — không gian màu sắc màu, độ bão hòa, độ sáng'),
    ('IK', 'Inverse Kinematics — động học ngược'),
    ('LM', 'Levenberg – Marquardt — thuật toán tối ưu phi tuyến bình phương tối thiểu'),
    ('PID', 'Proportional – Integral – Derivative — bộ điều khiển tỉ lệ, tích phân, vi phân'),
    ('PnP', 'Perspective-n-Point — bài toán xác định tư thế camera từ n cặp điểm 3D–2D'),
    ('RMS', 'Root Mean Square — căn quân phương'),
    ('ROS 2', 'Robot Operating System 2 — nền tảng phần mềm cho robot'),
    ('RTF', 'Real Time Factor — hệ số thời gian thực của mô phỏng'),
    ('SDF', 'Simulation Description Format — định dạng mô tả thế giới mô phỏng của Gazebo'),
    ('SQPnP', 'Sequential Quadratic Programming PnP — thuật toán giải bài toán PnP'),
    ('URDF', 'Unified Robot Description Format — định dạng mô tả robot của ROS'),
]
SYMBOLS = [
    ('f, e', 'bán kính đế cố định và bán kính bàn máy động (m)'),
    ('r_f, r_e', 'chiều dài cánh tay trên và chiều dài thanh chống (m)'),
    ('θ₁, θ₂, θ₃', 'ba góc khớp chủ động (rad)'),
    ('φ_i', 'góc pha của chân thứ i (0°, 120°, 240°)'),
    ('P = (x₀, y₀, z₀)', 'tọa độ tâm bàn máy động trong hệ tọa độ đế (m)'),
    ('K', 'ma trận nội tham số của camera'),
    ('R, t', 'ma trận quay và véc-tơ tịnh tiến (ngoại tham số camera)'),
]
T_ROWS = [(k, v) for k, v in ABBR]
table = doc.add_table(rows=0, cols=2)
table.style = 'Table Grid'
for k, v in T_ROWS:
    cells = table.add_row().cells
    cells[0].text = ''
    add_runs(cells[0].paragraphs[0], f'**{k}**', size=12)
    cells[1].text = ''
    add_runs(cells[1].paragraphs[0], v, size=12)
    cells[0].width, cells[1].width = Cm(3.0), Cm(13.0)
for row in table.rows:
    for c in row.cells:
        for pp in c.paragraphs:
            pp.paragraph_format.space_after = Pt(2)
            pp.paragraph_format.line_spacing = 1.0
            pp.paragraph_format.first_line_indent = Cm(0)
doc.add_paragraph()
p = CENTER('Ký hiệu toán học', bold=True, space_after=6)
table = doc.add_table(rows=0, cols=2)
table.style = 'Table Grid'
for k, v in SYMBOLS:
    cells = table.add_row().cells
    cells[0].text = ''
    add_runs(cells[0].paragraphs[0], f'**{k}**', size=12)
    cells[1].text = ''
    add_runs(cells[1].paragraphs[0], v, size=12)
    cells[0].width, cells[1].width = Cm(3.0), Cm(13.0)
for row in table.rows:
    for c in row.cells:
        for pp in c.paragraphs:
            pp.paragraph_format.space_after = Pt(2)
            pp.paragraph_format.line_spacing = 1.0
            pp.paragraph_format.first_line_indent = Cm(0)
BREAK()

# ---------------------------------------------------------------- danh mục hình, bảng
FRONT_HEAD('Danh mục hình vẽ')
for key, cap, _fn, _w in FIGURES:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(4)
    add_runs(p, f'**Hình {key}.** {cap}', size=12)
BREAK()

FRONT_HEAD('Danh mục bảng biểu')
for key, cap in TABLES:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(4)
    add_runs(p, f'**Bảng {key}.** {cap}', size=12)

start_numbered_body()


# ============================================================================ MỞ ĐẦU
H1('MỞ ĐẦU', page_break=False)

P('**1. Tính cần thiết của đề tài.** Robot delta là cơ cấu song song có ba bậc tự do tịnh tiến, '
  'được R. Clavel đề xuất năm 1990 [3] và ngày nay là loại robot phổ biến nhất trong các dây '
  'chuyền gắp–thả tốc độ cao của công nghiệp thực phẩm, dược phẩm và điện tử. Ưu điểm của cơ cấu '
  'này là toàn bộ động cơ đặt cố định trên đế nên khối lượng chuyển động rất nhỏ, cho phép đạt gia '
  'tốc lớn mà vẫn giữ được độ chính xác.')
P('Tuy nhiên, một robot chỉ chạy theo chương trình dạy trước chỉ làm việc được khi vật luôn nằm '
  'đúng một chỗ. Trong thực tế sản xuất, vật đi trên băng tải hoặc được đổ ra bàn với vị trí không '
  'biết trước; khi đó hệ điều khiển buộc phải nhận vị trí vật từ một cảm biến bên ngoài. Camera là '
  'cảm biến được dùng nhiều nhất cho nhiệm vụ này vì giá rẻ, không tiếp xúc và cung cấp đồng thời '
  'thông tin về vị trí, hình dạng lẫn màu sắc của vật. Bài toán “mắt nhìn – tay làm” do đó là một '
  'nội dung cốt lõi của robot công nghiệp hiện đại, và cũng là nội dung trọng tâm của đồ án này.')
P('**2. Ý nghĩa khoa học và thực tiễn.** Về mặt khoa học, đồ án đi trọn vẹn chuỗi xử lý từ điểm '
  'ảnh tới lệnh khớp: nhận dạng vật trên ảnh, hiệu chuẩn camera để đổi tọa độ ảnh sang tọa độ '
  'robot, xử lý hiện tượng che khuất một phần, giải động học ngược để ra lệnh cho ba khớp chủ '
  'động, và kiểm chứng từng khâu bằng số liệu đo được. Điểm đáng chú ý về phương pháp là toàn bộ '
  'hệ thống được đánh giá dựa trên vị trí thật của vật do mô phỏng cung cấp, nhờ đó sai số của '
  'từng khâu được đo chứ không phải ước đoán.')
P('Về mặt thực tiễn, hệ thống được xây dựng theo kiến trúc cho phép thay nguồn ảnh mô phỏng bằng '
  'camera thật mà không phải sửa phần điều khiển. Đây chính là mô hình “bản sao số” (digital '
  'twin): vật thật nằm trên bàn thật, camera thật nhận dạng, còn robot mô phỏng thực hiện thao tác '
  'tương ứng. Cách làm này cho phép thử nghiệm thuật toán an toàn và rẻ trước khi triển khai trên '
  'robot thật.')
P('**3. Đối tượng và phạm vi nghiên cứu.** Đối tượng nghiên cứu là robot delta ba bậc tự do dạng '
  'quay cùng hệ thống thị giác đi kèm. Phạm vi của khóa luận này là giai đoạn mô phỏng: robot, '
  'vật thể, khay và camera đều nằm trong môi trường Gazebo Harmonic, điều khiển bằng ROS 2 Jazzy. '
  'Giai đoạn mô phỏng được chọn làm bước đầu vì ở đó luôn có sẵn vị trí thật của vật để làm đối '
  'chứng, cho phép đo chính xác sai số của khối thị giác — điều không thể làm dễ dàng với hệ '
  'thống thật. Phần camera thật và chế độ bám theo marker được trình bày như hướng phát triển '
  'tiếp theo ở chương kết luận.')
P('**4. Phương pháp nghiên cứu.** Đồ án sử dụng kết hợp ba phương pháp. Phương pháp giải tích được '
  'dùng để xây dựng công thức động học dạng đóng và mô hình chiếu của camera. Phương pháp mô phỏng '
  'số được dùng để dựng môi trường làm việc và chạy thử toàn hệ thống. Phương pháp thực nghiệm '
  'được dùng để đo sai số: mỗi kết luận trong khóa luận đều gắn với một phép đo cụ thể, có nêu số '
  'mẫu, điều kiện đo và cách chấm điểm. Ngoài ra, mọi thành phần tính toán thuần túy đều được tách '
  'khỏi phần phụ thuộc nền tảng ROS để kiểm thử tự động bằng công cụ kiểm thử đơn vị.')
P('**5. Nội dung nghiên cứu.** Khóa luận thực hiện năm nhóm công việc: (i) xây dựng và kiểm chứng '
  'mô hình động học thuận, ngược của robot delta; (ii) dựng môi trường mô phỏng có vật thể, khay '
  'chứa và cơ cấu gắp bằng giác hút ảo; (iii) xây dựng bộ quy hoạch quỹ đạo và lớp lệnh gắp–thả '
  'cấp cao có kiểm chứng; (iv) xây dựng khối thị giác gồm nhận dạng vật theo màu, hiệu chuẩn '
  'camera bằng marker ArUco, chuyển tọa độ ảnh sang tọa độ robot và xử lý che khuất; (v) tích hợp '
  'toàn hệ thống và đánh giá định lượng độ chính xác, độ bền cũng như tỉ lệ gắp–thả thành công.')

# ============================================================================ CHƯƠNG 1
H1('Chương 1. TỔNG QUAN')

P('Chương này trình bày bối cảnh của đề tài: đặc điểm của robot song song kiểu delta, vai trò của '
  'thị giác máy tính trong điều khiển robot, các công cụ phần mềm được sử dụng, từ đó phát biểu '
  'bài toán, giới hạn phạm vi và nêu kế hoạch thực hiện.')

H2('1.1. Robot song song và robot delta')

P('Robot công nghiệp được chia thành hai nhóm lớn theo cấu trúc động học. Nhóm **nối tiếp** gồm '
  'các khâu nối liên tiếp nhau như một cánh tay người: mỗi động cơ phải mang theo toàn bộ các khâu '
  'phía sau nó, nên khối lượng chuyển động lớn và gia tốc bị hạn chế, đổi lại vùng làm việc rộng '
  'và cấu trúc đơn giản. Nhóm **song song** nối bàn máy động với đế cố định bằng nhiều chuỗi động '
  'học độc lập hoạt động đồng thời; nhờ đó tải trọng được chia cho các chân, độ cứng vững cao và '
  'sai số của từng chân được trung bình hóa thay vì cộng dồn như ở robot nối tiếp [5], [16].')
P('Robot delta là đại diện tiêu biểu nhất của nhóm song song. Cấu trúc gồm ba chân giống nhau đặt '
  'cách đều 120°; mỗi chân có một cánh tay trên quay quanh trục cố định trên đế và một thanh chống '
  'dạng hình bình hành nối tới bàn máy động. Chính cấu trúc hình bình hành này giữ cho bàn máy '
  '**luôn song song với đế**, nghĩa là bàn máy chỉ tịnh tiến theo ba phương mà không quay. Robot '
  'khảo sát trong đồ án thuộc loại **delta dạng quay** (rotary delta) — ba khớp chủ động là khớp '
  'quay — khác với delta tịnh tiến có ba khớp trượt.')
P('Đặc điểm quan trọng nhất với người lập trình điều khiển là: ở robot delta, **động học ngược dễ '
  'hơn động học thuận**. Vì ba chân ràng buộc độc lập nhau qua điều kiện chiều dài thanh chống '
  'không đổi nên từ vị trí bàn máy có thể tính ngay từng góc khớp bằng công thức dạng đóng; ngược '
  'lại, từ ba góc khớp phải giải bài toán giao ba mặt cầu. Đây là điều trái ngược với robot nối '
  'tiếp và sẽ được trình bày chi tiết ở Chương 2.')

H2('1.2. Thị giác máy tính trong điều khiển robot')

P('Hệ thống robot có dẫn hướng bằng thị giác thường được phân loại theo vị trí đặt camera. Cấu '
  'hình **eye-in-hand** gắn camera lên khâu cuối, cho ảnh cận cảnh và thay đổi theo chuyển động '
  'của robot. Cấu hình **eye-to-hand** đặt camera cố định trong không gian làm việc, quan sát '
  'đồng thời robot lẫn vật thể. Đồ án này dùng cấu hình eye-to-hand vì nó phù hợp với ứng dụng '
  'gắp–thả trên bàn: một camera cố định nhìn bao quát toàn bộ vùng làm việc, không phải đi dây '
  'theo khâu chuyển động, và vị trí camera chỉ cần hiệu chuẩn một lần.')
P('Chuỗi xử lý của một hệ thống như vậy gồm bốn khâu nối tiếp. Khâu **thu nhận ảnh** lấy khung '
  'hình từ camera. Khâu **nhận dạng** tìm vật trên ảnh và trả về tọa độ điểm ảnh, ở đây dùng phân '
  'đoạn theo màu vì vật có màu tương phản rõ với nền. Khâu **hiệu chuẩn và chuyển hệ tọa độ** đổi '
  'tọa độ điểm ảnh sang tọa độ vật lý trong hệ tọa độ robot; đây là khâu quyết định độ chính xác '
  'của toàn hệ thống. Cuối cùng, khâu **lập kế hoạch và điều khiển** biến vị trí vật thành chuỗi '
  'thao tác của robot.')
P('Khó khăn lớn nhất của khâu chuyển hệ tọa độ là một camera đơn chỉ đo được **hướng** của tia '
  'nhìn chứ không đo được **khoảng cách**: mọi điểm nằm trên cùng một tia đều chiếu về một điểm '
  'ảnh. Muốn xác định được điểm 3D phải bổ sung một ràng buộc. Có ba cách thường dùng: dùng camera '
  'kép để tính chênh lệch thị sai, dùng camera chiều sâu, hoặc dùng ràng buộc hình học biết trước. '
  'Đồ án chọn cách thứ ba: vật luôn nằm trên mặt bàn hoặc trong khay có cao độ đã biết, nên giao '
  'tia nhìn với mặt phẳng nằm ngang đi qua tâm vật là đủ xác định vị trí. Cách này chỉ cần một '
  'camera thông thường, phù hợp với điều kiện thiết bị của đề tài.')
P('Khó khăn thứ hai — và trong thực nghiệm của đồ án là khó khăn quyết định — là **che khuất một '
  'phần**. Khi vật bị robot hoặc vật khác che mất một phần, tâm khối của vùng ảnh nhìn thấy không '
  'còn trùng với hình chiếu của tâm vật, gây sai số hệ thống theo hướng nhìn. Chương 5 và Chương 7 '
  'phân tích hiện tượng này và trình bày cách xử lý.')
P('Về cách nhận dạng vật, có thể chia thành ba nhóm phương pháp. Nhóm **dựa trên đặc trưng ảnh** '
  'sử dụng màu sắc, biên hoặc đặc trưng cục bộ; ưu điểm là nhanh, dễ giải thích và không cần dữ '
  'liệu huấn luyện, nhược điểm là nhạy với điều kiện chiếu sáng và chỉ áp dụng được khi vật có đặc '
  'trưng rõ ràng. Nhóm **dựa trên marker** dán mã lên vật hoặc lên mặt phẳng tham chiếu [7]: cách '
  'này cho độ chính xác cao nhất và vẫn được dùng phổ biến trong hiệu chuẩn, nhưng đòi hỏi can '
  'thiệp vào hiện trường. Nhóm **dựa trên học máy** cho khả năng khái quát tốt với vật đa dạng, '
  'đổi lại cần dữ liệu huấn luyện và tài nguyên tính toán lớn hơn nhiều [15].')
P('Đồ án chọn kết hợp hai nhóm đầu theo đúng vai trò mạnh nhất của mỗi nhóm: dùng **marker** cho '
  'khâu hiệu chuẩn, nơi độ chính xác là yếu tố quyết định và việc dán marker lên bàn là hoàn toàn '
  'chấp nhận được; dùng **đặc trưng màu** cho khâu nhận dạng vật, vì vật trong bài toán có màu '
  'phân biệt rõ và yêu cầu về tốc độ xử lý cao. Nhóm thứ ba được để lại cho hướng phát triển khi '
  'cần mở rộng sang vật chưa biết trước hình dạng và màu sắc.')

H2('1.3. Công cụ phần mềm và mô hình bản sao số')

P('**ROS 2** (Robot Operating System 2) [12] là nền tảng phần mềm cho robot theo kiến trúc phân '
  'tán: chương trình được chia thành các tiến trình độc lập gọi là *node*, trao đổi dữ liệu qua '
  '*topic* theo cơ chế xuất bản – đăng ký, hoặc qua *service* theo cơ chế yêu cầu – đáp ứng. Kiến '
  'trúc này cho phép thay thế từng khối mà không ảnh hưởng các khối còn lại — tính chất được khai '
  'thác trực tiếp trong đồ án khi thay nguồn vị trí vật từ mô phỏng sang camera. Phiên bản sử dụng '
  'là ROS 2 Jazzy Jalisco trên Ubuntu 24.04.')
P('**Gazebo Harmonic** [13] là phần mềm mô phỏng động lực học cho robot, mô phỏng trọng lực, va '
  'chạm, ma sát và cả cảm biến như camera. Gazebo cung cấp hai thứ mà hệ thật không có: khả năng '
  'thử nghiệm không giới hạn số lần mà không hỏng thiết bị, và **vị trí thật** của mọi vật thể, '
  'dùng làm đối chứng để đo sai số của khối thị giác.')
P('**OpenCV** [11] là thư viện xử lý ảnh mã nguồn mở, cung cấp các phép biến đổi không gian màu, '
  'phép toán hình thái học, thuật toán giải bài toán PnP và bộ nhận dạng marker ArUco được dùng '
  'trong chương 5.')
P('Mô hình **bản sao số** là ý tưởng xuyên suốt đề tài: môi trường mô phỏng được dựng sao cho '
  'giống môi trường thật về kích thước và bố trí, để khi có camera thật chỉ cần thay nguồn ảnh là '
  'hệ thống tiếp tục chạy. Cụ thể, bố trí sáu marker hiệu chuẩn trong mô phỏng được thiết kế đúng '
  'bằng bố trí sẽ in ra giấy A4 dán lên bàn thật, và quy trình hiệu chuẩn dùng chung một chương '
  'trình cho cả hai trường hợp.')

H2('1.4. Bài toán đặt ra và phạm vi của đồ án')

P('Bài toán được phát biểu như sau. Cho một robot delta ba bậc tự do mô phỏng trong Gazebo, một '
  'mặt bàn trên đó đặt ba vật thể màu đỏ, xanh lá và xanh dương ở vị trí bất kỳ trong vùng làm '
  'việc, một khay ba ô, và một camera đơn cố định nhìn xiên xuống bàn. Yêu cầu: chỉ dùng ảnh từ '
  'camera, hệ thống phải xác định được vị trí từng vật trong hệ tọa độ robot với sai số nhỏ hơn '
  'dung sai của cơ cấu gắp, rồi tự động gắp từng vật bỏ vào ô trống của khay và lấy trở lại về vị '
  'trí cũ khi được yêu cầu, có kiểm chứng kết quả sau mỗi thao tác.')
P('Yêu cầu định lượng quan trọng nhất suy ra từ cơ cấu gắp: giác hút chỉ bám được vật khi tâm bàn '
  'máy lệch tâm vật không quá 12 mm theo phương ngang. Đây chính là **dung sai mà khối thị giác '
  'phải bảo đảm**; mọi đánh giá trong Chương 7 đều quy chiếu về ngưỡng này.')
P('Phạm vi của khóa luận giới hạn ở: robot và vật thể trong mô phỏng; camera mô phỏng đặt cố định; '
  'vật thể có màu đã biết trước và hình dạng đơn giản (hộp, trụ, cầu); mặt bàn nằm ngang và cao độ '
  'đã biết. Các nội dung nằm ngoài phạm vi và được nêu ở phần hướng phát triển gồm: camera thật '
  'kèm hiệu chuẩn nội tham số và khử méo ống kính, nhận dạng vật theo hình dạng hoặc học máy, vật '
  'thể chuyển động trên băng tải, và chế độ robot bám theo marker cầm tay.')

H2('1.5. Kế hoạch thực hiện')

P('Đề tài được chia thành các bước nhỏ, mỗi bước kết thúc bằng một phép đo kiểm chứng trên mô '
  'phỏng trước khi chuyển sang bước tiếp theo. Bảng 1.1 tóm tắt các bước và trạng thái tại thời '
  'điểm viết khóa luận này.')

T('1.1',
  ['Bước', 'Nội dung', 'Kết quả kiểm chứng', 'Trạng thái'],
  [
      ('1 – 2', 'Xác định thông số hình học, xây dựng công thức động học ngược',
       'Kiểm chứng bằng tay tại vị trí gốc', 'Đã xong'),
      ('3', 'Cài đặt động học ngược và thuận, kiểm thử tự động',
       'Vòng lặp IK→FK: sai số < 5·10⁻¹³ m', 'Đã xong'),
      ('4', 'Node điều khiển theo tọa độ Descartes',
       '9 điểm đo trên Gazebo, sai lệch < 1 mm', 'Đã xong'),
      ('5', 'Môi trường có bàn và ba vật thể', 'Robot tới đúng phía trên cả ba vật', 'Đã xong'),
      ('6', 'Tương tác vật lý, quỹ đạo an toàn, giác hút ảo, khay chứa',
       'Gắp và thả được cả ba vật vào khay', 'Đã xong'),
      ('7', 'Lệnh cấp cao: gắp, thả, dọn, lấy ra, đặt lại',
       'Dọn 3 vật trong ~28 s, có kiểm chứng', 'Đã xong'),
      ('8', 'Khối thị giác: camera mô phỏng, nhận dạng màu, hiệu chuẩn, xử lý che khuất',
       'Sai số 1,13 mm trong vùng gắp được', 'Đã xong'),
      ('9', 'Gắp–thả hoàn toàn dựa trên camera',
       '30/30 vật, bằng với dùng vị trí thật', 'Đã xong'),
      ('10a', 'Camera thật: hiệu chuẩn nội và ngoại tham số, đo sai số định vị',
       'Sai số 4,50 mm quy đổi, trong dung sai 12 mm', 'Đã xong'),
      ('10b', 'Bản sao số: vị trí vật thật được chép sang mô phỏng',
       'Vật ảo bám vật thật trong 1 mm', 'Đã xong'),
      ('11', 'Robot bám theo vật khi vật di chuyển',
       'Sai lệch bám 3 – 4 mm khi vật đang dịch', 'Đã xong'),
      ('10c', 'Đo chiều cao vật; phân biệt nhiều vật cùng màu',
       '—', 'Hướng phát triển'),
  ],
  widths=[1.8, 6.0, 5.5, 2.5])

H2('1.6. Bố cục của khóa luận')

B([
    '**Chương 1** trình bày tổng quan về robot delta, thị giác máy tính trong điều khiển robot, '
    'công cụ sử dụng và phát biểu bài toán.',
    '**Chương 2** trình bày cơ sở lý thuyết: động học thuận và ngược của robot delta, quy hoạch '
    'quỹ đạo, mô hình camera, bài toán PnP và phân đoạn màu.',
    '**Chương 3** mô tả việc xây dựng hệ thống mô phỏng: mô hình robot mạch động học kín, môi '
    'trường làm việc, giác hút ảo, camera và kiến trúc phần mềm.',
    '**Chương 4** trình bày phần điều khiển: cài đặt động học, sinh quỹ đạo và lớp lệnh gắp–thả '
    'cấp cao.',
    '**Chương 5** trình bày khối thị giác: nhận dạng vật theo màu, hiệu chuẩn camera bằng marker '
    'ArUco, chuyển tọa độ ảnh sang tọa độ robot và ước lượng có xét che khuất.',
    '**Chương 6** trình bày việc tích hợp: robot gắp–thả hoàn toàn dựa trên dữ liệu camera.',
    '**Chương 7** trình bày phương pháp đánh giá và toàn bộ kết quả thực nghiệm trên mô phỏng.',
    '**Chương 8** chuyển hệ thống sang **camera thật**: hiệu chuẩn, nguyên tắc ánh xạ tỉ lệ, các '
    'vấn đề chỉ xuất hiện khi rời mô phỏng, và kết quả đo sai số trên bàn thật.',
    '**Chương 9** trình bày **bản sao số** và chế độ **bám theo vật**, khép vòng từ vật thật tới '
    'chuyển động của robot.',
    'Phần **Kết luận** tổng kết kết quả đạt được, hạn chế còn tồn tại và hướng phát triển.',
])

# ============================================================================ CHƯƠNG 2
H1('Chương 2. CƠ SỞ LÝ THUYẾT')

P('Chương này xây dựng toàn bộ nền tảng toán học được sử dụng trong đồ án: động học của robot '
  'delta, quy hoạch quỹ đạo, mô hình camera và các thuật toán thị giác. Các công thức được trình '
  'bày kèm điều kiện áp dụng và cách kiểm chứng, vì toàn bộ chúng đều được cài đặt thành chương '
  'trình ở các chương sau.')

H2('2.1. Mô hình hóa robot delta')

H3('2.1.1. Cấu trúc cơ khí và quy ước hệ tọa độ')

P('Robot khảo sát gồm: đế cố định mang ba khớp chủ động đặt cách đều 120° trên đường tròn bán kính '
  'f; ba cánh tay trên chiều dài r_f quay quanh trục nằm ngang tiếp tuyến với đường tròn đế; ba '
  'thanh chống chiều dài r_e nối với cánh tay trên và với bàn máy bằng khớp cầu ở cả hai đầu; và '
  'bàn máy động bán kính e mang đầu công tác. Ba góc khớp chủ động ký hiệu θ₁, θ₂, θ₃.')
P('Hệ tọa độ gắn với đế được quy ước: gốc O tại tâm mặt đế; trục X hướng ra chân thứ nhất; trục Z '
  'hướng **lên trên**; trục Y theo quy tắc bàn tay phải. Vì bàn máy treo phía dưới đế nên tọa độ '
  'z₀ của nó **luôn âm** — đây là một quy ước cần nhớ khi đọc mọi số liệu trong khóa luận. Góc pha '
  'của ba chân là φ₁ = 0°, φ₂ = 120°, φ₃ = 240°. Quy ước dấu góc khớp: θᵢ = 0 khi cánh tay trên '
  'nằm ngang hướng ra ngoài, θᵢ tăng khi cánh tay hạ xuống.')
P('Các thông số hình học được trích trực tiếp từ mô hình URDF của robot, bảo đảm công thức và mô '
  'phỏng dùng chung một bộ số liệu (Bảng 2.1).')

T('2.1',
  ['Ký hiệu', 'Ý nghĩa', 'Giá trị (m)', 'Nguồn trong URDF'],
  [
      ('f', 'Bán kính đế cố định', '0,0417', 'origin của khớp Chain1_1'),
      ('e', 'Bán kính bàn máy động', '0,0276', 'origin của khớp Chain1_cl_A'),
      ('r_f', 'Chiều dài cánh tay trên', '0,0758', 'origin của khớp Chain1_top_A'),
      ('r_e', 'Chiều dài thanh chống', '0,1668', 'origin của Chain1_tip_joint'),
  ],
  widths=[2.2, 6.0, 3.0, 5.0])

P('Giới hạn của cả ba khớp chủ động là θᵢ ∈ [−1,0297 rad; 1,4312 rad], tương đương '
  '[−59,0°; 82,0°]. Vị trí gốc (home) ứng với θ₁ = θ₂ = θ₃ = 0 cho bàn máy tại '
  'P_home = (0; 0; −0,1405) m. Điểm này được dùng làm **mốc kiểm chứng chuẩn** cho mọi công thức: '
  'bất kỳ công thức nào cũng phải tái tạo đúng cặp giá trị trên trước khi được sử dụng.')

H3('2.1.2. Ràng buộc cơ bản của mỗi chân')

P('Ký hiệu u_i = (cos φᵢ, sin φᵢ, 0) là véc-tơ đơn vị hướng ra chân thứ i. Khuỷu tay E_i là đầu '
  'ngoài của cánh tay trên, đồng thời là đầu trên của thanh chống:')
EQ('E_i = (f + r_f·cos θᵢ)·u_i − r_f·sin θᵢ·ẑ', '2.1')
P('Khớp cầu phía bàn máy B_i nằm trên bàn máy, lệch khỏi tâm bàn máy P một đoạn e theo hướng u_i:',
  indent=True)
EQ('B_i = P + e·u_i', '2.2')
P('Vì thanh chống là vật rắn nên chiều dài của nó không đổi. Đó là ràng buộc duy nhất của mỗi '
  'chân, và toàn bộ động học của robot được suy ra từ ba ràng buộc này:')
EQ('‖B_i − E_i‖ = r_e,     i = 1, 2, 3', '2.3')
P('Bài toán động học ngược là biết P tìm θᵢ; bài toán động học thuận là biết θᵢ tìm P. Hình 2.1 '
  'minh họa các đại lượng hình học của một chân.')

IMG('2.1')

H2('2.2. Động học ngược')

H3('2.2.1. Tách bài toán về từng chân')

P('Ba ràng buộc (2.3) độc lập nhau theo θᵢ, nên có thể giải riêng cho từng chân; cách triển '
  'khai dưới đây theo hướng trình bày của Williams [4]. Để công thức của '
  'cả ba chân giống hệt nhau, ta quay điểm P quanh trục Z một góc −φᵢ để đưa về hệ tọa độ cục bộ '
  'của chân đang xét:')
EQ('xᵢ = x₀·cos φᵢ + y₀·sin φᵢ;   yᵢ = −x₀·sin φᵢ + y₀·cos φᵢ;   zᵢ = z₀', '2.4')
P('Trong hệ cục bộ, chân đang xét nằm trong mặt phẳng XZ, khớp chủ động đặt tại (f, 0, 0) và quay '
  'quanh trục Y. Khi đó E_i = (f + r_f·cos θᵢ, 0, −r_f·sin θᵢ) và B_i = (xᵢ + e, yᵢ, zᵢ).')

H3('2.2.2. Thiết lập phương trình lượng giác')

P('Đặt aᵢ = (xᵢ + e) − f là khoảng cách theo phương X từ khớp chủ động tới khớp cầu phía bàn máy. '
  'Thay vào ràng buộc ‖B_i − E_i‖² = r_e² được:')
EQ('(aᵢ − r_f·cos θᵢ)² + yᵢ² + (zᵢ + r_f·sin θᵢ)² = r_e²', '2.5')
P('Khai triển và dùng đồng nhất thức cos²θ + sin²θ = 1, các số hạng bậc hai của θ triệt tiêu và '
  'phương trình trở thành tuyến tính theo sin θᵢ và cos θᵢ:')
EQ('Aᵢ·cos θᵢ + Bᵢ·sin θᵢ + Cᵢ = 0', '2.6')
P('với các hệ số:')
EQ('Aᵢ = −2·r_f·aᵢ;   Bᵢ = 2·r_f·zᵢ;   Cᵢ = aᵢ² + yᵢ² + zᵢ² + r_f² − r_e²', '2.7')

H3('2.2.3. Giải bằng phép thế Weierstrass')

P('Phương trình (2.6) được giải bằng phép thế Weierstrass t = tan(θᵢ/2), khi đó '
  'cos θᵢ = (1 − t²)/(1 + t²) và sin θᵢ = 2t/(1 + t²). Nhân hai vế với (1 + t²) thu được phương '
  'trình bậc hai đối với t:')
EQ('(Cᵢ − Aᵢ)·t² + 2Bᵢ·t + (Aᵢ + Cᵢ) = 0', '2.8')
EQ('t = [−Bᵢ ± √(Aᵢ² + Bᵢ² − Cᵢ²)] / (Cᵢ − Aᵢ);   θᵢ = 2·arctan t', '2.9')
P('Biệt thức Δᵢ = Aᵢ² + Bᵢ² − Cᵢ² mang ý nghĩa hình học rõ ràng:')
B([
    'Δᵢ > 0: hai nghiệm, ứng với hai cấu hình lắp ráp khác nhau của chân;',
    'Δᵢ = 0: hai nghiệm trùng nhau — cánh tay trên và thanh chống duỗi thẳng hàng. Đây là **biên '
    'không gian làm việc** của chân, đồng thời là **điểm kỳ dị** vì tại đó chân mất khả năng '
    'truyền lực theo phương duỗi;',
    'Δᵢ < 0: vô nghiệm — điểm cần tới nằm ngoài tầm với của chân.',
])
P('Trường hợp suy biến Cᵢ − Aᵢ ≈ 0 làm phương trình (2.8) trở thành bậc nhất; chương trình cài đặt '
  'xử lý riêng nhánh này để tránh chia cho số rất nhỏ.')

H3('2.2.4. Chọn nghiệm: tiêu chí khuỷu ra ngoài')

P('Mỗi chân cho hai nghiệm toán học nhưng robot thật chỉ lắp theo một cấu hình: khuỷu tay nằm '
  '**phía ngoài** đoạn nối từ khớp chủ động tới khớp cầu phía bàn máy. Chọn sai nghiệm sẽ cho cấu '
  'hình lắp ngược, không tồn tại trên robot. Tiêu chí chọn nhánh là dấu đạo hàm của vế trái '
  'phương trình ràng buộc theo θᵢ:')
EQ('−Aᵢ·sin θᵢ + Bᵢ·cos θᵢ ≤ 0', '2.10')
P('Đại lượng này tỉ lệ với tích có hướng giữa véc-tơ nối khớp chủ động tới khớp cầu phía bàn máy '
  'và véc-tơ nối khớp chủ động tới khuỷu tay, nên dấu âm tương ứng với khuỷu nằm phía ngoài. Kiểm '
  'chứng tại vị trí gốc: θᵢ = 0 cho −Aᵢ·sin 0 + Bᵢ·cos 0 = Bᵢ = 2·r_f·z₀ < 0 vì z₀ < 0, thỏa mãn.')
P('Sau khi chọn nhánh mới kiểm tra giới hạn khớp; nếu nghiệm khuỷu-ngoài vượt giới hạn thì điểm '
  'đó không với tới được. Thứ tự này quan trọng: tiêu chí ban đầu từng được dự kiến là “lấy nghiệm '
  'nằm trong giới hạn khớp”, nhưng khi quét lưới toàn không gian đã phát hiện những điểm mà xét '
  'riêng một chân thì cả hai nghiệm đều nằm trong giới hạn — ví dụ chân thứ nhất tại x = −0,09 m, '
  'z = −0,02 m cho θ ≈ 0,641 rad và θ ≈ −1,020 rad — nên quy tắc đó không đủ xác định. Tiêu chí '
  'khuỷu-ngoài có cơ sở hình học rõ ràng nên được dùng thay thế; trên 149 769 điểm mà cả ba chân '
  'đều giải được, hai quy tắc cho kết quả hoàn toàn trùng khớp.')

H2('2.3. Động học thuận')

P('Viết lại ràng buộc (2.3) theo P, chuyển số hạng e·u_i sang vế chứa E_i:')
EQ('‖P − C_i‖ = r_e,   với   C_i = E_i − e·u_i', '2.11')
P('Vì θᵢ đã biết nên E_i tính được trực tiếp từ (2.1), do đó C_i là điểm đã biết:')
EQ('C_i = (f + r_f·cos θᵢ − e)·u_i − r_f·sin θᵢ·ẑ', '2.12')
P('Bài toán động học thuận do đó quy về **tìm giao điểm của ba mặt cầu** có tâm C₁, C₂, C₃ và '
  'cùng bán kính r_e — bài toán trilateration quen thuộc trong định vị. Dựng hệ trục phụ trực '
  'chuẩn gốc tại C₁:')
EQ('û = (C₂ − C₁)/d;   v̂ = [(C₃ − C₁) − i·û]/j;   ŵ = û × v̂', '2.13')
P('trong đó d = ‖C₂ − C₁‖, i = û·(C₃ − C₁) và j = ‖(C₃ − C₁) − i·û‖. Vì ba bán kính bằng nhau nên '
  'các số hạng r_e² triệt tiêu, công thức rút gọn đáng kể:')
EQ('p_u = d/2;   p_v = (i² + j² − 2·i·p_u)/(2j);   p_w = ±√(r_e² − p_u² − p_v²)', '2.14')
EQ('P = C₁ + p_u·û + p_v·v̂ + p_w·ŵ', '2.15')
P('Hai giá trị ±p_w đối xứng nhau qua mặt phẳng chứa ba tâm; nghiệm vật lý là nghiệm nằm phía '
  'dưới, tức có tọa độ z nhỏ hơn, vì bàn máy treo dưới đế. Hai trường hợp không hợp lệ cần bắt '
  'lỗi là: r_e² − p_u² − p_v² < 0 (ba mặt cầu không giao nhau, bộ góc khớp không lắp ráp được) và '
  'd ≈ 0 hoặc j ≈ 0 (ba tâm thẳng hàng, cấu hình suy biến).')
P('Vai trò của động học thuận trong hệ điều khiển rất thiết thực: mô phỏng chỉ công bố ba khớp '
  'chủ động qua topic trạng thái khớp, mô phỏng đúng như encoder trên robot thật, nên động học '
  'thuận là **cách duy nhất** để biết bàn máy đang thực sự ở đâu. Nó được dùng để lấy điểm xuất '
  'phát khi sinh quỹ đạo, để kiểm tra điều kiện hút vật và để hiển thị vị trí hiện tại.')

H2('2.4. Không gian làm việc và điểm kỳ dị')

P('Một điểm với tới được khi và chỉ khi **cả ba chân** đều có nghiệm khuỷu-ngoài nằm trong giới '
  'hạn khớp, tức Δᵢ ≥ 0 và θᵢ ∈ [θ_min, θ_max] với mọi i. Bảng 2.2 cho bán kính lớn nhất mà robot '
  'với tới được theo mọi hướng tại từng cao độ, tính bằng chương trình quét lưới.')

T('2.2',
  ['z₀ (m)', '−0,11', '−0,14', '−0,16', '−0,18', '−0,20', '−0,22', '−0,24'],
  [('r_max (m)', '0,138', '0,128', '0,118', '0,105', '0,085', '0,057', '0')],
  widths=[3.0, 1.9, 1.9, 1.9, 1.9, 1.9, 1.9, 1.9])

P('Không gian làm việc có dạng chỏm thu nhỏ dần khi xuống thấp, hội tụ về một điểm tại '
  'z₀ ≈ −0,24 m khi ba chân duỗi hết cỡ. Phía trên z₀ ≈ −0,10 m hầu như không với tới được do '
  'giới hạn khớp. Biên của vùng này chính là tập các điểm có ít nhất một chân đạt Δᵢ = 0, tức là '
  '**biên kỳ dị loại duỗi thẳng**: tại đó bàn máy mất một bậc tự do tức thời và lực cần thiết để '
  'giữ vị trí tăng vọt. Trong điều khiển, cách xử lý đơn giản và an toàn là kiểm tra trước toàn bộ '
  'quỹ đạo và từ chối thực hiện nếu có bất kỳ điểm nào vi phạm — cách làm được áp dụng ở mục 4.3.')

H2('2.5. Quy hoạch quỹ đạo')

P('Ra lệnh cho robot nhảy thẳng tới điểm đích khiến bộ điều khiển khớp nhận bước nhảy vị trí, gây '
  'gia tốc lớn, rung và sai lệch đường đi. Vì vậy quỹ đạo cần được nội suy theo thời gian sao cho '
  'vận tốc và gia tốc liên tục. Đồ án dùng **biên dạng bậc năm** (còn gọi là quỹ đạo giật cực '
  'tiểu, minimum jerk [14]) cho tham số đường đi. Với τ = t/T ∈ [0, 1]:')
EQ('s(τ) = 10τ³ − 15τ⁴ + 6τ⁵', '2.16')
P('Hàm này thỏa mãn s(0) = 0, s(1) = 1, đồng thời đạo hàm bậc nhất và bậc hai bằng không ở cả hai '
  'đầu, nghĩa là robot xuất phát và dừng lại **êm**, không có bước nhảy vận tốc hay gia tốc. Vận '
  'tốc lớn nhất đạt ở giữa đoạn:')
EQ('v_max = 1,875·L/T', '2.17')
P('trong đó L là chiều dài đoạn thẳng và T là thời gian đi hết đoạn. Công thức (2.17) được dùng '
  'ngược lại để chọn T từ vận tốc giới hạn cho trước: T = 1,875·L/v_max.')
P('Với thao tác gắp–thả, đi thẳng từ điểm này sang điểm khác có thể quét ngang qua vật khác. Vì '
  'vậy đồ án dùng **quỹ đạo an toàn ba đoạn**: nâng thẳng đứng lên cao độ an toàn, đi ngang ở cao '
  'độ đó, rồi hạ thẳng đứng xuống đích. Mỗi đoạn vẫn dùng biên dạng bậc năm nên toàn bộ đường đi '
  'trơn tru.')

H2('2.6. Mô hình camera lỗ kim')

P('Camera được mô hình hóa theo mô hình lỗ kim [6]. Một điểm trong không gian có tọa độ X_r trong '
  'hệ robot được đưa về hệ tọa độ camera bằng phép biến đổi cứng gồm ma trận quay R và véc-tơ tịnh '
  'tiến t — gọi là **ngoại tham số**:')
EQ('X_c = R·X_r + t', '2.18')
P('Sau đó điểm được chiếu lên mặt phẳng ảnh bằng ma trận **nội tham số** K:')
EQ('u = f_x·(X_c/Z_c) + c_x;   v = f_y·(Y_c/Z_c) + c_y', '2.19')
P('trong đó f_x, f_y là tiêu cự tính theo đơn vị điểm ảnh, còn (c_x, c_y) là tâm ảnh. Ống kính '
  'thật còn gây **méo hình**, thường mô tả bằng các hệ số méo xuyên tâm k₁, k₂, k₃ và méo tiếp '
  'tuyến p₁, p₂ tác động lên tọa độ chuẩn hóa trước khi nhân với K. Camera mô phỏng trong đồ án là '
  'camera lỗ kim lý tưởng nên các hệ số méo bằng không; khi chuyển sang camera thật, các hệ số này '
  'phải được xác định bằng hiệu chuẩn nội tham số theo phương pháp bàn cờ của Zhang [10].')
P('Điều quan trọng về mặt nguyên lý: phép chiếu (2.19) làm **mất thông tin chiều sâu**. Từ một '
  'điểm ảnh (u, v) chỉ khôi phục được một tia trong không gian, xuất phát từ tâm quang học:')
EQ('X_r(λ) = Rᵀ·(λ·K⁻¹·[u, v, 1]ᵀ − t),   λ > 0', '2.20')
P('Muốn xác định điểm 3D phải có thêm một ràng buộc, và ràng buộc đó trong đồ án là cao độ của '
  'tâm vật (mục 2.9).')

H2('2.7. Bài toán PnP và marker ArUco')

P('Bài toán **PnP** (Perspective-n-Point) là: cho n điểm có tọa độ 3D đã biết trong một hệ tọa độ '
  'và hình chiếu tương ứng của chúng trên ảnh, cùng với nội tham số K, hãy tìm R và t. Đây chính '
  'là bài toán hiệu chuẩn ngoại tham số: xác định camera đang đứng ở đâu và nhìn theo hướng nào so '
  'với hệ tọa độ robot. Nghiệm được tìm bằng cách cực tiểu hóa tổng bình phương sai lệch chiếu '
  'ngược:')
EQ('min Σⱼ ‖π(K, R, t, X_j) − x_j‖²', '2.21')
P('trong đó π là phép chiếu (2.18) – (2.19), X_j là điểm 3D và x_j là điểm ảnh quan sát được. Đồ '
  'án dùng thuật toán **SQPnP** [8] để tìm nghiệm ban đầu rồi tinh chỉnh bằng thuật toán '
  'Levenberg–Marquardt. Sai lệch chiếu ngược RMS sau khi giải là thước đo trực tiếp chất lượng '
  'hiệu chuẩn.')
P('Để có các cặp điểm 3D–2D một cách tin cậy, đồ án dùng **marker ArUco** [7]: các ô vuông đen '
  'trắng mã hóa một số hiệu, được thiết kế sao cho bộ nhận dạng xác định được bốn góc với độ chính '
  'xác dưới một điểm ảnh và đọc được số hiệu ngay cả khi marker bị nghiêng hoặc che một phần. Dán '
  'marker lên bàn tại các vị trí đã đo trước cho ta các điểm 3D chính xác, còn ảnh cho ta các điểm '
  '2D tương ứng.')

H2('2.8. Phân đoạn màu và phép toán hình thái học')

P('Ảnh màu thu được ở dạng ba kênh đỏ, lục, lam. Không gian màu này không tiện cho việc nhận dạng '
  'theo màu vì cả ba kênh đều thay đổi khi độ sáng thay đổi. Vì vậy ảnh được chuyển sang không '
  'gian **HSV**, trong đó H (hue) mã hóa sắc màu, S (saturation) mã hóa độ bão hòa và V (value) '
  'mã hóa độ sáng [15]. Nhờ tách riêng sắc màu khỏi độ sáng, ngưỡng theo H ổn định hơn nhiều khi '
  'vật nằm trong bóng đổ.')
P('Vùng ảnh thuộc một lớp màu được tách bằng phép lấy ngưỡng theo khoảng trên cả ba kênh. Riêng '
  'màu đỏ nằm ở hai đầu của vòng tròn sắc màu nên phải dùng **hai khoảng** rồi hợp lại. Mặt nạ thu '
  'được luôn có nhiễu muối tiêu và lỗ nhỏ, được làm sạch bằng hai phép toán hình thái học: phép '
  '**mở** (co rồi giãn) xóa các đốm nhỏ hơn phần tử cấu trúc, phép **đóng** (giãn rồi co) lấp các '
  'lỗ nhỏ bên trong vùng. Sau đó các vùng liên thông được gắn nhãn và vùng quá nhỏ bị loại bỏ.')
P('Vị trí của vật trên ảnh được lấy bằng **tâm khối** của vùng ảnh, tức trung bình tọa độ của mọi '
  'điểm ảnh thuộc vùng:')
EQ('(ū, v̄) = (1/N)·Σ (u_k, v_k)', '2.22')
P('Cần lưu ý ngay từ đây một đặc điểm sẽ quyết định độ chính xác của cả hệ thống: tâm khối tính '
  'theo (2.22) là tâm của **phần nhìn thấy**, không phải hình chiếu của tâm vật. Khi vật bị che một '
  'phần, hai điểm này lệch nhau và gây sai số hệ thống.')

H2('2.9. Từ điểm ảnh về tọa độ robot')

P('Kết hợp tia nhìn (2.20) với ràng buộc hình học cho phép xác định điểm 3D. Vật nằm trên mặt bàn '
  'có cao độ z_bàn đã biết và có nửa chiều cao h đã biết, nên tâm vật nằm trên mặt phẳng ngang:')
EQ('z = z_bàn + h', '2.23')
P('Giao tia nhìn với mặt phẳng này cho nghiệm duy nhất. Việc chọn đúng mặt phẳng là quan trọng: '
  'nếu lấy giao với mặt bàn thay vì với mặt phẳng đi qua tâm vật thì kết quả lệch đi một đoạn cỡ '
  'h·tan(góc nhìn); với cấu hình của đồ án, sai lệch này khoảng 12 mm, tức là đủ để làm hỏng thao '
  'tác gắp. Trường hợp vật nằm trong khay, mặt phẳng tham chiếu là đáy khay thay vì mặt bàn.')
P('Về độ phân giải: một milimét trên mặt bàn tương ứng khoảng 0,87 điểm ảnh theo phương X và 1,64 '
  'điểm ảnh theo phương Y với cấu hình camera của đồ án. Sự chênh lệch này là do camera nhìn xiên '
  'nên phương X bị nén. Suy ngược lại, sai số một điểm ảnh khi xác định tâm vật tương ứng khoảng '
  '1,15 mm theo X và 0,61 mm theo Y — con số cho thấy độ chính xác của khâu nhận dạng ảnh hưởng '
  'trực tiếp và tuyến tính tới độ chính xác của vị trí vật.')

H2('2.10. Quan hệ vận tốc và ma trận Jacobi')

P('Phần này trình bày quan hệ vận tốc của robot delta. Hệ điều khiển xây dựng trong đồ án làm việc '
  'ở mức vị trí — quỹ đạo được rời rạc hóa thành chuỗi điểm rồi giải động học ngược cho từng điểm '
  '— nên quan hệ vận tốc không được dùng trực tiếp. Tuy nhiên đây là cơ sở lý thuyết cần thiết để '
  'phân tích điểm kỳ dị một cách chặt chẽ và để mở rộng sang điều khiển theo vận tốc ở giai đoạn '
  'sau, nên được đưa vào đây cho đầy đủ.')
P('Lấy đạo hàm theo thời gian hai vế của ràng buộc ‖B_i − E_i‖² = r_e² và đặt '
  'w_i = B_i − E_i là véc-tơ dọc theo thanh chống, ta được:')
EQ('w_iᵀ·(Ṗ − Ė_i) = 0', '2.24')
P('Vận tốc của khuỷu tay chỉ phụ thuộc tốc độ khớp chủ động: Ė_i = θ̇ᵢ·(∂E_i/∂θᵢ), trong đó '
  '∂E_i/∂θᵢ = −r_f·sin θᵢ·u_i − r_f·cos θᵢ·ẑ theo (2.1). Thay vào và viết cho cả ba chân được hệ '
  'phương trình tuyến tính:')
EQ('J_x·Ṗ = J_θ·θ̇', '2.25')
P('với J_x là ma trận 3×3 có hàng thứ i là w_iᵀ, còn J_θ là ma trận đường chéo có phần tử thứ i '
  'bằng w_iᵀ·(∂E_i/∂θᵢ). Khi J_x khả nghịch, ma trận Jacobi của robot là:')
EQ('J = J_x⁻¹·J_θ,   Ṗ = J·θ̇', '2.26')
P('Cấu trúc hai ma trận này cho phép phân loại điểm kỳ dị một cách hệ thống. Khi **det J_θ = 0**, '
  'tức thanh chống vuông góc với phương chuyển động của khuỷu tay ở một chân nào đó, chân đó mất '
  'khả năng truyền chuyển động — đây chính là trạng thái duỗi thẳng hàng ứng với Δᵢ = 0 đã nêu ở '
  'mục 2.2.3, và là biên của không gian làm việc. Khi **det J_x = 0**, tức ba thanh chống trở nên '
  'phụ thuộc tuyến tính, bàn máy có thể chuyển động tức thời mà ba khớp chủ động đứng yên; đây là '
  'kỳ dị nguy hiểm hơn vì robot mất khả năng giữ vị trí. Với cấu hình hình học và giới hạn khớp '
  'của robot khảo sát, loại kỳ dị thứ hai không xuất hiện trong vùng làm việc đã dùng.')
P('Về mặt thực hành, cách xử lý kỳ dị trong đồ án là gián tiếp nhưng hiệu quả: mọi điểm trên quỹ '
  'đạo đều phải giải được động học ngược với nghiệm nằm trong giới hạn khớp thì lệnh mới được thực '
  'hiện (mục 4.3). Điều kiện Δᵢ ≥ 0 bảo đảm quỹ đạo không chạm biên kỳ dị loại duỗi thẳng, còn '
  'biên an toàn thực tế được tạo ra bởi giới hạn khớp vốn chặt hơn điều kiện toán học.')


# ============================================================================ CHƯƠNG 3
H1('Chương 3. XÂY DỰNG HỆ THỐNG MÔ PHỎNG')

P('Chương này trình bày việc dựng môi trường làm việc cho toàn bộ đề tài: mô hình robot mạch động '
  'học kín trong Gazebo, bàn và vật thể, cơ cấu gắp bằng giác hút ảo, camera, cùng kiến trúc phần '
  'mềm điều khiển. Những đặc điểm và hạn chế của mô phỏng được nêu kèm số liệu đo, vì chúng ảnh '
  'hưởng trực tiếp tới cách thiết kế các khối ở chương sau.')

H2('3.1. Kiến trúc tổng thể')

P('Hệ thống gồm ba mảng chạy song song và trao đổi dữ liệu qua ROS 2 (Hình 3.1). Mảng **mô phỏng** '
  'gồm Gazebo với thế giới chứa robot, bàn, vật thể, khay và camera; nó cung cấp ảnh, trạng thái '
  'khớp và vị trí thật của vật. Mảng **thị giác** nhận ảnh, nhận dạng vật và công bố vị trí vật '
  'trong hệ tọa độ robot. Mảng **điều khiển** gồm bộ lập kế hoạch nhiệm vụ, bộ sinh quỹ đạo, bộ '
  'giải động học ngược và node điều khiển giác hút.')

IMG('3.1')

P('Điểm nối giữa thị giác và điều khiển được thiết kế có chủ đích: bộ lập kế hoạch không gọi trực '
  'tiếp hàm xử lý ảnh mà chỉ đọc **vị trí vật** từ một nguồn có thể chọn được. Nguồn đó có thể là '
  'vị trí thật do mô phỏng cung cấp hoặc kết quả của khối thị giác. Nhờ vậy, việc chuyển hệ thống '
  'sang dùng camera — và sau này là camera thật — không đụng chạm tới phần lập kế hoạch và điều '
  'khiển.')

H2('3.2. Mô hình robot mạch động học kín')

P('Định dạng URDF của ROS chỉ mô tả được cấu trúc **cây**, trong khi robot delta có mạch động học '
  '**kín**. Giải pháp được dùng trong mô hình nền là đóng mạch **lúc chạy**: mô hình URDF mô tả ba '
  'chân như ba nhánh cây rời, còn bốn khớp kiểu DetachableJoint của Gazebo sẽ hàn các khâu lại với '
  'nhau sau khi robot được sinh ra trong thế giới mô phỏng. Hệ quả cần nhớ khi chỉnh sửa mô hình: '
  'hai khâu được hàn phải có hệ tọa độ **trùng nhau tại vị trí gốc**, nếu thay đổi hình học mà '
  'không cập nhật vị trí gốc thì mối hàn sẽ bị giật hoặc hỏng.')
P('Trong mô hình, mỗi khớp cầu ở hai đầu thanh chống được biểu diễn bằng chuỗi ba khớp quay, còn '
  'bàn máy treo trên chuỗi ba khớp trượt X–Y–Z bị động nên luôn nằm ngang, đúng với tính chất ba '
  'bậc tự do tịnh tiến đã nêu ở mục 1.1. Ba khớp chủ động được điều khiển bằng bộ điều khiển vị '
  'trí PID của Gazebo, nhận lệnh góc qua ba topic riêng.')
P('Một chi tiết quan trọng về mặt phương pháp: topic trạng thái khớp được cấu hình để **chỉ chứa '
  'ba khớp chủ động**, đúng như encoder trên robot thật chỉ đo được khớp có động cơ. Nhờ vậy hệ '
  'điều khiển buộc phải dùng động học thuận để biết vị trí bàn máy, giống hệt tình huống thật, '
  'thay vì đọc trộm vị trí bàn máy từ mô phỏng.')
P('Về va chạm, chỉ khâu đầu công tác được gắn hình khối va chạm (hộp 50 × 50 × 6 mm); các khâu còn '
  'lại chỉ có hình hiển thị. Đây là lựa chọn có chủ đích để mô phỏng nhẹ và ổn định, nhưng kéo '
  'theo hạn chế: cánh tay và thanh chống đi xuyên qua bàn và vật. Vì vậy quỹ đạo được thiết kế sao '
  'cho chỉ đầu công tác tiếp xúc với vật (mục 4.3).')

H2('3.3. Môi trường làm việc')

P('Thế giới mô phỏng được xây dựng riêng cho đề tài trên cơ sở thế giới gốc, gồm: một mặt bàn nằm '
  'ngang, ba vật thể có màu và hình dạng khác nhau, một khay ba ô để phân loại, sáu marker hiệu '
  'chuẩn dán trên bàn và một camera. Mọi tọa độ trong khóa luận được cho trong **hệ tọa độ robot**, '
  'tức hệ gắn với đế; do đế đặt cao 1 m trong thế giới mô phỏng nên tọa độ hệ robot bằng tọa độ '
  'thế giới trừ đi 1 m theo phương Z. Bảng 3.1 liệt kê các đối tượng chính.')

T('3.1',
  ['Đối tượng', 'Hình dạng', 'Vị trí ban đầu (m)', 'Ghi chú'],
  [
      ('Mặt bàn', 'tấm phẳng', 'z = −0,220', 'Cố định, là mặt phẳng tham chiếu'),
      ('Hộp đỏ', 'hộp 30 mm', '(0,060; 0,000)', 'Tâm vật cao z = −0,205'),
      ('Trụ xanh lá', 'trụ r = 15 mm, cao 30 mm', '(−0,030; 0,052)', 'Tâm vật cao z = −0,205'),
      ('Cầu xanh dương', 'cầu r = 15 mm', '(−0,030; −0,052)', 'Có đế chống lăn vô hình'),
      ('Khay ba ô', 'lòng 70 × 70 mm, thành cao 20 mm', 'tâm (0,0375; 0,065)',
       'Đáy khay z = −0,217'),
      ('Ô thả A / B / C', 'điểm thả', '(0,0205; 0,048) / (0,0545; 0,048) / (0,0205; 0,082)',
       'Cách nhau ≥ 34 mm'),
      ('Sáu marker ArUco', 'ô vuông 50 mm', 'xem Phụ lục A', 'Chỉ có hình hiển thị'),
  ],
  widths=[2.8, 4.2, 5.0, 4.0], size=11)

P('Ba hình dạng khác nhau được chọn có chủ đích để thử thách khối thị giác: hộp có mặt trên phẳng '
  'và cạnh sắc, trụ có mặt bên cong, còn cầu không có mặt phẳng nào — mỗi loại cho hình bóng khác '
  'nhau trên ảnh và cần mô hình dự đoán riêng (mục 5.5).')
P('Quả cầu ban đầu gây một vấn đề đáng ghi nhận: bộ giải va chạm của Gazebo không mô hình hóa ma '
  'sát lăn, nên quả cầu lăn chậm liên tục sau khi được thả, dịch 25 – 51 mm và làm bước kiểm chứng '
  'báo thất bại. Giải pháp được chọn là thêm cho quả cầu một **đế chống lăn vô hình**: một đĩa bán '
  'kính 7 mm, dày 2 mm, nhô dưới đáy 0,5 mm, chỉ có khối va chạm mà không có hình hiển thị. Camera '
  'vẫn nhìn thấy đúng một quả cầu, trong khi vật chỉ đổ khi mặt bàn nghiêng quá 24°. Sau khi sửa, '
  'quả cầu đứng yên suốt 20 s trong ô khay và sai lệch khi đặt lại chỗ cũ giảm còn 2,7 mm.')

H2('3.4. Cơ cấu gắp bằng giác hút ảo')

P('Cơ cấu gắp được mô phỏng theo nguyên lý giác hút: khi đầu công tác chạm vào vật và có lệnh hút, '
  'vật được **hàn** vào đầu công tác; khi có lệnh nhả, mối hàn bị gỡ và vật rơi tự do theo vật lý. '
  'Về kỹ thuật, mỗi vật có một khớp DetachableJoint riêng nối vật với khâu đầu công tác, điều khiển '
  'qua một cặp topic gắn/gỡ riêng.')
P('Việc dùng topic riêng cho từng vật là bắt buộc chứ không phải tùy chọn: bốn khớp DetachableJoint '
  'đóng mạch động học kín của robot dùng chung cặp topic mặc định, nên nếu gửi lệnh gỡ vào cặp '
  'topic đó thì **toàn bộ mạch kín của robot bị tháo rời**. Đây là một trong những lỗi tốn thời '
  'gian nhất khi xây dựng hệ thống và đã được ghi lại trong tài liệu kỹ thuật của dự án.')
P('Một đặc điểm khác của phần mở rộng này là nó **tự động gắn khi khởi động** và không có tùy chọn '
  'tắt. Hậu quả là ngay sau khi mô phỏng chạy, robot bị ba vật đang nằm trên bàn giữ cứng. Node '
  'điều khiển giác hút do đó phải chủ động gửi lệnh gỡ cho tới khi nhận được xác nhận trạng thái '
  '“đã gỡ” trước khi cho phép nhận lệnh.')
P('Điều kiện hút được kiểm tra bằng phần mềm, mô phỏng giới hạn vật lý của giác hút thật: độ lệch '
  'ngang giữa tâm đầu công tác và tâm vật không quá **12 mm**, và khe giữa mặt dưới đầu công tác '
  'với đỉnh vật nằm trong khoảng từ −4 mm tới +6 mm. Nếu không thỏa mãn, dịch vụ hút trả về thất '
  'bại kèm tọa độ gợi ý. Ngưỡng 12 mm chính là dung sai mà khối thị giác phải đáp ứng, như đã nêu '
  'ở mục 1.4.')
P('Điểm thiết kế quan trọng: node điều khiển giác hút **luôn dùng vị trí thật của vật** do mô '
  'phỏng cung cấp, kể cả khi hệ thống đang chạy ở chế độ camera. Lý do là node này mô phỏng **phần '
  'cứng**: trên robot thật, giác hút bám được hay không là kết quả của vật lý chứ không phải của '
  'nhận thức. Việc tách bạch nhận thức khỏi phần cứng giữ cho thí nghiệm ở Chương 6 trung thực: '
  'nếu thị giác ước lượng sai, giác hút sẽ hút trượt đúng như ngoài đời.')

H2('3.5. Camera mô phỏng')

P('Camera được đặt cố định ở phía sau robot nhìn chếch xuống bàn, tại vị trí (−0,400; 0; 0,030) m '
  'trong hệ tọa độ robot, nghiêng xuống 32°. Hướng đặt được chọn nằm giữa chân thứ hai và chân thứ '
  'ba vì ở hướng đó cánh tay robot che tầm nhìn ít nhất. Góc nhìn xiên là một lựa chọn có chủ '
  'đích: camera nhìn thẳng từ trên xuống sẽ bị chính bàn máy che khuất trung tâm vùng làm việc, '
  'còn camera nhìn xiên vẫn thấy được mặt trên và một phần mặt bên của vật — thông tin cần thiết '
  'cho cơ chế khớp mép trên ở mục 5.5. Thông số chi tiết của camera được trình bày ở Bảng 5.2.')
P('Ảnh thu được cho thấy trọn ba vật, khay và bàn máy, đồng thời có **bóng đổ của robot** in lên '
  'mặt bàn. Bóng đổ này không được loại bỏ mà giữ nguyên, vì nó là một thử thách thực tế cho khâu '
  'phân đoạn màu và là lý do các ngưỡng ở mục 5.2 phải được chọn cẩn thận.')

H2('3.6. Kiến trúc phần mềm')

P('Toàn bộ phần mềm tự viết nằm trong một package ROS 2 ngôn ngữ Python. Nguyên tắc tổ chức xuyên '
  'suốt là **tách phần tính toán thuần túy khỏi phần phụ thuộc ROS**: các module động học, quỹ '
  'đạo, điều kiện hút, lập kế hoạch nhiệm vụ, xử lý ảnh và ước lượng vị trí đều không nhập thư '
  'viện ROS, nhờ đó kiểm thử được bằng công cụ kiểm thử đơn vị mà không cần khởi động Gazebo. Các '
  'node chỉ làm nhiệm vụ nối các module đó với topic và dịch vụ (Bảng 3.2).')

T('3.2',
  ['Node', 'Chức năng'],
  [
      ('cartesian_control', 'Giao diện dòng lệnh chính: nhận lệnh của người dùng, sinh quỹ đạo, '
                            'giải động học ngược và phát lệnh khớp; chứa bộ thực thi nhiệm vụ'),
      ('gripper', 'Mô phỏng giác hút: kiểm tra điều kiện hút, gửi lệnh gắn/gỡ và công bố vật '
                  'đang giữ'),
      ('vision', 'Nhận ảnh, nhận dạng vật theo màu, ước lượng vị trí trong hệ tọa độ robot và '
                 'công bố kèm mức độ tin cậy'),
      ('calibrate_camera', 'Hiệu chuẩn ngoại tham số camera bằng marker ArUco, ghi ra tệp cấu hình'),
      ('manual_control', 'Nhập trực tiếp ba góc khớp, dùng khi kiểm tra phần cứng mô phỏng'),
  ],
  widths=[4.0, 12.0], size=11)

P('Các node trao đổi dữ liệu qua những topic và dịch vụ trong Bảng 3.3; sơ đồ kết nối đầy đủ được '
  'cho ở Hình 3.2.')

T('3.3',
  ['Tên', 'Kiểu', 'Vai trò'],
  [
      ('/delta_3dof/ChainN_1/cmd_pos', 'topic', 'Lệnh góc cho ba khớp chủ động'),
      ('/joint_states', 'topic', 'Góc đo được của ba khớp chủ động'),
      ('/side_camera/image', 'topic', 'Ảnh màu từ camera mô phỏng'),
      ('/side_camera/camera_info', 'topic', 'Nội tham số camera'),
      ('/objects/<vật>/odometry', 'topic', 'Vị trí thật của vật (dùng làm đối chứng)'),
      ('/vision/detections', 'topic', 'Kết quả nhận dạng trên ảnh (khung bao, tâm khối)'),
      ('/vision/objects', 'topic', 'Vị trí vật trong hệ tọa độ robot kèm điểm tin cậy'),
      ('/vision/debug_image', 'topic', 'Ảnh chú thích phục vụ theo dõi'),
      ('/gripper/grip, /gripper/release', 'dịch vụ', 'Ra lệnh hút và nhả'),
      ('/gripper/held_object', 'topic', 'Tên vật đang giữ (lưu trạng thái cuối)'),
  ],
  widths=[6.0, 2.2, 7.8], size=11)

IMG('3.2')

P('Hai bài học kỹ thuật thu được khi xây dựng phần này đáng được nêu vì chúng lặp lại ở nhiều hệ '
  'thống ROS. Thứ nhất, topic lệnh khớp không lưu lịch sử, nên lệnh phát ra **trước khi** phía '
  'nhận kịp đăng ký sẽ mất hoàn toàn; giải pháp là chờ cho tới khi có ít nhất một bên đăng ký rồi '
  'mới gửi. Thứ hai, các giá trị trạng thái quan trọng như “vật đang giữ” phải được công bố ở chế '
  'độ lưu trạng thái cuối, nếu không một node vừa khởi động sẽ hiểu nhầm là chưa giữ vật nào.')

H2('3.7. Tương tác vật lý và hạn chế đã đo được')

P('Trước khi xây dựng thao tác gắp–thả, hành vi va chạm của đầu công tác được đo riêng để biết mô '
  'phỏng đáng tin tới đâu. Kết quả: khi đứng yên tại vị trí gốc, cao độ ổn định tới 0,1 mm; khi '
  'đẩy ngang hộp đỏ, hộp dịch chuyển đúng như tính toán (từ 0,060 m tới 0,069 m so với dự kiến '
  '0,070 m); khi ép xuống mặt bàn tĩnh, đầu công tác bị chặn đúng tại z = −0,217 m và không rung.')
P('Tuy nhiên, khi ép đầu công tác xuống một **vật động đang nằm trên bàn**, đầu công tác lún dần '
  'vào vật khoảng 5 – 8 mm. Hiện tượng xảy ra với cả ba hình dạng vật và vẫn còn khi thay hình '
  'dạng của bàn máy, nên không phải do cặp tiếp xúc trụ–trụ. Nguyên nhân được nghi là vật nhẹ 50 g '
  'bị kẹp giữa lực lớn của bộ điều khiển PID và mặt bàn, khiến bộ giải tiếp xúc không hội tụ; giả '
  'thuyết này **chưa được kiểm chứng**. Hệ quả thực tế được rút ra và áp dụng cho toàn bộ phần sau: '
  'khi gắp, robot chỉ hạ tới đúng đỉnh vật rồi hút, **không bao giờ ra lệnh xuống thấp hơn đỉnh '
  'vật**.')
P('Hiện tượng trên cũng cho thấy giới hạn chung của mô phỏng động lực học. Thế giới mô phỏng dùng '
  'bộ giải va chạm theo phương pháp lặp kiểu Gauss–Seidel chiếu; phương pháp này giải quyết tốt '
  'các tiếp xúc rời rạc nhưng hội tụ chậm khi nhiều ràng buộc tiếp xúc chồng lên nhau, đúng như '
  'trường hợp vật nhẹ bị kẹp giữa hai bề mặt cứng. Vì vậy mọi kết luận về **vị trí** trong khóa '
  'luận đều đáng tin — chúng được kiểm chứng bằng phép đo trực tiếp — còn các kết luận liên quan '
  'tới **lực tiếp xúc** thì cần được xem là đặc thù của mô phỏng, phải kiểm chứng lại trên hệ '
  'thống thật.')
P('Một hệ quả thiết kế được rút ra và áp dụng nhất quán: hệ thống không bao giờ dựa vào tiếp xúc '
  'để định vị. Robot không ép xuống để “dò” mặt bàn hay đỉnh vật, mà luôn tính trước cao độ cần '
  'tới từ thông số hình học đã biết và vị trí vật đo được. Cách làm này vừa tránh được vùng hành '
  'vi kém tin cậy của mô phỏng, vừa đúng với nguyên tắc làm việc của giác hút thật.')

H2('3.8. Quy trình thay đổi môi trường mô phỏng')

P('Môi trường mô phỏng được tổ chức sao cho việc thêm hoặc sửa vật thể là thao tác có quy trình rõ '
  'ràng, vì đây là việc sẽ phải làm lại khi chuyển sang bàn thật. Thông tin về cảnh được mô tả ở '
  'ba nơi, và cả ba phải khớp nhau:')
N([
    'Tệp mô tả thế giới của Gazebo: hình dạng, khối lượng, vị trí ban đầu của vật và bộ công bố vị '
    'trí thật đi kèm.',
    'Tệp mô tả robot: một khớp gắn/gỡ riêng cho mỗi vật để giác hút ảo làm việc được với vật đó.',
    'Module mô tả cảnh phía phần mềm điều khiển: tên vật, nửa chiều cao, tên gọi tắt khi nhập '
    'lệnh, vị trí ban đầu, màu, hình dạng và nửa bề rộng.',
])
P('Module thứ ba đóng vai trò **nguồn thông tin duy nhất** cho toàn bộ phía phần mềm: tệp khởi '
  'động, node giác hút, bộ lập kế hoạch và khối thị giác đều đọc từ đó. Nhờ vậy, khi đổi kích '
  'thước hay vị trí của một vật, không có chỗ nào trong chương trình còn giữ giá trị cũ. Riêng '
  'phần mô tả phía Gazebo vẫn phải sửa thủ công cho khớp, và đây là điểm cần chú ý nhất khi bảo '
  'trì hệ thống.')
P('Cách tổ chức này cũng chính là cơ sở cho bản sao số: khi chuyển sang bàn thật, chỉ cần cập nhật '
  'module mô tả cảnh theo kích thước và vị trí đo được trên bàn thật, còn toàn bộ logic lập kế '
  'hoạch, kiểm tra chỗ đặt và ước lượng hình bóng vật vẫn giữ nguyên.')

H2('3.9. Hiệu năng thời gian thực')

P('Mô phỏng có camera nặng hơn đáng kể so với mô phỏng thuần cơ khí. Hệ số thời gian thực (RTF) — '
  'tỉ số giữa thời gian mô phỏng và thời gian thực — được đo ở nhiều cấu hình (Bảng 3.4) vì bộ '
  'sinh quỹ đạo phát điểm theo đồng hồ thực, nên RTF thấp làm quỹ đạo bị bám kém.')

T('3.4',
  ['Cấu hình (thế giới có camera)', 'RTF'],
  [
      ('Đồ họa tích hợp, có cửa sổ hiển thị', '≈ 0,35'),
      ('Đồ họa tích hợp, không cửa sổ', '≈ 0,94'),
      ('Card rời, có cửa sổ, trước khi sửa tải CPU', '0,56'),
      ('Card rời, có cửa sổ, sau khi sửa tải CPU', '0,77'),
      ('Như trên, ở chế độ hiệu năng cao', '0,76 – 0,99'),
  ],
  widths=[11.0, 5.0], size=11)

P('Hai nguyên nhân gây tải CPU đã được tìm ra và sửa; cả hai đều là bài học chung khi làm việc với '
  'ROS 2 và Gazebo:')
N([
    'Gazebo công bố đồng hồ mô phỏng ở **mỗi bước tính**, khoảng 2000 lần mỗi giây. Node giác hút '
    'ban đầu được cấu hình dùng đồng hồ mô phỏng nên phải xử lý toàn bộ luồng thông điệp đó và '
    'chiếm 103% một lõi CPU; sau khi bỏ cấu hình này, mức chiếm dụng còn 21%.',
    'Bộ công bố trạng thái khớp của Gazebo không có tùy chọn giảm tần số, cũng phát khoảng 2000 '
    'thông điệp mỗi giây. Giải pháp là chèn một node tiết lưu để hạ xuống 100 Hz trước khi đưa vào '
    'hệ điều khiển; mức chiếm dụng CPU của node điều khiển giảm từ 88% xuống 14%.',
])
P('Sau khi sửa, mô phỏng chạy đủ nhanh để toàn bộ thí nghiệm ở Chương 7 được thực hiện với hành vi '
  'ổn định và lặp lại được.')

# ============================================================================ CHƯƠNG 4
H1('Chương 4. ĐIỀU KHIỂN ĐỘNG HỌC VÀ THAO TÁC GẮP–THẢ')

P('Chương này trình bày phần điều khiển: cài đặt công thức động học thành chương trình, sinh quỹ '
  'đạo trơn và an toàn, thực hiện thao tác gắp–thả, và xây dựng lớp lệnh cấp cao có khả năng tự '
  'kiểm chứng kết quả. Đây là nền tảng mà khối thị giác ở Chương 5 sẽ nối vào.')

H2('4.1. Cài đặt động học')

P('Toàn bộ công thức ở mục 2.2 và 2.3 được cài đặt trong một module Python thuần, không phụ thuộc '
  'ROS, gồm: cấu trúc dữ liệu chứa thông số hình học và giới hạn khớp; hàm giải một chân; hàm động '
  'học ngược trả về ba góc khớp hoặc báo lỗi “ngoài tầm với”; hàm động học thuận bằng giao ba mặt '
  'cầu; và các hàm phụ tính vị trí khuỷu tay, vị trí khớp cầu phía bàn máy phục vụ kiểm chứng.')
P('Cách tổ chức này cho phép kiểm thử toàn bộ phần toán học bằng công cụ kiểm thử đơn vị mà không '
  'cần khởi động mô phỏng, nên mỗi lần sửa đổi chỉ mất vài giây để biết có làm hỏng gì không. Kết '
  'quả kiểm thử được trình bày ở mục 7.2.')

H2('4.2. Node điều khiển theo tọa độ Descartes')

P('Node điều khiển chính cung cấp giao diện dòng lệnh để người vận hành nhập trực tiếp tọa độ đích '
  '(x, y, z). Node giải động học ngược, sinh quỹ đạo và phát lần lượt các điểm góc khớp theo chu '
  'kỳ định trước. Ngoài ra node còn có các lệnh phụ trợ: đọc vị trí hiện tại bằng động học thuận, '
  'đổi vận tốc giới hạn, gửi thẳng góc khớp để so sánh, và các lệnh gắp–thả ở mục 4.5. Tham số '
  'chính được cho ở Bảng 4.1.')

T('4.1',
  ['Tham số', 'Giá trị mặc định', 'Ý nghĩa'],
  [
      ('max_speed', '0,05 m/s', 'Vận tốc lớn nhất của bàn máy, dùng để chọn thời gian đoạn'),
      ('rate_hz', '50 Hz', 'Tần số phát điểm quỹ đạo'),
      ('safe_z', '−0,16 m', 'Cao độ đi ngang khi không giữ vật'),
      ('safe_z_holding', '−0,14 m', 'Cao độ đi ngang khi đang giữ vật'),
      ('object_source', 'camera', 'Nguồn vị trí vật: camera hoặc vị trí thật'),
  ],
  widths=[3.6, 3.4, 9.0], size=11)

P('Hai quyết định thiết kế trong node này xuất phát từ lỗi thực tế gặp phải. Thứ nhất, **điểm xuất '
  'phát của quỹ đạo là vị trí đo được** — kết quả động học thuận của góc khớp hiện tại — chứ không '
  'phải điểm đích của lệnh trước đó. Nhờ vậy quỹ đạo vẫn liên tục ngay cả khi robot bị vật chắn '
  'không tới được đích lần trước. Thứ hai, vòng phát điểm quỹ đạo và hàm chờ nhập lệnh đều là các '
  'thao tác chặn, nên phần xử lý thông điệp của ROS được chạy trên một luồng riêng; đồng thời bộ '
  'xử lý tín hiệu mặc định được tắt để phím dừng chỉ hủy quỹ đạo đang chạy mà không tắt cả node.')

H2('4.3. Sinh quỹ đạo an toàn')

P('Bộ sinh quỹ đạo là một module Python thuần, nhận điểm đầu, điểm cuối và trả về danh sách các '
  'điểm trung gian theo biên dạng bậc năm (2.16). Thời gian của đoạn được chọn từ vận tốc giới hạn '
  'theo (2.17). Với thao tác gắp–thả, quỹ đạo an toàn ba đoạn nâng – đi ngang – hạ được dùng, với '
  'cao độ đi ngang khác nhau tùy robot có đang giữ vật hay không, vì khi giữ vật thì vật nhô thêm '
  'xuống dưới đầu công tác.')
P('Một cơ chế an toàn quan trọng là **kiểm tra trước toàn tuyến**: bộ sinh quỹ đạo giải động học '
  'ngược cho **mọi** điểm của quỹ đạo trước khi phát điểm đầu tiên. Nếu có bất kỳ điểm nào ngoài '
  'tầm với — kể cả điểm nằm giữa đường trong khi hai đầu đều hợp lệ — lệnh bị từ chối và robot '
  'không hề di chuyển. Cách này tránh được tình huống nguy hiểm nhất: robot dừng giữa chừng trong '
  'khi đang giữ vật.')

H2('4.4. Thao tác gắp và thả')

P('Thao tác gắp gồm ba bước: đi theo quỹ đạo an toàn tới điểm chạm, gọi dịch vụ hút, rồi nâng '
  'thẳng đứng lên cao độ an toàn. Điểm chạm được tính từ vị trí vật: tâm đầu công tác đặt tại '
  'đỉnh vật cộng thêm nửa bề dày đầu công tác (3 mm), đúng theo kết luận ở mục 3.7 là không hạ '
  'thấp hơn đỉnh vật.')
P('Thao tác thả gồm: mang vật tới điểm nhả, gọi dịch vụ nhả, rồi lùi thẳng lên. Điểm nhả được tính '
  'sao cho đáy vật cách mặt đỡ 5 mm khi nhả, nghĩa là vật rơi một đoạn rất ngắn, đủ để không kẹt '
  'mà không đủ để nảy ra khỏi ô. Với ô khay, mặt đỡ là đáy khay; với thao tác đặt ra bàn, mặt đỡ '
  'là mặt bàn.')

H2('4.5. Lớp lệnh cấp cao và cơ chế tự kiểm chứng')

P('Trên nền các thao tác cơ bản, một lớp lệnh cấp cao được xây dựng để người vận hành ra lệnh theo '
  'ngôn ngữ nhiệm vụ thay vì theo tọa độ (Bảng 4.2). Lớp này gồm hai phần tách biệt: bộ **lập kế '
  'hoạch** thuần túy, biến một lệnh thành chuỗi thao tác Di chuyển – Hút – Nhả dựa trên vị trí vật '
  'hiện tại; và bộ **thực thi**, chạy từng thao tác rồi kiểm chứng kết quả.')

T('4.2',
  ['Lệnh', 'Ý nghĩa'],
  [
      ('vat', 'Liệt kê vị trí và trạng thái của từng vật (trên bàn, trong ô nào, đang giữ)'),
      ('den <vật>', 'Đưa đầu công tác tới phía trên vật'),
      ('nhat <vật>', 'Gắp vật'),
      ('tha [ô]', 'Thả vật đang giữ vào ô chỉ định hoặc ô trống đầu tiên'),
      ('chuyen <vật> [ô]', 'Gắp rồi thả vào khay, có kiểm tra ô trống trước khi gắp'),
      ('don', 'Dọn lần lượt mọi vật còn trên bàn vào các ô trống'),
      ('lay_ra <vật> [x y]', 'Lấy vật từ khay đặt trở lại bàn'),
      ('reset', 'Đưa mọi vật trong khay về đúng vị trí ban đầu'),
      ('nguon camera | that', 'Chọn nguồn vị trí vật'),
  ],
  widths=[5.0, 11.0], size=11)

P('Nguyên tắc thiết kế quan trọng nhất của lớp này là **không tin rằng thao tác đã thành công mà '
  'phải kiểm chứng**. Sau khi gắp, hệ thống kiểm tra vật đã thực sự được nhấc lên ít nhất 10 mm. '
  'Sau khi thả, hệ thống kiểm tra vật có nằm trong đúng ô yêu cầu không. Lệnh đặt vật ra bàn kiểm '
  'tra sai lệch so với điểm đặt không quá 10 mm. Nhờ cơ chế này, một thao tác hỏng được phát hiện '
  'ngay thay vì âm thầm làm hỏng các bước sau — và chính cơ chế này đã bắt được lỗi che khuất ở '
  'Chương 6.')
P('Ngoài ra, mọi điều kiện có thể kiểm tra trước đều được kiểm tra **trước khi robot chạm vào '
  'vật**: ô đích còn trống không, điểm đặt có chồng lên khay hoặc quá gần vật khác không, mọi điểm '
  'trên quỹ đạo có trong tầm với không. Triết lý chung là thà từ chối lệnh còn hơn dừng giữa chừng '
  'khi đang giữ vật.')

H2('4.6. Kiểm chứng phần điều khiển trên mô phỏng')

P('Quỹ đạo thực tế của đầu công tác được ghi lại từ mô phỏng ở tần số cao và so với quỹ đạo lý '
  'thuyết (Bảng 4.3). Kết quả cho thấy quỹ đạo nội suy bám đường thẳng tốt hơn rõ rệt so với việc '
  'gửi thẳng góc khớp, và quỹ đạo an toàn giữ được cao độ đi ngang như thiết kế.')

T('4.3',
  ['Phép đo', 'Kết quả'],
  [
      ('Vị trí đọc bằng động học thuận so với vị trí thật trong mô phỏng', 'lệch 0,1 mm'),
      ('Đi từ vị trí gốc tới trên hộp đỏ, gửi thẳng góc khớp', 'lệch đường thẳng tối đa 4,5 mm'),
      ('Cùng đoạn trên, dùng quỹ đạo nội suy', 'lệch đường thẳng tối đa 2,5 mm'),
      ('Quỹ đạo an toàn ba đoạn', 'lệch tối đa 4,4 mm; cao độ đi ngang thấp nhất −0,1611 m '
                                  '(thiết kế −0,16 m)'),
      ('Dừng khẩn cấp giữa quỹ đạo', 'Robot dừng, node vẫn hoạt động bình thường'),
  ],
  widths=[9.5, 6.5], size=11)

P('Thao tác gắp–thả hoàn chỉnh cũng được kiểm chứng: robot gắp được cả ba vật và thả vào ba ô '
  'khay, cả ba nằm đúng trên đáy khay ở cao độ −0,202 m; lệnh hút khi chưa chạm vật bị từ chối kèm '
  'gợi ý tọa độ; sau khi thao tác xong, robot trở về vị trí gốc vẫn chính xác (−0,1410 m so với '
  'giá trị lý thuyết −0,1405 m). Lệnh dọn ba vật vào khay mất khoảng 28 s, lệnh đưa mọi vật trở về '
  'chỗ cũ chạy trọn vẹn với sai lệch dưới 1 mm cho hộp và trụ.')


# ============================================================================ CHƯƠNG 5
H1('Chương 5. XÂY DỰNG KHỐI THỊ GIÁC MÁY TÍNH')

P('Chương này là nội dung trọng tâm của đề tài: xây dựng chuỗi xử lý biến ảnh camera thành vị trí '
  'vật trong hệ tọa độ robot, đủ chính xác để robot gắp được. Chuỗi gồm bốn khâu — nhận dạng vật '
  'trên ảnh, hiệu chuẩn camera, chuyển tọa độ, và ước lượng có xét che khuất — được trình bày lần '
  'lượt kèm theo cách kiểm chứng riêng của từng khâu.')

H2('5.1. Cấu trúc khối thị giác và thông số camera')

P('Khối thị giác được cài đặt thành một node ROS 2 đọc ảnh từ camera và công bố hai kết quả: kết '
  'quả nhận dạng trên ảnh (khung bao và tâm khối theo điểm ảnh) và vị trí vật trong hệ tọa độ '
  'robot kèm một điểm số thể hiện mức độ tin cậy. Nội dung tính toán đặt trong các module Python '
  'thuần: một module nhận dạng màu, một module mô hình camera và một module ước lượng vị trí. Nhờ '
  'vậy toàn bộ khối được kiểm thử bằng ảnh tĩnh lưu sẵn, không cần chạy mô phỏng.')

T('5.1',
  ['Thông số', 'Giá trị'],
  [
      ('Độ phân giải', '640 × 480 điểm ảnh'),
      ('Góc nhìn ngang', '45°'),
      ('Tiêu cự quy đổi f_x, f_y', '≈ 772,5 điểm ảnh'),
      ('Tâm ảnh (c_x, c_y)', '(320; 240) điểm ảnh'),
      ('Tần số khung hình', '10 Hz'),
      ('Vị trí thật (hệ robot)', '(−0,400; 0,000; 0,030) m'),
      ('Góc nghiêng xuống', '32° (0,5586 rad)'),
      ('Hệ số méo', 'bằng không (camera lỗ kim lý tưởng)'),
  ],
  widths=[7.0, 9.0], size=11)

P('Cần nêu rõ một hạn chế của công cụ mô phỏng đã được kiểm chứng: khai báo nhiễu cảm biến trong '
  'tệp mô tả thế giới **không có tác dụng** — đo giữa hai khung hình liên tiếp chỉ có 0,4% số điểm '
  'ảnh thay đổi giá trị. Nói cách khác, ảnh mô phỏng gần như sạch tuyệt đối. Hệ quả về phương pháp: '
  'muốn đánh giá độ bền của thuật toán với nhiễu thì phải **tự thêm nhiễu bằng phần mềm**, như '
  'được làm ở mục 7.5.')

H2('5.2. Nhận dạng vật thể theo màu')

P('Ba vật trong cảnh có ba màu khác hẳn nhau, nên phân đoạn theo màu là cách nhận dạng đơn giản và '
  'nhanh nhất. Chuỗi xử lý gồm năm bước: chuyển ảnh sang không gian HSV; lấy ngưỡng theo khoảng '
  'cho từng lớp màu; làm sạch mặt nạ bằng phép mở rồi phép đóng; gắn nhãn vùng liên thông và loại '
  'các vùng nhỏ hơn 30 điểm ảnh; cuối cùng tính tâm khối và khung bao.')
P('Việc chọn ngưỡng (Bảng 5.2) phải tính tới hai nguồn gây nhầm trong cảnh: mặt bàn có độ bão hòa '
  'khoảng 77 và đáy khay khoảng 20, nên ngưỡng bão hòa được đặt ở 90 – 100 để loại cả hai; hộp đỏ '
  'khi nằm trong bóng đổ của robot có độ sáng chỉ khoảng 95, nên ngưỡng độ sáng phải hạ xuống 40. '
  'Khay màu cam và bàn máy màu vàng có sắc màu lần lượt khoảng 20 và 29 nên không rơi vào khoảng '
  'nào trong ba lớp màu đang dùng.')

T('5.2',
  ['Lớp màu', 'Khoảng H (0 – 180)', 'S tối thiểu', 'V tối thiểu'],
  [
      ('Đỏ', '[0; 8] ∪ [172; 180]', '100', '40'),
      ('Xanh lá', '[45; 85]', '90', '40'),
      ('Xanh dương', '[95; 125]', '90', '40'),
  ],
  widths=[4.0, 5.5, 3.2, 3.3], size=11)

P('Một quyết định thiết kế quan trọng: mọi mảnh cùng màu được **gộp thành một vật duy nhất**, vì '
  'trong cảnh mỗi màu chỉ ứng với đúng một vật. Nhờ vậy, khi một vật bị bàn máy cắt đôi trên ảnh, '
  'hệ thống vẫn báo một vật thay vì hai. Số mảnh được giữ lại như một dấu hiệu cho biết vật có bị '
  'chia cắt hay không.')
P('Hiệu quả nhận dạng đo trên mô phỏng: thời gian xử lý khoảng 12 ms mỗi khung hình; trong một '
  'lượt chạy đầy đủ gồm lệnh dọn và lệnh đặt lại (607 khung hình), 99,5% số khung thấy đủ cả ba '
  'vật, 0,5% còn lại thiếu trụ xanh do bị bàn máy che kín. Ở lượt chạy khác dài hơn (1 117 khung), '
  'tỉ lệ thấy đủ ba vật là 98,6%. Những khung thiếu vật đều rơi đúng vào lúc bàn máy che vật — dấu '
  'hiệu đầu tiên cho thấy che khuất, chứ không phải ngưỡng màu, mới là vấn đề chính.')

H2('5.3. Hiệu chuẩn ngoại tham số camera')

P('Nhận dạng được vật trên ảnh mới chỉ cho tọa độ điểm ảnh. Muốn biết vật nằm ở đâu trong hệ tọa '
  'độ robot thì phải biết camera đứng ở đâu và nhìn theo hướng nào, tức phải xác định R và t trong '
  '(2.18). Có hai cách: đọc trực tiếp vị trí camera từ tệp mô tả thế giới, hoặc hiệu chuẩn bằng '
  'ảnh. Đồ án chọn cách thứ hai, dù cách thứ nhất dễ hơn nhiều, vì ba lý do: đó là cách duy nhất '
  'khả thi với camera thật; nó cho phép **đo sai số hiệu chuẩn** bằng cách so với giá trị thật; và '
  'quy trình xây dựng được sẽ dùng lại nguyên vẹn khi lắp camera thật.')
P('Phương pháp là dán sáu marker ArUco thuộc từ điển DICT_4X4_50, ô đen cạnh 50 mm, lên mặt bàn '
  'tại sáu vị trí đã biết trước, trải rộng quanh vùng làm việc để bài toán PnP có điều kiện tốt. '
  'Các marker chỉ có hình hiển thị, không có khối va chạm, nên không ảnh hưởng tới chuyển động của '
  'robot. Bố trí marker trong mô phỏng được thiết kế đúng bằng bố trí sẽ in ra giấy dán lên bàn '
  'thật, đúng tinh thần bản sao số.')
P('Quy trình hiệu chuẩn: node hiệu chuẩn thu 20 khung hình, nhận dạng marker với chế độ tinh chỉnh '
  'góc theo đường bao, lấy **tâm marker** làm điểm tương ứng, giải PnP rồi ghi kết quả ra tệp cấu '
  'hình để node thị giác nạp lại (Hình 5.1).')

IMG('5.1')

P('Ba lựa chọn kỹ thuật trong bước này đều xuất phát từ kiểm chứng bằng số chứ không từ suy đoán:')
N([
    'Dùng **tâm marker** thay vì bốn góc: tâm được tính bằng giao điểm hai đường chéo, vì đó mới '
    'là ảnh đúng của tâm hình vuông dưới phép chiếu phối cảnh; lấy trung bình bốn góc sẽ lệch khi '
    'nhìn xiên. Dùng tâm cũng khiến kết quả không phụ thuộc chiều dán marker.',
    'Dùng thuật toán **SQPnP** kèm tinh chỉnh Levenberg–Marquardt thay vì thuật toán IPPE dành cho '
    'điểm đồng phẳng: IPPE tuy đạt kết quả đúng trên dữ liệu tổng hợp nhưng trên ảnh thật lại cho '
    'nghiệm sai với sai lệch chiếu ngược tới 434 điểm ảnh, trong khi SQPnP cho 0,29 điểm ảnh. Đây '
    'là ví dụ điển hình cho thấy phải kiểm chứng thuật toán trên dữ liệu thật.',
    'Lấy trung bình trên 20 khung hình để giảm ảnh hưởng của sai số nhận dạng góc marker.',
])

T('5.3',
  ['Chỉ tiêu', 'Kết quả'],
  [
      ('Sai lệch chiếu ngược RMS', '0,14 điểm ảnh'),
      ('Sai lệch vị trí camera so với giá trị thật', '0,35 mm'),
      ('Sai lệch hướng nhìn so với giá trị thật', '0,017°'),
      ('Số marker sử dụng', '6 (số hiệu 0 – 5)'),
      ('Số khung hình', '20'),
  ],
  widths=[9.0, 7.0], size=11)

P('Kết quả ở Bảng 5.3 cho thấy hiệu chuẩn đạt độ chính xác dưới milimét. Trong quá trình phân tích '
  'còn phát hiện một chi tiết nhỏ: tâm marker đo được lệch so với dự đoán khoảng 0,5 điểm ảnh và '
  'lệch cùng một chiều ở mọi marker. Nguyên nhân được nghi là quy ước tâm điểm ảnh khác nhau giữa '
  'công cụ mô phỏng và thư viện xử lý ảnh (320 so với 319,5) nhưng **chưa được kiểm chứng**; dù '
  'sao, phép giải PnP đã tự bù phần lớn độ lệch này, phần còn lại khoảng 0,4 mm.')

H2('5.4. Chuyển tọa độ ảnh sang tọa độ robot')

P('Với mô hình camera đã hiệu chuẩn, tâm khối của vật trên ảnh được đổi thành tia nhìn theo (2.20) '
  'rồi giao với mặt phẳng nằm ngang đi qua tâm vật theo (2.23). Node thị giác công bố kết quả dưới '
  'dạng danh sách vật kèm tọa độ trong hệ tọa độ robot (Hình 5.2).')

IMG('5.2')

P('Kiểm tra nhanh với ba vật ở vị trí ban đầu cho sai lệch lần lượt 0,5 mm, 0,7 mm và 1,1 mm so '
  'với vị trí thật. Để khẳng định mô hình chiếu là đúng, một phép kiểm chứng độc lập đã được thực '
  'hiện: chiếu tâm 3D thật của vật lên ảnh bằng mô hình camera rồi so với tâm khối nhận dạng được. '
  'Hai điểm cách nhau 0,7 – 1,2 điểm ảnh, nghĩa là với vật có chiều cao xấp xỉ bề rộng, tâm của '
  'phần nhìn thấy gần trùng với hình chiếu của tâm vật khi vật không bị che.')
P('Phép kiểm chứng này cũng xác nhận tầm quan trọng của việc chọn đúng mặt phẳng: nếu vô ý giao '
  'tia nhìn với mặt bàn thay vì với mặt phẳng qua tâm vật, sai số lên tới khoảng 12 mm — đúng bằng '
  'dung sai của giác hút, nghĩa là thao tác gắp sẽ hỏng. Một trường hợp kiểm thử tự động đã được '
  'viết riêng để phát hiện lỗi này nếu ai đó sửa nhầm mã nguồn về sau.')

H2('5.5. Ước lượng vị trí có xét che khuất')

P('Các phép đo hệ thống ở mục 7.4 cho thấy nguồn sai số lớn duy nhất còn lại là **che khuất một '
  'phần**. Nguyên nhân đã nêu ở mục 2.8: tâm khối là tâm của phần nhìn thấy. Khi vật bị che, sai '
  'số xuất hiện theo hướng nhìn của camera và có dấu phụ thuộc phần nào bị che:')
B([
    'vật nằm **sau bàn máy** (vùng xa, x ≥ 90 mm): phần trên bị che nên tâm khối dịch xuống dưới, '
    'ước lượng ra gần camera hơn thật tới 19 mm;',
    'vật nằm **trong khay**: thành khay phía trước che nửa dưới nên tâm khối dịch lên trên, ước '
    'lượng ra xa hơn thật 12 – 20 mm — vượt dung sai giác hút, tức là lệnh lấy vật khỏi khay sẽ '
    'hút trượt;',
    'vật bị **cắt bởi mép ảnh** (góc gần camera): sai số trung bình 8,2 mm.',
])
P('Để xử lý, đồ án xây dựng một bộ ước lượng dựa trên **hình bóng dự đoán**. Ý tưởng: vì đã biết '
  'hình dạng và kích thước của vật (hộp, trụ hoặc cầu) và đã hiệu chuẩn camera, có thể tính trước '
  'vật sẽ hiện lên ảnh như thế nào nếu nó đứng ở một vị trí giả định. Cụ thể, lấy một tập điểm '
  'trên bề mặt vật, chiếu tất cả lên ảnh rồi lấy bao lồi — với vật lồi, bao lồi của ảnh các điểm '
  'bề mặt chính là hình bóng. Kiểm chứng cho thấy vật không bị che có tỉ lệ diện tích nhìn thấy '
  'trên diện tích hình bóng dự đoán xấp xỉ 0,99, nghĩa là mô hình hình bóng khớp với thực tế.')
P('Từ hình bóng dự đoán, hai cơ chế được xây dựng.')

H3('5.5.1. Khớp mép trên cho vật nằm trong khay')

P('Vì camera nhìn chếch từ trên xuống nên **mặt trên của vật trong khay luôn lộ ra**, chỉ phần '
  'dưới bị thành khay che. Do đó thay vì dùng tâm khối, hệ thống khớp hai đại lượng ổn định: tọa '
  'độ mép trên của vùng ảnh và hoành độ tâm ngang của hình bóng. Bài toán trở thành hệ hai phương '
  'trình hai ẩn (x, y) với giả thiết tâm vật nằm ở cao độ đáy khay cộng nửa chiều cao vật, và được '
  'giải bằng phương pháp Newton.')
P('Cơ chế chỉ được kích hoạt khi ước lượng thô rơi vào lân cận khay (trong phạm vi thành ngoài '
  'cộng 30 mm) và kết quả khớp phải nằm trong lòng khay thì mới được chấp nhận; nếu không, hệ '
  'thống giữ nguyên kết quả tâm khối. Nhờ điều kiện kép này, trên toàn bộ bộ dữ liệu đánh giá cơ '
  'chế kích hoạt đúng 9/9 lần cho vật trong khay và **không lần nào** kích hoạt nhầm cho vật trên '
  'bàn. Sai số với vật trong khay giảm từ trung bình 13,4 mm xuống **1,0 mm**, lớn nhất từ 19,7 mm '
  'xuống 1,9 mm.')

H3('5.5.2. Cờ tin cậy')

P('Không phải trường hợp che khuất nào cũng sửa được. Khi vật bị bàn máy che phần trên, hệ thống '
  'không có cách nào biết phần bị che rộng bao nhiêu, nên không thể khôi phục vị trí đúng. Với các '
  'trường hợp đó, giải pháp đúng đắn là **thừa nhận không biết** thay vì đưa ra một con số sai. Hệ '
  'thống gắn cho mỗi ước lượng một cờ tin cậy dựa trên hai điều kiện: tỉ lệ diện tích nhìn thấy so '
  'với hình bóng dự đoán phải đạt ngưỡng, và vùng ảnh không được chạm mép ảnh (trừ khi đã dùng cơ '
  'chế khớp mép trên).')
P('Ngưỡng tỉ lệ nhìn thấy được chọn bằng dữ liệu chứ không bằng cảm tính. Với ngưỡng 0,85, cờ bắt '
  'được 97% số ước lượng sai quá 5 mm, báo nhầm 10 trên 143 ước lượng tốt, và sai số lớn nhất '
  'trong nhóm được coi là tin cậy là 5,65 mm. Sau sự cố phân tích ở mục 6.4, ngưỡng được nâng lên '
  '**0,90**: cờ bắt được **100%** số ước lượng sai quá 5 mm, báo nhầm 12 trên 143, và sai số lớn '
  'nhất trong nhóm tin cậy giảm còn **3,42 mm** — an toàn tuyệt đối so với dung sai 12 mm của giác '
  'hút. Cái giá phải trả là đôi khi hệ thống từ chối một ước lượng vốn dĩ vẫn đúng, nhưng với bài '
  'toán gắp–thả thì bỏ qua một lượt rồi quan sát lại rẻ hơn nhiều so với hút trượt.')
P('Node thị giác công bố tỉ lệ nhìn thấy làm điểm tin cậy, và đặt điểm bằng **không** khi ước '
  'lượng không đáng tin, để bên sử dụng chỉ cần một phép so sánh đơn giản. Ảnh chú thích phục vụ '
  'theo dõi cũng hiển thị tỉ lệ phần trăm và nhãn cho biết ước lượng có dùng cơ chế khớp mép trên '
  'hay đang bị nghi che khuất.')
P('Thời gian xử lý sau khi thêm bộ ước lượng này là khoảng 16 ms mỗi khung hình, vẫn nhanh hơn '
  'nhiều so với chu kỳ 100 ms của camera, nên khối thị giác không phải là nút cổ chai của hệ '
  'thống.')

H2('5.6. Giao diện dữ liệu của khối thị giác')

P('Kết quả của khối thị giác được công bố dưới dạng các kiểu thông điệp chuẩn của ROS 2 dành cho '
  'thị giác, thay vì kiểu dữ liệu tự định nghĩa. Lựa chọn này có hai lợi ích: các công cụ hiển thị '
  'sẵn có đọc được ngay, và khi thay khối nhận dạng bằng một khối khác — chẳng hạn một mô hình học '
  'sâu ở giai đoạn sau — phần còn lại của hệ thống không phải sửa.')
P('Khối công bố ba luồng dữ liệu. Luồng **kết quả trên ảnh** chứa danh sách phát hiện, mỗi phát '
  'hiện gồm tên vật, khung bao và tâm khối tính theo điểm ảnh; luồng này phục vụ chẩn đoán và cho '
  'phép đánh giá riêng khâu nhận dạng. Luồng **vị trí trong hệ tọa độ robot** chứa tọa độ ba chiều '
  'của từng vật kèm một điểm số, trong đó điểm số mang ý nghĩa tỉ lệ diện tích nhìn thấy, và bằng '
  'không khi ước lượng không đáng tin. Luồng **ảnh chú thích** chỉ được sinh ra khi có người theo '
  'dõi, nhằm tiết kiệm tài nguyên; ảnh này vẽ khung bao, tên vật, tỉ lệ nhìn thấy và nhãn cho biết '
  'ước lượng đã dùng cơ chế khớp mép trên hay đang bị nghi che khuất.')
P('Quy ước “điểm số bằng không nghĩa là không tin cậy” được chọn có chủ đích để bên sử dụng chỉ '
  'cần một phép so sánh duy nhất, không phải hiểu chi tiết các tiêu chí bên trong. Đây là một '
  'nguyên tắc thiết kế giao diện quan trọng: khối nhận thức chịu trách nhiệm đánh giá chất lượng '
  'kết quả của chính nó, còn khối điều khiển chỉ cần biết dùng được hay không.')

# ============================================================================ CHƯƠNG 6
H1('Chương 6. TÍCH HỢP: GẮP–THẢ DỰA TRÊN THỊ GIÁC')

P('Chương này trình bày bước tích hợp cuối cùng: cắt nguồn vị trí thật khỏi bộ não điều khiển và '
  'thay hoàn toàn bằng dữ liệu camera, đồng thời giữ lại vị trí thật chỉ để chấm điểm. Đây chính '
  'là mục tiêu của đề tài, và cũng là nơi mọi sai sót của các khâu trước lộ ra.')

H2('6.1. Chọn nguồn vị trí vật')

P('Bộ thực thi nhiệm vụ đọc vị trí vật qua một tham số chọn nguồn, mặc định là camera; người vận '
  'hành có thể đổi ngay lúc chạy bằng một lệnh. Hai chế độ khác nhau không chỉ ở nguồn dữ liệu mà '
  'còn ở cách kiểm chứng kết quả (Bảng 6.1), vì camera có những điều không quan sát được.')

T('6.1',
  ['Khía cạnh', 'Chế độ vị trí thật', 'Chế độ camera'],
  [
      ('Nguồn vị trí vật', 'Vị trí thật từ mô phỏng', 'Ước lượng từ ảnh, chỉ dùng khi tin cậy'),
      ('Trước khi đo', 'Không cần', 'Robot lùi về tư thế quan sát, chờ ảnh mới'),
      ('Xác nhận đã nhấc được vật', 'Vật cao lên ≥ 10 mm', 'Trạng thái của giác hút'),
      ('Xác nhận đã thả đúng chỗ', 'Vị trí thật của vật', 'Quan sát lại bằng camera'),
      ('Vật không xác định được', 'Không xảy ra', 'Từ chối lệnh kèm lý do, hoặc bỏ qua và ghi chú'),
  ],
  widths=[4.0, 5.5, 6.5], size=11)

P('Cần nhấn mạnh lại điểm đã nêu ở mục 3.4: chỉ **bộ não** đổi nguồn, còn node giác hút vẫn dùng '
  'vị trí thật để quyết định hút được hay không. Nếu cho node giác hút dùng luôn dữ liệu camera '
  'thì thí nghiệm sẽ mất ý nghĩa — hệ thống sẽ “hút được” cả khi nhìn sai, điều không thể xảy ra '
  'ngoài đời.')

H2('6.2. Tư thế quan sát')

P('Vấn đề đầu tiên gặp phải khi chuyển sang camera là chính robot che vật. Ở vị trí gốc, bàn máy '
  'nằm giữa vùng làm việc và che khuất các vật ở xa: hộp đỏ đặt tại x = 120 mm bị gắn cờ không tin '
  'cậy và sai số lên tới 17 mm. Giải pháp là trước mỗi lần đo, robot được đưa về một **tư thế quan '
  'sát** cố định (0; 0; −0,11) m — tức nâng bàn máy lên cao nhất có thể ở giữa vùng làm việc. Tại '
  'tư thế này, cùng vật nói trên có tỉ lệ nhìn thấy 0,99 và sai số 0,3 mm.')
P('Vấn đề thứ hai là **thời điểm lấy ảnh**. Nếu dùng khung hình chụp trong lúc robot còn đang di '
  'chuyển thì ảnh vừa nhòe vừa có thể còn thấy bàn máy ở vị trí cũ. Vì vậy hệ thống chỉ nhận các '
  'khung hình được chụp **sau khi robot đã dừng** cộng thêm 0,3 s để hết rung, và yêu cầu ít nhất '
  'hai khung hình mới trước khi kết luận.')
P('Vấn đề thứ ba là vật **đang được giữ trên tay**: camera không thể đo được vì bộ ước lượng giả '
  'thiết vật nằm trên bàn hoặc trong khay. Hệ thống xử lý bằng cách dùng lại kết quả quan sát ngay '
  'trước khi nhặt, và xác nhận việc nhấc vật bằng trạng thái giác hút thay vì bằng camera. Đây là '
  'cách làm giống hệt hệ thống thật: cảm biến chân không trong giác hút cho biết đã bám được vật, '
  'còn camera thì không nhìn thấy vật nằm khuất dưới đầu công tác.')

H2('6.3. Xử lý vật không quan sát được')

P('Khi một vật không được thấy rõ, hệ thống không đoán mò. Tùy loại lệnh, có hai cách xử lý. Với '
  'lệnh chỉ đích danh một vật, lệnh bị **từ chối kèm lý do** — phân biệt rõ hai trường hợp “thấy '
  'nhưng không tin cậy, có thể bị che một phần” và “hoàn toàn không thấy”. Với lệnh quét toàn cảnh '
  'như dọn khay hay đặt lại, hệ thống **bỏ qua vật đó và ghi chú**, rồi tiếp tục với các vật khác.')
P('Cách xử lý thứ hai có một tính chất rất hữu ích: vòng lặp dọn quan sát lại sau **mỗi** vật, nên '
  'một vật đang bị vật khác che sẽ tự lộ ra sau khi vật che nó đã được dọn đi. Nói cách khác, hệ '
  'thống tự giải quyết được phần lớn tình huống che khuất bằng chính thứ tự thao tác, mà không cần '
  'thuật toán phức tạp.')

H2('6.4. Một ca hỏng và cách khắc phục')

P('Trong loạt thí nghiệm đầu tiên (năm bố trí, ngưỡng tin cậy 0,85), một ca hỏng đã xảy ra và rất '
  'đáng phân tích vì nó cho thấy giá trị của cơ chế tự kiểm chứng.')
P('Diễn biến: ở bố trí thứ tư, hộp đỏ nằm tại (8,4; −94,9) mm, tình cờ đứng **ngay sau trụ xanh** '
  'khi nhìn từ camera nên bị che khoảng 15%. Tỉ lệ nhìn thấy vẫn nhỉnh hơn ngưỡng 0,85 nên ước '
  'lượng được coi là tin cậy, dù đã lệch 8 mm. Giác hút có dung sai 12 mm nên **vẫn hút được** '
  'nhưng lệch tâm 8 mm. Khi thả vào ô A — ô chỉ cách thành khay 3 mm — hộp đè lên thành khay rồi '
  'trượt sang ô B. Bước kiểm chứng bằng camera phát hiện “hộp đỏ đang ở ô B chứ không phải ô A” và '
  'báo lỗi, thay vì báo thành công giả.')
P('Chẩn đoán: giả thuyết ban đầu là cánh tay robot che vật. Giả thuyết này được kiểm tra bằng cách '
  'cho robot quan sát từ sáu tư thế khác nhau; kết quả hoàn toàn giống nhau, nên nguyên nhân không '
  'phải robot mà là **vật che vật**.')
P('Khắc phục: nâng ngưỡng tỉ lệ nhìn thấy từ 0,85 lên 0,90 dựa trên số liệu của bộ dữ liệu đánh '
  'giá (số ước lượng sai bị bỏ sót giảm từ 1/29 xuống 0/29, đổi lại số báo nhầm tăng từ 10 lên '
  '12/143). Sau khi sửa, hộp đỏ trong tình huống này bị coi là “chưa rõ”, vòng lặp dọn chuyển sang '
  'gắp các vật khác trước; khi trụ xanh đã được dọn đi, hộp đỏ lộ ra hoàn toàn và được gắp chính '
  'xác. Bố trí thứ tư chạy lại thành công trọn vẹn.')
P('Bài học rút ra có giá trị vượt ra ngoài phạm vi ca hỏng này: trong một hệ thống có nhiều khâu, '
  'sai số nhỏ ở khâu nhận thức (8 mm, vẫn trong dung sai gắp) có thể bị **khuếch đại** ở khâu sau '
  '(thả trượt ô vì ô chỉ rộng hơn vật vài milimét). Vì vậy ngưỡng an toàn không nên chọn theo dung '
  'sai của một khâu mà theo khâu ngặt nhất trong chuỗi.')


# ============================================================================ CHƯƠNG 7
H1('Chương 7. THỰC NGHIỆM VÀ ĐÁNH GIÁ')

P('Chương này trình bày toàn bộ kết quả thực nghiệm của đề tài. Nguyên tắc xuyên suốt là mỗi kết '
  'luận phải gắn với một phép đo cụ thể, có nêu rõ số mẫu, điều kiện đo và cách chấm điểm, để '
  'người đọc có thể đánh giá được độ tin cậy của kết luận và có thể lặp lại phép đo.')

H2('7.1. Phương pháp đánh giá và bộ dữ liệu')

P('Ưu thế lớn nhất của việc làm trên mô phỏng là luôn có **vị trí thật** của vật để đối chứng. Mọi '
  'sai số trong chương này được định nghĩa là khoảng cách **theo phương ngang** giữa vị trí do '
  'khối thị giác ước lượng và vị trí thật do mô phỏng cung cấp. Phương ngang được chọn vì đó là '
  'phương quyết định thao tác gắp: giác hút hạ thẳng đứng xuống, nên sai số theo phương đứng không '
  'ảnh hưởng chừng nào robot còn dừng đúng ở đỉnh vật.')
P('Bộ dữ liệu đánh giá gồm **172 ảnh** kèm vị trí thật của vật, được thu tự động bằng một chương '
  'trình riêng: chương trình gọi dịch vụ của mô phỏng để dời vật tới từng vị trí trong một lưới 61 '
  'điểm, lần lượt cho cả ba vật, đồng thời đặt robot ở các tư thế khác nhau (lơ lửng trên vật với '
  'khe 60, 30, 15 và 5 mm) và đặt vật vào ba ô khay. Ảnh chỉ được chụp **sau khi** vật đã dời xong '
  'và chờ thêm 0,8 s cho ổn định.')
P('Việc phân tích được làm **ngoại tuyến**: một module tái hiện đúng chuỗi xử lý của node thị giác '
  'chạy lại trên các ảnh đã lưu. Cách làm này có ba ưu điểm: kết quả lặp lại được chính xác; có '
  'thể thêm nhiễu hoặc đổi độ sáng một cách tất định theo hạt giống ngẫu nhiên để đánh giá độ bền; '
  'và có thể so sánh hai phiên bản thuật toán trên cùng dữ liệu. Toàn bộ phân tích chạy trong '
  'khoảng 36 s.')

H2('7.2. Kiểm chứng phần động học')

P('Động học được kiểm chứng theo ba mức độc lập, từ tính tay tới mô phỏng vật lý.')
P('**Mức 1 — kiểm chứng bằng tay.** Thay vị trí gốc P = (0; 0; −0,1405) vào công thức động học '
  'ngược cho chân thứ nhất: a₁ = e − f = −0,0141; C₁ = a₁² + z₀² + r_f² − r_e² = −0,002137; '
  'A₁ = −2·r_f·a₁ = +0,002138, do đó A₁ + C₁ ≈ 0. Theo (2.8) thì t = 0 và θ₁ = 0, đúng bằng giá '
  'trị ghi trong mô hình URDF. Chính phép kiểm chứng đơn giản này đã bắt được một lỗi dấu trong '
  'phiên bản đầu tiên: khi viết nhầm aᵢ = (xᵢ − e) − f, vị trí gốc cho z₀ = −0,0823 m thay vì '
  '−0,1405 m. Bài học: luôn kiểm chứng công thức bằng một cấu hình đã biết trước khi tin dùng.')
P('**Mức 2 — kiểm thử tự động.** Ràng buộc chiều dài thanh chống sau khi giải động học ngược được '
  'thỏa mãn với sai số dưới 10⁻⁹ m. Điểm nằm trên trục Z cho ba góc khớp bằng nhau tới 10⁻¹². '
  'Phép quay điểm đi 120° làm ba góc hoán vị vòng đúng như dự đoán. Mạnh nhất là **vòng lặp động '
  'học ngược rồi thuận** trên 5 424 điểm: điểm thu được trùng điểm ban đầu với sai số lớn nhất '
  '5×10⁻¹³ m. Phép thử này có sức thuyết phục cao vì hai công thức được xây dựng hoàn toàn độc lập '
  'nhau — một dùng phép thế Weierstrass, một dùng giao ba mặt cầu — nên việc chúng khử lẫn nhau '
  'tới cỡ sai số làm tròn của máy tính cho thấy cả hai đều đúng.')
P('**Mức 3 — kiểm chứng trên mô phỏng vật lý.** Robot được ra lệnh tới chín điểm rồi đo lại vị trí '
  'thật của đầu công tác (Bảng 7.1).')

T('7.1',
  ['Lệnh (x; y; z) m', 'Gazebo đo được (m)', 'Sai lệch'],
  [
      ('(0; 0; −0,1405)', '(0,0002; −0,0002; −0,1406)', '< 0,3 mm'),
      ('(0; 0; −0,12)', '(0,0001; −0,0001; −0,1199)', '< 0,2 mm'),
      ('(0; 0; −0,18)', '(0,0002; −0,0002; −0,1802)', '< 0,3 mm'),
      ('(0,03; 0; −0,15)', '(0,0297; −0,0001; −0,1502)', '< 0,4 mm'),
      ('(−0,03; 0; −0,15)', '(−0,0293; −0,0001; −0,1502)', '< 0,8 mm'),
      ('(0; 0,03; −0,15)', '(0,0001; 0,0294; −0,1502)', '< 0,7 mm'),
      ('(0,02; −0,02; −0,16)', '(0,0198; −0,0197; −0,1602)', '< 0,4 mm'),
      ('(−0,04; −0,03; −0,19)', '(−0,0387; −0,0295; −0,1905)', '< 1,4 mm'),
  ],
  widths=[5.0, 6.5, 4.5], size=11)

P('Sai lệch dưới 1 mm trong vùng làm việc chính và tăng nhẹ tới khoảng 1,5 mm khi tay duỗi xa. '
  'Phần sai lệch còn lại **không đến từ công thức** mà từ mô phỏng vật lý: bàn máy võng nhẹ dưới '
  'trọng lực và bộ điều khiển PID của khớp có sai số xác lập cỡ 0,003 – 0,01 rad. Hiện tượng này '
  'phù hợp với hành vi của robot thật, nơi độ cứng hữu hạn và sai số bám của servo cũng gây sai '
  'lệch tương tự.')

H2('7.3. Độ chính xác của khối thị giác')

P('Bảng 7.2 tổng hợp sai số ước lượng vị trí trên toàn bộ bộ dữ liệu, chia theo từng nhóm tình '
  'huống. Hàng quan trọng nhất về mặt ứng dụng là nhóm “trong tầm với của robot”, vì đó là vùng mà '
  'hệ thống thực sự phải làm việc.')

T('7.2',
  ['Nhóm', 'Số mẫu', 'TB (mm)', 'Trung vị', 'RMS', 'P95', 'Max'],
  [
      ('Lưới — mọi điểm', '151', '2,76', '0,95', '4,95', '12,27', '20,58'),
      ('Lưới — vật trọn trong ảnh', '133', '2,03', '0,77', '3,97', '8,43', '20,58'),
      ('Lưới — vật bị cắt mép ảnh', '18', '8,19', '7,94', '9,47', '15,06', '15,14'),
      ('**Lưới — trong tầm với của robot**', '**58**', '**1,13**', '**0,83**', '**1,66**',
       '**3,68**', '**6,16**'),
      ('Trọn trong ảnh — hộp đỏ', '43', '2,02', '0,69', '4,06', '8,35', '19,38'),
      ('Trọn trong ảnh — trụ xanh lá', '44', '1,39', '0,49', '2,56', '6,62', '8,26'),
      ('Trọn trong ảnh — cầu xanh dương', '46', '2,65', '1,42', '4,88', '9,89', '20,58'),
      ('Vật trong khay', '9', '1,01', '0,88', '1,08', '1,63', '1,91'),
      ('Chỉ các ước lượng tin cậy', '131', '0,86', '0,73', '1,03', '1,89', '3,42'),
  ],
  widths=[5.6, 1.7, 1.9, 1.9, 1.5, 1.7, 1.7], size=11)

P('**Kết luận chính: trong vùng robot gắp được, sai số trung bình là 1,13 mm và lớn nhất là '
  '6,16 mm, tức 100% số mẫu nằm trong dung sai 12 mm của giác hút.** Độ lệch hệ thống đo được chỉ '
  '0,16 mm theo phương X và 0,00 mm theo phương Y, cho thấy hiệu chuẩn không để lại sai lệch đáng '
  'kể.')
P('Các sai số lớn đều nằm ngoài vùng làm việc của robot: vật ở góc gần camera bị mép ảnh cắt mất '
  'một phần (trung bình 8,19 mm), hoặc vật ở vùng xa bị bàn máy che. Hình 7.1 cho thấy phân bố sai '
  'số theo vị trí trên bàn: vùng trung tâm rất chính xác, sai số tăng dần về phía các mép.')

IMG('7.1')

P('So sánh giữa ba vật cũng cho thấy ảnh hưởng của hình dạng: trụ xanh có sai số nhỏ nhất (trung '
  'bình 1,39 mm) vì hình bóng của nó đối xứng và ổn định; quả cầu có sai số lớn nhất (2,65 mm) vì '
  'mặt cong làm biên vùng ảnh nhạy hơn với ngưỡng và với bóng đổ.')
P('Ảnh hưởng của việc robot che vật được đo riêng bằng cách cho robot lơ lửng ngay trên vật với '
  'các khe khác nhau (Bảng 7.3).')

T('7.3',
  ['Khe giữa bàn máy và đỉnh vật (mm)', 'Số mẫu', 'TB (mm)', 'Trung vị', 'Max'],
  [
      ('60', '3', '0,88', '0,93', '1,10'),
      ('30', '3', '0,79', '0,73', '1,04'),
      ('15', '3', '0,81', '0,72', '1,10'),
      ('5', '3', '4,57', '5,97', '7,63'),
  ],
  widths=[7.0, 2.2, 2.4, 2.2, 2.2], size=11)

P('Kết quả cho thấy chừng nào bàn máy còn cách đỉnh vật từ 15 mm trở lên thì ảnh hưởng không đáng '
  'kể (dưới 1,1 mm); chỉ khi hạ sát tới 5 mm, bàn máy mới che mất phần đáng kể của vật và sai số '
  'tăng lên trung bình 4,57 mm. Đây là căn cứ định lượng cho quy tắc ở mục 6.2: đo vị trí vật khi '
  'robot đang ở tư thế quan sát, chứ không phải khi robot đang lơ lửng ngay trên vật.')

H2('7.4. Hiệu quả của cơ chế xử lý che khuất')

P('Bảng 7.4 so sánh sai số trước và sau khi áp dụng bộ ước lượng có xét che khuất ở mục 5.5, trên '
  'cùng một bộ dữ liệu.')

T('7.4',
  ['Nhóm', 'TB trước (mm)', 'Max trước', 'TB sau (mm)', 'Max sau'],
  [
      ('Lưới — trong tầm với', '1,13', '6,16', '1,13', '6,16'),
      ('Lưới — mọi điểm', '2,76', '20,58', '2,76', '20,58'),
      ('**Vật trong khay**', '**13,44**', '**19,74**', '**1,01**', '**1,91**'),
      ('Bàn máy sát vật (khe 5 mm)', '4,57', '7,63', '4,57', '7,63'),
  ],
  widths=[5.5, 3.0, 2.6, 3.0, 2.4], size=11)

P('Cơ chế khớp mép trên giải quyết triệt để trường hợp vật trong khay: sai số trung bình giảm hơn '
  '13 lần, từ 13,44 mm — vượt dung sai giác hút — xuống 1,01 mm. Đây là cải tiến quyết định để '
  'lệnh lấy vật khỏi khay hoạt động được ở chế độ camera. Các nhóm còn lại không đổi vì cơ chế chỉ '
  'kích hoạt cho vật trong khay, đúng như thiết kế.')
P('Đóng góp của cờ tin cậy được đánh giá riêng như một bài toán phân loại: trong 29 ước lượng sai '
  'quá 5 mm, cờ bắt được **100%**; trong 143 ước lượng tốt, cờ báo nhầm 12 trường hợp (8%). Quan '
  'trọng nhất, sai số lớn nhất còn sót lại trong nhóm được coi là tin cậy chỉ là **3,42 mm**, tức '
  'là nếu hệ điều khiển chỉ dùng các ước lượng tin cậy thì nó không bao giờ nhận một vị trí sai '
  'quá 3,5 mm — an toàn với dung sai 12 mm.')

H2('7.5. Độ bền với nhiễu và với thay đổi độ sáng')

P('Vì camera mô phỏng gần như không có nhiễu (mục 5.1), độ bền được đánh giá bằng cách thêm nhiễu '
  'Gauss và thay đổi độ sáng một cách tất định lên ảnh đã lưu, rồi chạy lại toàn bộ chuỗi xử lý '
  '(Bảng 7.5, Bảng 7.6 và Hình 7.2).')

T('7.5',
  ['σ (mức xám)', '0', '5', '10', '20', '30', '40', '60'],
  [
      ('Tỉ lệ nhận dạng được', '100%', '100%', '100%', '99,2%', '93,2%', '82,7%', '57,9%'),
      ('Sai số TB (mm)', '2,03', '2,02', '2,07', '3,09', '4,36', '6,67', '7,52'),
      ('Trung vị (mm)', '0,77', '0,76', '0,81', '1,66', '3,16', '4,52', '6,95'),
  ],
  widths=[4.6, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6, 1.8], size=11)

T('7.6',
  ['Hệ số sáng', '0,2', '0,3', '0,5', '0,7', '1,0', '1,3', '1,6', '2,0'],
  [
      ('Tỉ lệ nhận dạng được', '52,6%', '83,5%', '100%', '100%', '100%', '100%', '100%', '100%'),
      ('Sai số TB (mm)', '21,19', '3,97', '2,04', '2,03', '2,03', '2,03', '1,98', '3,59'),
  ],
  widths=[4.4, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5], size=11)

IMG('7.2')

P('Nhận xét về nhiễu: chuỗi xử lý không bị ảnh hưởng cho tới σ = 10 mức xám, bắt đầu suy giảm từ '
  'σ = 20 và tụt mạnh từ σ = 40. Cần đọc bảng cẩn thận: ở mức nhiễu lớn, sai số P95 có xu hướng '
  '**giảm** trở lại, nhưng đó không phải vì thuật toán tốt lên mà vì thống kê chỉ tính trên các '
  'vật **còn nhận dạng được** — những vật khó đã bị loại khỏi mẫu.')
P('Nhận xét về độ sáng: hệ thống ổn định trong dải rộng từ 0,5× tới 1,6×, nghĩa là dung thứ tốt '
  'với thay đổi chiếu sáng vừa phải. Khi ảnh tối còn 0,3×, 16,5% số vật không được nhận dạng do '
  'không vượt ngưỡng độ sáng V ≥ 40; ở mức 0,2× thì mất hơn một nửa. Kết luận thực tiễn cho giai '
  'đoạn camera thật: điều kiện chiếu sáng cần được giữ ổn định ở mức trung bình trở lên, và ngưỡng '
  'độ sáng nên được hiệu chỉnh lại theo điều kiện phòng thí nghiệm thực tế.')

H2('7.6. Kết quả gắp–thả dựa trên camera')

P('Thí nghiệm cuối cùng đánh giá toàn hệ thống. Một chương trình tự động sinh 10 bố trí ngẫu nhiên '
  'của ba vật trong tầm với của robot (hạt giống cố định để lặp lại được), với mỗi bố trí chạy '
  'lệnh dọn toàn bộ vật vào khay rồi lệnh đưa mọi vật về chỗ cũ, ở cả hai chế độ nguồn vị trí. '
  'Việc chấm điểm dùng **vị trí thật** từ mô phỏng: lệnh dọn thành công khi mỗi vật nằm trong một '
  'ô riêng; lệnh đặt lại thành công khi vật về chỗ cũ với sai lệch không quá 10 mm.')

T('7.7',
  ['Chế độ', 'Vật vào ô', 'Lượt dọn trọn vẹn', 'Vật về chỗ cũ', 'Lượt đặt lại trọn vẹn',
   'Thời gian TB (s)'],
  [
      ('**Camera**', '**30/30**', '**10/10**', '**30/30**', '**10/10**', '58 + 55'),
      ('Vị trí thật', '30/30', '10/10', '30/30', '10/10', '43 + 36'),
  ],
  widths=[2.6, 2.2, 3.0, 2.4, 3.2, 2.6], size=11)

P('**Kết quả cho thấy hệ thống điều khiển hoàn toàn bằng camera đạt tỉ lệ thành công bằng đúng hệ '
  'thống dùng vị trí thật: 30/30 vật và 10/10 lượt cho cả hai lệnh.** Nói cách khác, ở quy mô thí '
  'nghiệm này, việc thay nguồn vị trí thật bằng thị giác máy tính **không làm giảm độ tin cậy** '
  'của thao tác.')
P('Chi phí phải trả là thời gian: mỗi lượt ở chế độ camera mất 58 s cho lệnh dọn và 55 s cho lệnh '
  'đặt lại, so với 43 s và 36 s ở chế độ vị trí thật, tức chậm hơn khoảng 35%. Toàn bộ phần chênh '
  'lệch này đến từ việc trước mỗi lần đo robot phải lùi về tư thế quan sát và chờ đủ hai khung '
  'hình mới. Đây là cái giá của độ tin cậy, và cũng là điểm còn có thể tối ưu: nếu bố trí camera '
  'sao cho bàn máy không bao giờ che vùng làm việc thì bước lùi về tư thế quan sát có thể bỏ đi.')

H2('7.7. Kiểm thử tự động của phần mềm')

P('Ngoài các phép đo trên mô phỏng, toàn bộ phần tính toán được kiểm thử tự động (Bảng 7.8). Đây '
  'là phần bảo đảm rằng những kết quả đã đạt được không bị phá vỡ khi chương trình tiếp tục được '
  'phát triển ở các bước sau.')

T('7.8',
  ['Tệp kiểm thử', 'Nội dung kiểm tra'],
  [
      ('test_delta_kinematics', 'Vị trí gốc, ràng buộc chiều dài thanh chống, tính đối xứng, '
                                'chọn nhánh nghiệm, vòng lặp ngược–thuận, điểm ngoài tầm với'),
      ('test_trajectory', 'Biên dạng bậc năm, vận tốc lớn nhất, quỹ đạo an toàn, kiểm tra trước '
                          'toàn tuyến'),
      ('test_gripper_logic', 'Điều kiện hút theo độ lệch ngang và khe hở'),
      ('test_task_planner', 'Lập kế hoạch cho mọi lệnh cấp cao và các trường hợp bị từ chối'),
      ('test_task_executor', 'Chế độ camera với robot giả lập: quan sát, kiểm chứng, vật không rõ'),
      ('test_color_detector', 'Ảnh tổng hợp biết trước đáp án và ba ảnh thật lưu sẵn'),
      ('test_camera_model', 'Phép chiếu, tia nhìn, giao mặt phẳng, hiệu chuẩn trên ảnh thật'),
      ('test_vision_estimation', 'Hình bóng dự đoán, khớp mép trên, cờ tin cậy trên ảnh thật'),
      ('test_vision_eval', 'Tính đúng của công cụ đánh giá sai số'),
  ],
  widths=[4.6, 11.4], size=11)

P('Tổng cộng bộ kiểm thử gồm **143 trường hợp**, chạy hết trong khoảng 5 s và tất cả đều đạt. Điểm '
  'đáng nói về phương pháp: các trường hợp kiểm thử của khối thị giác dùng **ảnh thật lưu sẵn** '
  'kèm đáp án, chứ không chỉ dùng ảnh tổng hợp — nhờ vậy chúng phát hiện được cả những lỗi chỉ xuất '
  'hiện trên dữ liệu thực, như trường hợp thuật toán IPPE đã nêu ở mục 5.3.')

H2('7.8. Đối chiếu yêu cầu và kết quả')

P('Bảng 7.9 đối chiếu từng yêu cầu đặt ra ở mục 1.4 với kết quả đo được, kèm mục trong khóa luận '
  'chứa số liệu tương ứng.')

T('7.9',
  ['Yêu cầu', 'Chỉ tiêu', 'Kết quả đạt được', 'Mục'],
  [
      ('Giải được động học cho mọi điểm trong vùng làm việc',
       'Không có nghiệm sai nhánh', 'Đúng trên 149 769 điểm; vòng lặp ngược–thuận '
       'sai số 5·10⁻¹³ m', '2.2; 7.2'),
      ('Robot tới đúng điểm được lệnh', 'Sai lệch nhỏ hơn dung sai gắp 12 mm',
       'Dưới 1 mm trong vùng chính, 1,4 mm khi duỗi xa', '7.2'),
      ('Xác định vị trí vật chỉ bằng ảnh camera',
       'Sai số ngang nhỏ hơn 12 mm', 'Trung bình 1,13 mm, lớn nhất 6,16 mm trong vùng gắp được',
       '7.3'),
      ('Không đưa ra vị trí sai mà vẫn hành động', 'Phát hiện được ước lượng kém',
       'Cờ tin cậy bắt 100% ước lượng sai quá 5 mm; nhóm tin cậy sai tối đa 3,42 mm', '5.5; 7.4'),
      ('Lấy được vật từ trong khay bằng dữ liệu camera',
       'Sai số nhỏ hơn 12 mm', 'Giảm từ 13,44 mm xuống 1,01 mm nhờ khớp mép trên', '5.5; 7.4'),
      ('Gắp–thả tự động toàn bộ cảnh', 'Tỉ lệ thành công cao',
       '30/30 vật và 10/10 lượt, bằng chế độ dùng vị trí thật', '7.6'),
      ('Kiểm chứng được kết quả từng thao tác', 'Không báo thành công giả',
       'Bắt được ca thả trượt ô ở mục 6.4', '4.5; 6.4'),
      ('Sẵn sàng chuyển sang camera thật', 'Không phải sửa phần điều khiển',
       'Đổi nguồn bằng một tham số; marker hiệu chuẩn đã xuất bản in', '6.1; Kết luận'),
  ],
  widths=[4.4, 3.4, 6.2, 2.0], size=11)

H2('7.9. Bàn luận và những hạn chế đã biết')

P('Tổng hợp lại, các kết quả trên cho phép rút ra ba nhận định.')
P('**Thứ nhất, độ chính xác của khối thị giác không phải là yếu tố giới hạn.** Sai số trung bình '
  '1,13 mm trong vùng làm việc nhỏ hơn một bậc so với dung sai 12 mm của giác hút, và ngay cả giá '
  'trị lớn nhất cũng chỉ bằng một nửa dung sai. Yếu tố giới hạn thực sự là **che khuất** — một vấn '
  'đề mang tính hình học chứ không phải vấn đề độ phân giải hay nhiễu.')
P('**Thứ hai, cơ chế thừa nhận không biết quan trọng hơn cơ chế đoán giỏi.** Cờ tin cậy không làm '
  'ước lượng chính xác hơn, nhưng nó biến một sai số nguy hiểm (nhận vị trí sai mà vẫn hành động) '
  'thành một trạng thái an toàn (biết mình không rõ, quan sát lại sau). Kết hợp với việc quan sát '
  'lại sau mỗi vật, cơ chế này giải quyết được cả che khuất do robot lẫn do vật khác.')
P('**Thứ ba, kiểm chứng sau mỗi thao tác là thành phần không thể thiếu.** Ca hỏng ở mục 6.4 cho '
  'thấy chính bước kiểm chứng đã ngăn hệ thống báo thành công giả, và cung cấp thông tin để chẩn '
  'đoán đúng nguyên nhân.')
P('Những hạn chế đã biết của hệ thống ở giai đoạn này gồm:')
B([
    'Mô hình hình bóng giả thiết hộp **không bị xoay** quanh trục đứng; hộp bị xoay có diện tích '
    'hình bóng khác nên tỉ lệ nhìn thấy kém chính xác hơn.',
    'Cơ chế khớp mép trên chỉ áp dụng cho vật trong khay; vật bị che **phía trên** vẫn chỉ được '
    'gắn cờ chứ không sửa được vị trí.',
    'Vùng ngay phía sau khay bị thành khay che vĩnh viễn với góc camera hiện tại.',
    'Đầu công tác vẫn lún vào vật động khi bị ép xuống (mục 3.7), nguyên nhân chưa được kiểm chứng.',
    'Trong một lượt thí nghiệm ở chế độ vị trí thật, khi lấy hộp đỏ khỏi một ô, trụ xanh ở ô bên '
    'cạnh **văng khỏi bàn**. Hiện tượng không lặp lại trong loạt 10 bố trí sau đó; nguyên nhân '
    'được nghi liên quan tới việc bàn máy rộng 50 mm đè lên cả vật bên cạnh kết hợp với xung lực '
    'tiếp xúc của bộ giải va chạm, nhưng **chưa được kiểm chứng**.',
    'Bộ sinh quỹ đạo phát điểm theo đồng hồ thực chứ chưa theo đồng hồ mô phỏng, nên khi hệ số '
    'thời gian thực nhỏ hơn 1 thì quỹ đạo bị bám kém hơn thiết kế.',
    'Camera mô phỏng không có méo ống kính và không có nhiễu thật, nên kết quả về độ bền chỉ mang '
    'tính tham khảo cho hệ thật.',
])

# ============================================================================ KẾT LUẬN
H1('Chương 8. CHUYỂN SANG CAMERA THẬT')

P('Bảy chương trước xây dựng và đánh giá hệ thống hoàn toàn trong môi trường mô phỏng. Chương này '
  'thay camera mô phỏng bằng một camera thật quan sát các vật thật đặt trên bàn thật, giữ nguyên '
  'robot trong mô phỏng. Đây là trọng tâm của đề tài theo đúng tên gọi: tín hiệu điều khiển đến từ '
  'thế giới thật, còn đối tượng được điều khiển nằm trong mô phỏng.')
P('Chương được tổ chức theo đúng thứ tự mà các vấn đề đã bộc lộ trong quá trình thực hiện: trước '
  'hết là bài toán tỉ lệ và cách giải quyết nó ở mức thiết kế, tiếp đến là hiệu chuẩn, rồi tới ba '
  'vấn đề mà môi trường mô phỏng không thể bộc lộ — ánh sáng thay đổi, mặt bàn phản chiếu, và các '
  'vùng ảnh giả mạo — và cuối cùng là kết quả đo sai số đối chiếu với mô phỏng.')

H2('8.1. Bài toán tỉ lệ và nguyên tắc ánh xạ')

P('Robot delta trong mô phỏng có vùng làm việc rất nhỏ: mặt bàn nằm ở cao độ −0,22 m còn trần vùng '
  'làm việc khoảng −0,10 m, tức chỉ còn khoảng 120 mm chiều cao khả dụng. Vật thật được chọn là '
  'lon nước ngọt 330 ml, đường kính 57,5 mm và cao 147 mm. Đặt thẳng một lon như vậy vào cảnh mô '
  'phỏng thì đỉnh lon nằm đúng ở trần vùng làm việc: robot có thể chạm tới đỉnh lon nhưng **không '
  'thể nhấc lon lên**, và khay chứa có lòng 70×70 mm cũng không chứa nổi lon đường kính 66 mm kể '
  'cả phần nhô.')
P('Phóng to robot không phải là lời giải. Hình học robot được mô tả trong tệp URDF, và mạch động '
  'học kín được đóng lúc chạy bằng cách hàn hai liên kết có hệ quy chiếu **trùng nhau tại tư thế '
  'gốc**; đổi hình học sẽ phá vỡ điều kiện trùng khớp đó, đồng thời làm mất hiệu lực toàn bộ phần '
  'kiểm chứng động học đã trình bày ở Chương 7.')
P('Lời giải được chọn là **ánh xạ theo tỉ lệ**: thế giới thật được thu nhỏ k lần khi đưa vào mô '
  'phỏng. Với k = 3, lon thật đường kính 57,5 mm và cao 147 mm trở thành lon ảo đường kính 19,2 mm '
  'và cao 49 mm — vừa vặn vùng làm việc và vừa khay chứa. Tỉ lệ hình dạng được giữ nguyên nên lon '
  'ảo trông đúng như lon thật.')
P('Giá trị k = 3 không phải chọn tùy tiện mà là **kết quả của một ràng buộc đo được**. Khi mang '
  'một lon tới khay, robot phải nhấc lon đi qua phía trên các lon còn đang đứng, tức đầu công tác '
  'phải lên tới cao độ bằng đỉnh lon đứng cộng nửa bề dày bàn máy cộng chiều cao lon đang mang. '
  'Với k = 2,5 (lon ảo cao 58,8 mm) yêu cầu đó là −0,0994 m, **vượt trần vùng làm việc** −0,10 m '
  'nên không thể thực hiện: trong thí nghiệm, lon đang mang chồng 30,6 mm vào lon đang đứng và '
  'đánh đổ nó. Với k = 3 yêu cầu chỉ còn −0,119 m, thỏa mãn thoải mái.')
P('Một câu hỏi tự nhiên là liệu việc thu nhỏ có làm xấu độ chính xác hay không. Câu trả lời là '
  '**không**, và lý do rất gọn: camera phải bao quát một vùng rộng gấp k lần nên độ phân giải '
  'không gian (số milimét ứng với mỗi điểm ảnh) xấu đi đúng k lần; nhưng khi quy sai số về không '
  'gian ảo thì nó lại được chia cho k. Hai hệ số triệt tiêu nhau. Dung sai giác hút 12 mm trong '
  'không gian ảo tương đương 36 mm trên bàn thật. Camera thật có độ phân giải 1280×720, gấp đôi '
  'camera mô phỏng 640×480 theo mỗi chiều, nên phần dư này còn bù thêm cho nhiễu cảm biến và méo '
  'ống kính vốn không có trong mô phỏng.')

H3('8.1.1. Quy ước tỉ lệ khi hiệu chuẩn')

P('Một quyết định thiết kế quan trọng là **đưa tọa độ ảo vào bài toán hiệu chuẩn ngay từ đầu**, '
  'thay vì hiệu chuẩn theo milimét thật rồi chia kết quả cho k về sau. Cụ thể, khi giải bài toán '
  'ước lượng tư thế camera từ các điểm mốc, tọa độ của các điểm mốc được khai báo bằng **tọa độ '
  'thật chia cho k**.')
P('Cơ sở của quy ước này là một tính chất của phép chiếu phối cảnh: thu nhỏ toàn bộ thế giới đi k '
  'lần chỉ làm **vectơ tịnh tiến của camera bị chia cho k**, còn ma trận nội tham số, các hệ số '
  'méo và bản thân phép chiếu đều không đổi. Nhờ vậy toàn bộ khối thị giác đã xây dựng ở Chương 5 '
  '— phép giao tia với mặt phẳng, hình bóng dự đoán, cao độ mặt bàn, hình học khay — chạy nguyên '
  'vẹn trong hệ ảo mà **không phải sửa một dòng nào**. Cái giá duy nhất là vị trí camera in ra '
  'trong các báo cáo nhỏ hơn thực tế k lần, điều chỉ ảnh hưởng tới cách trình bày.')

H2('8.2. Thiết bị và bố trí thực nghiệm')

P('Camera được chọn là Logitech C270. Tiêu chí lựa chọn không phải độ phân giải cao nhất mà là '
  '**khả năng khóa các chế độ tự động**: một camera tự điều chỉnh tiêu cự, phơi sáng hoặc cân bằng '
  'trắng trong lúc chạy sẽ làm vô hiệu kết quả hiệu chuẩn và làm ngưỡng màu trôi theo thời gian. '
  'C270 khóa được phơi sáng, cân bằng trắng và bù ngược sáng, và quan trọng hơn cả, nó là camera '
  '**lấy nét cố định** — không có mô-tơ lấy nét nên tiêu cự không thể trôi sau khi hiệu chuẩn. '
  'Trong bối cảnh này, việc thiếu chức năng lấy nét tự động là một **ưu điểm** chứ không phải '
  'khuyết điểm.')
P('Một chương trình kiểm tra riêng được viết để thẩm định camera trước khi dùng: nó liệt kê các '
  'nút điều chỉnh bắt buộc, chọn chế độ nén có độ phân giải lớn nhất đạt tối thiểu 15 hình/giây, '
  'khóa các chế độ thủ công rồi **đọc lại để xác nhận**, và đo nhiễu cảm biến. Kết quả: C270 chạy '
  '1280×720 ở 30 hình/giây, khóa được toàn bộ các chế độ cần thiết, nhiễu cảm biến khoảng 2,2 mức '
  'xám — thấp hơn nhiều so với ngưỡng 10 mức xám mà Chương 7 xác định là vô hại.')

T('8.1',
  ['Hạng mục', 'Thông số'],
  [
      ('Camera', 'Logitech C270, 1280×720 @ 30 hình/giây, nén MJPG, lấy nét cố định'),
      ('Nhiễu cảm biến', '≈ 2,2 mức xám (ngưỡng vô hại theo Chương 7: ≤ 10)'),
      ('Vị trí camera', 'Lùi 539 mm, cao 628 mm so với mặt bàn, góc chúc xuống 45,2°'),
      ('Mặt bàn', 'Màu đen nhám, kích thước khả dụng khoảng 600 mm'),
      ('Điểm mốc hiệu chuẩn', 'Sáu marker ArUco từ điển 4×4, ô đen 60 mm, dán cố định trên bàn'),
      ('Vật thể', 'Ba lon nước ngọt 330 ml: đỏ, xanh lam, xanh lục'),
      ('Tỉ lệ ánh xạ', 'k = 3 (lon ảo đường kính 19,2 mm, cao 49 mm)'),
      ('Chiếu sáng', 'Hai đèn khuếch tán, rèm che ánh sáng ngoài trời'),
  ],
  widths=[4.5, 11.3])

IMG('8.1')

P('Góc chúc thật là 45,2°, khác hẳn góc 32° của camera mô phỏng. Sự khác biệt này được **chấp nhận '
  'có ý thức** thay vì cố ép cho giống: bàn thật không đủ dài để lùi camera thêm. Khối thị giác '
  'không bị ảnh hưởng vì nó dùng mô hình camera **đo được** chứ không giả định góc nhìn; và góc '
  'dốc hơn thực ra **có lợi** cho bài toán che khuất vì các lon ít che nhau hơn. Điểm cần lưu ý '
  'chỉ là khi đối chiếu kết quả thật với mô phỏng thì có thêm một biến khác nhau giữa hai bên.')
P('Bố trí các điểm mốc trên bàn thật **không phải là bố trí ảo nhân với k**: nhân ba lên thì các '
  'điểm mốc trải rộng 810×870 mm, không vừa mặt bàn rộng 600 mm. Vì vậy một bố trí riêng được '
  'thiết kế cho bàn thật, chiếm 560 mm, kèm vùng đặt vật tương ứng. Khi quy về không gian ảo, vùng '
  'đặt vật này có bán kính 113 mm, nằm gọn trong tầm với 119 mm của robot.')

H2('8.3. Hiệu chuẩn camera')

P('Camera thật khác camera mô phỏng ở hai điểm buộc phải xử lý: nó có **méo ống kính**, và các '
  'tham số quang học của nó **không được biết trước**. Do đó phải hiệu chuẩn hai bước: nội tham số '
  '(tiêu cự, tâm ảnh, hệ số méo — gắn với từng máy cụ thể, kể cả hai máy cùng kiểu) và ngoại tham '
  'số (vị trí và hướng của camera so với bàn).')

H3('8.3.1. Nội tham số')

P('Nội tham số được xác định bằng phương pháp bàn cờ quen thuộc: chụp nhiều ảnh một bàn cờ phẳng ở '
  'nhiều tư thế rồi giải bài toán tối ưu để tìm bộ tham số làm các góc ô chiếu lại đúng nhất.')
P('Quá trình này đã thất bại nhiều lần trước khi thành công, và các nguyên nhân đều đáng ghi lại '
  'vì chúng là những cái bẫy điển hình. Thứ nhất là **bàn cờ không phẳng**: bản in dán lên bìa '
  'cứng vẫn vênh khoảng 1,8 mm, đủ để làm hỏng phép giải. Thứ hai, và tinh vi hơn, là **suy biến '
  'do thiếu đa dạng tư thế**: nếu mọi ảnh đều chụp bàn cờ nghiêng xấp xỉ như nhau thì tiêu cự và '
  'khoảng cách tới bàn cờ **không tách được khỏi nhau**, bài toán có vô số nghiệm cho cùng một sai '
  'số chiếu lại. Triệu chứng là phép giải vẫn báo sai số nhỏ nhưng cho tiêu cự vô lý.')
P('Giải pháp cuối cùng là hiển thị bàn cờ **trên màn hình máy tính** thay vì dùng bản in: màn hình '
  'phẳng tuyệt đối và kích thước ô biết chính xác, nên loại bỏ hoàn toàn nguyên nhân thứ nhất. '
  'Chương trình hiệu chuẩn được bổ sung phần hướng dẫn trực tiếp: nó đo độ nghiêng của bàn cờ '
  'trong từng khung hình, chia dải nghiêng thành nhiều khoảng và **yêu cầu đủ số ảnh trong mỗi '
  'khoảng** trước khi cho phép giải, qua đó ngăn chặn suy biến một cách có hệ thống. Hệ số méo bậc '
  'cao nhất được cố định bằng 0 để đường cong méo giữ tính đơn điệu ra tới góc ảnh.')

T('8.2',
  ['Đại lượng', 'Giá trị'],
  [
      ('Tiêu cự f_x, f_y', '1417,4 và 1418,1 điểm ảnh'),
      ('Tâm ảnh c_x, c_y', '610,9 và 382,4 điểm ảnh'),
      ('Hệ số méo xuyên tâm k₁, k₂', '+0,1178 và −0,2765'),
      ('Hệ số méo tiếp tuyến p₁, p₂', '+0,0027 và −0,0008'),
      ('Sai số chiếu lại', '0,222 điểm ảnh'),
      ('Số ảnh dùng để giải', '16'),
  ],
  widths=[7.0, 8.8])

H3('8.3.2. Ngoại tham số')

P('Ngoại tham số được xác định từ sáu marker ArUco dán cố định trên bàn, theo đúng phương pháp đã '
  'dùng trong mô phỏng ở Chương 5: tâm marker được lấy làm điểm tương ứng, bài toán tư thế được '
  'giải bằng thuật toán SQPnP rồi tinh chỉnh bằng phương pháp Levenberg–Marquardt.')
P('Khác biệt quan trọng so với mô phỏng là ngoại tham số được **giải lại ở từng khung hình** thay '
  'vì nạp một lần từ tệp. Lý do rất thực tế: giá đỡ camera có thể bị chạm tay, và một góc lệch 1° '
  'đã làm vị trí vật sai 7,7 mm quy đổi, 2° là vượt dung sai giác hút, mà không có gì báo cho '
  'người vận hành biết. Vì các marker nằm cố định ở rìa bàn và luôn trong khung hình, việc giải '
  'lại mỗi khung là khả thi và biến một nguồn sai số tiềm ẩn thành một đại lượng được theo dõi '
  'liên tục.')
P('Trong quá trình dựng bố trí thật, ba cái bẫy **đo đạc** đã mắc phải, cả ba đều là khuyết điểm '
  'của công cụ chứ không phải của người dựng, và cả ba đều suýt dẫn tới việc bóc các marker ra dán '
  'lại một cách vô ích.')
N([
    '**Quy đổi chiều cao camera quên mất cao độ mặt bàn.** Công cụ nhân cao độ ảo với k mà quên '
    'rằng trong hệ ảo mặt bàn nằm ở −0,22 chứ không phải 0, nên báo camera ở độ cao âm, tức nằm '
    'dưới mặt bàn. Phép kiểm thử tự động không phát hiện được vì nó so kết quả với chính đại lượng '
    'mắc cùng một lỗi — hai vế cùng sai một kiểu thì phép so sánh vẫn qua. Phép kiểm thử sau đó '
    'được sửa để so với hình học thật của giá đỡ.',
    '**Hàm ước lượng tư thế từng marker riêng lẻ cho kết quả sai** trên marker nhỏ nhìn xiên: nó '
    'báo hai marker lệch tới 65 mm, hai lần liên tiếp. Phương pháp đúng là khớp tư thế từ một nhóm '
    'marker đáng tin rồi **giao tia với mặt phẳng bàn** để suy ra vị trí các marker còn lại; làm '
    'như vậy thì cả sáu marker đều nằm trong 8 mm so với thiết kế.',
    '**Chấm điểm bằng đơn vị điểm ảnh là sai đơn vị.** Công cụ báo sai số 3,25 điểm ảnh là "quá '
    'lớn", trong khi quy về không gian ảo chỉ là 0,93 mm, ngang với mô phỏng. Cùng một sai số điểm '
    'ảnh ứng với số milimét rất khác nhau tùy camera đặt gần hay xa. Ngưỡng đánh giá sau đó được '
    'định nghĩa theo **milimét quy đổi, đối chiếu với dung sai giác hút 12 mm**.',
])

T('8.3',
  ['Đại lượng', 'Giá trị'],
  [
      ('Số marker nhận được', '6 / 6'),
      ('Sai số định vị marker (quy đổi về không gian ảo)', '0,93 mm'),
      ('Sai số tương ứng trên bàn thật', '2,8 mm'),
      ('Vị trí camera suy ra', 'lùi 557 mm, lệch ngang +1 mm, cao 631 mm'),
      ('Góc chúc xuống suy ra', '46,1°'),
      ('Ngưỡng chấp nhận', '≤ 3 mm quy đổi (đạt); > 6 mm (lỗi)'),
  ],
  widths=[8.5, 7.3])

H2('8.4. Phân đoạn vật khỏi nền: vì sao ngưỡng cố định không dùng được')

P('Trong mô phỏng, việc tách vật khỏi nền được thực hiện bằng cách lấy ngưỡng: một điểm ảnh được '
  'coi là thuộc vật nếu nó đủ bão hòa màu **hoặc** đủ sáng so với mức nền. Cách này hoạt động tốt '
  'suốt Chương 5 đến Chương 7 vì môi trường mô phỏng có điều kiện chiếu sáng không đổi.')
P('Trên bàn thật, cách này **thất bại theo hai cơ chế ngược nhau**, tùy điều kiện chiếu sáng. Phát '
  'hiện này đến từ việc chạy đúng một bộ ngưỡng trên cùng một bố trí vào hai thời điểm khác nhau '
  'trong ngày.')

T('8.4',
  ['', 'Ban ngày, ánh sáng tự nhiên', 'Một đèn, rèm che'],
  [
      ('Độ sáng mặt bàn', 'Cao (mức 97)', 'Rất thấp (mức 39)'),
      ('Cơ chế hỏng', 'Ánh sáng cửa sổ làm mặt bàn **ám màu** nên nhiều điểm ảnh của bàn vượt '
       'ngưỡng bão hòa', 'Bàn quá tối nên đại lượng bão hòa, vốn là tỉ số, trở nên **nhiễu**; '
       'phần lớn điểm ảnh của bàn vượt ngưỡng'),
      ('Tỉ lệ khung hình bị coi là vật', '17 – 48 %', '35 – 55 %'),
      ('Hệ quả', 'Các lon dính liền với mảng nền, hình bóng méo hoàn toàn',
       'Gần như toàn bộ mặt bàn bị coi là vật'),
      ('Sàn độ sáng có cứu được không?', 'Không — mặt bàn đã sáng hơn ngưỡng sàn',
       'Có, nhưng khi đó lại cắt mất nửa dưới của các lon sẫm màu'),
  ],
  widths=[3.6, 6.1, 6.1])

P('Điểm then chốt là **hai cơ chế này triệt tiêu lẫn nhau về mặt giải pháp**: ngưỡng nào chữa được '
  'trường hợp thứ nhất thì làm hỏng trường hợp thứ hai và ngược lại. Việc quét toàn bộ dải phơi '
  'sáng từ 80 đến 2600 và dải khuếch đại từ 0 đến 100 cho thấy không có thiết lập nào cho kết quả '
  'nhận dạng chấp nhận được, nên nguyên nhân không nằm ở việc chỉnh camera.')
P('Kết luận rút ra có giá trị tổng quát: **một ngưỡng cố định mã hóa một giả định về điều kiện '
  'chiếu sáng**, và giả định đó không tồn tại ngoài phòng thí nghiệm.')

H3('8.4.1. Trừ nền theo ảnh tham chiếu')

P('Giải pháp được chọn là đổi câu hỏi. Thay vì hỏi *"điểm ảnh này sáng và đậm màu đến mức nào"*, '
  'hệ thống hỏi *"điểm ảnh này có còn giống mặt bàn lúc không có vật hay không"*. Cụ thể, một ảnh '
  'mặt bàn trống được chụp làm chuẩn, lấy trung vị của hai mươi khung hình để nhiễu cảm biến không '
  'đi vào chính cái chuẩn; sau đó mỗi khung hình được so sánh từng điểm ảnh với ảnh chuẩn, và '
  'điểm nào sai khác quá 30 mức xám thì được coi là thuộc vật.')
P('Ưu điểm của cách này là vân bàn, ám màu, chỗ sáng chỗ tối đều **có mặt y hệt trong ảnh chuẩn** '
  'nên tự triệt tiêu. Hiệu quả đo được rất dứt khoát: trên một cảnh không thay đổi, mặt nạ mới báo '
  '**0,00 %** diện tích khung hình là vật, trong khi phương pháp lấy ngưỡng báo **12,06 %**. Biên '
  'an toàn cũng rất rộng: nhiễu cảm biến đo được là 1 mức xám so với ngưỡng 30.')
IMG('8.2')

P('Hình 8.2 cho thấy sự khác biệt trên cùng một khung hình. Ở phương pháp lấy ngưỡng, các mảng nền '
  'quanh lon bên trái lọt vào mặt nạ và dính liền với lon, làm hình bóng méo hẳn; ở phương pháp '
  'trừ nền, mặt nạ chỉ còn ba lon. Phần nhô ra dưới chân mỗi lon trong ảnh (b) chính là **ảnh phản '
  'chiếu** — nó vẫn ở trong mặt nạ, và đó là lý do mục 8.5 phải đổi sang dùng mép trên.')

P('Phương pháp này có hai giới hạn phải nói rõ. Thứ nhất, **đổi điều kiện chiếu sáng hoặc xê dịch '
  'camera thì phải chụp lại ảnh chuẩn** — đó là cái giá phải trả, và nó biến một giả định ngầm '
  '(ánh sáng không đổi) thành một thao tác tường minh mà người vận hành kiểm soát được. Thứ hai, '
  'và quan trọng hơn, nó **không loại bỏ được ảnh phản chiếu của vật trên mặt bàn**, vì ảnh phản '
  'chiếu chỉ xuất hiện khi có vật nên nó cũng "khác với mặt bàn trống". Vấn đề này được xử lý ở '
  'mục tiếp theo.')

H2('8.5. Mặt bàn phản chiếu và việc chọn đặc trưng hình học')

P('Mặt bàn thật, dù sơn nhám, vẫn phản chiếu các lon đủ rõ để ảnh phản chiếu dính liền với chân '
  'lon trong mặt nạ. Đo trực tiếp bằng cách so mặt nạ với hình bóng dự đoán tại vị trí thật đã '
  'biết: mặt nạ **phình xuống dưới 24 đến 57 điểm ảnh** so với chân lon.')
P('Độ dài vệt phản chiếu **phụ thuộc khoảng cách tới camera** theo một quy luật hình học đơn giản: '
  'camera càng nhìn chếch thì ảnh gương càng trải dài. Đo trên một khung hình với ba lon ở ba '
  'khoảng cách khác nhau: lon xa camera nhất cho vệt dài **25 điểm ảnh**, lon ở giữa **67**, lon '
  'gần nhất **102**. Con số này quan trọng khi thiết kế phép kiểm tra: một ngưỡng cố định theo '
  'điểm ảnh sẽ sai ở một trong hai đầu, nên mọi phép đo đều phải quy chiếu về **chân vật dự đoán** '
  'chứ không về một khoảng cách cố định.')
P('Hệ quả là **mép đáy của mặt nạ không còn là chỗ lon chạm bàn**, trong khi toàn bộ phép ước '
  'lượng vị trí ở Chương 5 dựa trên chính đặc trưng đó. Phải chọn một đặc trưng hình học khác, và '
  'lựa chọn tự nhiên là **mép trên**: ảnh phản chiếu luôn nằm phía dưới vật nên không bao giờ chạm '
  'tới mép trên.')
P('Cần nói rõ rằng kết luận này **mâu thuẫn với kết luận đã rút ra trong mô phỏng ở Chương 5**, '
  'nơi phép khớp mép trên bị loại bỏ vì cho sai số 5–12 mm trong khi mép đáy chỉ cho 0,1–0,7 mm. '
  'Mâu thuẫn chỉ là bề ngoài: kết luận cũ áp dụng cho mặt nạ **theo màu**, nơi mép trên là mép của '
  'vành màu trên thân lon, bị nắp lon và vành nhãn làm nhòe. Ở đây mặt nạ là **hình bóng** của vật, '
  'nên mép trên chính là vành miệng lon — một đặc trưng hình học sắc nét. Hai kết luận trái ngược '
  'nhau nhưng đều đúng trong phạm vi của mình, vì chúng nói về hai đại lượng khác nhau.')

H3('8.5.1. Một bài học về cách so sánh hai phương pháp')

P('Trước khi áp dụng trừ nền, phép đo sai số cho kết quả tưởng như rõ ràng: khớp mép đáy đạt 9,08 '
  'mm quy đổi còn khớp mép trên chỉ đạt 18,31 mm, tức mép đáy **tốt hơn gấp đôi**. Sau khi áp '
  'dụng trừ nền, thứ tự **đảo ngược hoàn toàn**: mép đáy 11,42 mm còn mép trên 4,50 mm.')
P('Nguyên nhân của sự đảo ngược là **hai sai số triệt tiêu lẫn nhau**. Khi mặt nạ còn bẩn, các '
  'mảng nền lọt vào làm hình bóng phình lên **phía trên**, kéo ước lượng ra xa camera; ảnh phản '
  'chiếu làm hình bóng phình xuống **phía dưới**, kéo ước lượng lại gần. Với hai trong ba lon, hai '
  'hiệu ứng ngược chiều này bù nhau một cách tình cờ, tạo ra một con số đẹp không phản ánh chất '
  'lượng thật của phương pháp. Dấu hiệu nhận biết đã có sẵn trong dữ liệu mà ban đầu bị bỏ qua: '
  'sai lệch hệ thống của ba lon rất khác nhau (−15,9; −16,9 và −41,5 mm). Sau khi mặt nạ được làm '
  'sạch, ba giá trị đó trở nên **gần như bằng nhau** (−31,7; −33,0 và −34,3 mm), đúng bằng chiều '
  'cao ảnh phản chiếu — một sai lệch có nguyên nhân vật lý duy nhất thì phải tác động như nhau lên '
  'cả ba vật giống nhau.')
P('Bài học phương pháp luận: **không chọn phương pháp dựa trên con số tổng hợp khi dữ liệu đầu vào '
  'còn chứa lỗi chưa xử lý**. Sự không đồng nhất giữa các mẫu lẽ ra phải được xem là tín hiệu cảnh '
  'báo trước khi so sánh các con số trung bình.')

H2('8.6. Kiểm tra độ tin cậy trên dữ liệu thật')

P('Cờ tin cậy xây dựng ở Chương 5 dựa trên **tỉ lệ nhìn thấy**, tức tỉ số giữa diện tích mặt nạ đo '
  'được và diện tích hình bóng dự đoán. Trên dữ liệu thật, cơ chế này bộc lộ hai khiếm khuyết.')
P('**Khiếm khuyết thứ nhất — ảnh phản chiếu làm phồng tỉ lệ.** Vì ảnh phản chiếu nằm trong mặt nạ, '
  'một lon lành lặn cho tỉ lệ 1,08 đến 1,29 thay vì xấp xỉ 1,00. Cờ tin cậy báo động khi tỉ lệ '
  '**tụt** xuống dưới 0,90, nên xuất phát từ 1,2 nghĩa là vật phải bị che tới khoảng 30 % mới bị '
  'phát hiện — một nửa tác dụng của cơ chế đã mất. Cách sửa: vì vị trí vật nay được suy ra từ mép '
  'trên nên đã biết **chân vật phải nằm ở hàng điểm ảnh nào**; chỉ đếm phần mặt nạ nằm phía trên '
  'hàng đó. Tỉ lệ đo lại được là 0,99 đến 1,02, cơ chế lấy lại toàn bộ dư địa.')
P('**Khiếm khuyết thứ hai — tỉ lệ diện tích tự chuẩn hóa, nên về nguyên tắc không phát hiện được '
  'vị trí sai.** Đây là một tính chất cấu trúc chứ không phải chuyện đặt ngưỡng chưa khéo, và nó '
  'đáng được nêu rõ. Quy trình ước lượng xác định vị trí **trước**, rồi mới dựng hình bóng dự đoán '
  '**tại chính vị trí vừa xác định**. Nếu vùng ảnh lớn hơn thực tế, phép khớp sẽ đẩy vật lại gần '
  'camera hơn; mà ở gần camera thì hình bóng dự đoán **cũng lớn hơn**. Hai đại lượng cùng tăng nên '
  'tỉ số giữa chúng vẫn xấp xỉ 1 ngay cả khi vị trí sai hàng trăm milimét. Thực nghiệm xác nhận '
  'điều này: một vùng ảnh giả mạo cho vị trí sai 284 mm trong khi tỉ lệ nhìn thấy vẫn báo 1,00.')
P('Đại lượng tỉ lệ diện tích chỉ phát hiện được **che khuất**, vì che khuất làm méo *hình dạng* '
  'theo cách mà phép khớp không thể hấp thụ. Muốn phát hiện vị trí sai thì cần một đại lượng mà '
  'phép khớp **không tự điều chỉnh được**.')

H3('8.6.1. Kiểm tra kích thước hình bóng')

P('Đại lượng đó là **bề rộng và chiều cao** của khung bao. Phép khớp chỉ ràng buộc hai điều kiện: '
  'mép trên và tâm ngang của hình bóng. Bề rộng và chiều cao không nằm trong số đó, nên chúng là '
  '**bằng chứng độc lập** mà phép khớp không thể làm cho khớp một cách giả tạo.')
P('Phép đo này phải thực hiện **trên phần nằm phía trên chân vật**, cùng lý do như với tỉ lệ nhìn '
  'thấy. Khi đo trên toàn bộ khung bao, ảnh phản chiếu làm chiều cao đo được lớn hơn dự đoán '
  '16–28 %, buộc phải nới ngưỡng chiều cao một cách không đối xứng để lon lành lặn không bị loại '
  'oan. Khi đo trên phần vật, ba lon lành lặn cho chiều cao lệch **+0 %, −2 % và +0 %** — ngưỡng '
  'trở lại đối xứng và chặt hơn hẳn. Đây là một ví dụ cho thấy việc **chọn đúng miền đo** có giá '
  'trị hơn việc nới ngưỡng cho vừa dữ liệu.')
P('Trên các khung hình thật, ba lon lành lặn cho bề rộng lệch +5 %, +13 % và +8 % so với dự đoán; '
  'một vùng ảnh rộng gấp 2,3 lần và một mảnh vụn 51 điểm ảnh đều bị loại. Ngưỡng cho chiều cao '
  'được đặt **không đối xứng** một cách có chủ ý: nới rộng về phía trên tới 1,60 lần vì ảnh phản '
  'chiếu còn nằm trong khung bao làm lon lành lặn cao hơn dự đoán 16–28 %, nhưng giữ chặt về phía '
  'dưới ở 0,65 lần vì "thấp hơn hẳn" chính là dấu hiệu đặc trưng của một vành nhãn bị tách rời — '
  'rộng bằng cả lon nhưng chỉ cao bằng một phần tư.')

H2('8.7. Kết quả đo sai số trên bàn thật')

P('Phép đo được thực hiện bằng cách đặt từng lon vào các vị trí đã đánh dấu sẵn trên mặt bàn và so '
  'vị trí do hệ thống ước lượng với vị trí đánh dấu. Sáu điểm đo được chương trình **tự chọn** '
  'theo tư thế camera đang đo được, với ràng buộc là hai lon cách nhau tối thiểu và không lon nào '
  'nằm chắn đường nhìn tới lon khác; ba lon luân phiên đổi chỗ qua sáu lượt nên mỗi lon được đo ở '
  'mọi điểm. Tổng cộng 18 phép đo, mỗi phép lấy trung vị của mười lăm khung hình.')
P('Một chi tiết nhỏ nhưng quan trọng về quy ước đặt vật: **tâm đáy lon** phải trùng dấu, không '
  'phải mép lon. Đại lượng được ước lượng là tâm vật, nên đặt mép vào dấu sẽ làm mọi phép đo lệch '
  'thêm đúng một bán kính lon, và sai lệch đó trông y hệt một sai số hệ thống của khối thị giác.')

T('8.5',
  ['Phương pháp', 'Vật', 'Trung bình', 'Lớn nhất', 'Sai lệch hệ thống theo X'],
  [
      ('Khớp mép đáy', 'Lon đỏ', '11,81 mm', '20,55 mm', '−34,3 mm'),
      ('', 'Lon lam', '11,06 mm', '18,36 mm', '−31,7 mm'),
      ('', 'Lon lục', '11,39 mm', '20,55 mm', '−33,0 mm'),
      ('', '**Chung**', '**11,42 mm**', '**20,55 mm**', ''),
      ('Khớp mép trên', 'Lon đỏ', '4,37 mm', '6,07 mm', '+9,4 mm'),
      ('', 'Lon lam', '4,71 mm', '6,31 mm', '+10,2 mm'),
      ('', 'Lon lục', '4,42 mm', '5,99 mm', '+9,2 mm'),
      ('', '**Chung**', '**4,50 mm**', '**6,31 mm**', ''),
  ],
  widths=[3.4, 2.4, 3.0, 3.0, 4.0])

P('Các giá trị trung bình và lớn nhất được quy đổi về không gian ảo để so trực tiếp với dung sai '
  'giác hút 12 mm; sai lệch hệ thống để nguyên theo milimét trên bàn thật cho dễ hình dung.')
P('Phương pháp khớp mép trên đạt **4,50 mm trung bình và 6,31 mm ở trường hợp xấu nhất**, tức '
  '**toàn bộ 18 phép đo nằm trong dung sai**, kể cả trường hợp xấu nhất còn dư gần một nửa. Khi '
  'trừ đi thành phần sai lệch hệ thống thì phần còn lại chỉ 2,35 mm, cho thấy **bản thân phép đo '
  'rất ổn định** và phần sai số chủ yếu là sai lệch của mô hình chứ không phải nhiễu ngẫu nhiên.')
P('Thành phần sai lệch hệ thống +9,6 mm đã được truy nguyên. Giả thuyết đầu tiên — chiều cao lon '
  'khai trong chương trình không đúng — bị **bác bỏ bằng tính toán**: sai chiều cao sẽ sinh ra sai '
  'lệch **tăng dần** theo khoảng cách tới camera, trong khi sai lệch đo được **giảm dần** '
  '(+12,5; +12,4 và +3,9 mm tại ba khoảng cách khảo sát). Nguyên nhân thực sự nằm ở vị trí các '
  'điểm mốc: đo riêng từng marker cho thấy hai marker lệch 26 và 29 mm so với tọa độ thiết kế, làm '
  'sai số ngoại tham số tăng từ 0,93 lên 1,96 mm quy đổi. Hướng khắc phục là **đo lại tọa độ thật '
  'của các marker bằng thước và khai báo đúng giá trị đo được** — các điểm mốc không cần nằm đúng '
  'chỗ thiết kế, chỉ cần vị trí của chúng được **biết chính xác**.')

T('8.6',
  ['Tiêu chí', 'Mô phỏng (Chương 7)', 'Bàn thật (Chương 8)'],
  [
      ('Sai số định vị trung bình', '1,13 mm', '4,50 mm'),
      ('Sai số lớn nhất', '6,2 mm', '6,31 mm'),
      ('Tỉ lệ nằm trong dung sai 12 mm', '100 %', '100 %'),
      ('Độ phân giải cảm biến', '640×480', '1280×720'),
      ('Góc chúc của camera', '32°', '45,2°'),
      ('Phương pháp tách nền', 'Lấy ngưỡng theo màu và độ sáng', 'Trừ theo ảnh nền tham chiếu'),
      ('Đặc trưng hình học dùng để định vị', 'Mép đáy', 'Mép trên'),
      ('Nguồn sai số chính', 'Che khuất một phần', 'Vị trí các điểm mốc hiệu chuẩn'),
  ],
  widths=[5.4, 5.2, 5.2])

P('Sai số thật lớn gấp khoảng bốn lần mô phỏng, điều hoàn toàn hợp lý khi tính đến méo ống kính, '
  'nhiễu cảm biến, sai số dán các điểm mốc và sai số của chính phép đo đối chứng bằng thước. Điều '
  'đáng chú ý hơn là **sai số lớn nhất của hai bên gần như bằng nhau**: mô phỏng có những trường '
  'hợp che khuất nặng đẩy sai số lên 6,2 mm, còn hệ thống thật thì ổn định quanh mức trung bình. '
  'Nói cách khác, hệ thống thật kém chính xác hơn nhưng **đồng đều hơn**.')

H2('8.8. Giới hạn đã xác định')

P('Hai giới hạn được ghi nhận rõ ràng ở thời điểm viết khóa luận.')

H3('8.8.1. Hai vật đứng chạm nhau trong ảnh')

P('Bộ nhận dạng dùng cho camera thật tách nền trước rồi mới phân loại từng **vùng liên thông** '
  'theo màu chiếm ưu thế. Khi hai lon đứng đủ gần để hình ảnh của chúng chạm nhau — và điều này '
  'xảy ra sớm hơn trực giác, vì chỉ cần hai hình bóng **chạm mép**, chưa cần che nhau — chúng trở '
  'thành một vùng duy nhất, được gán một danh tính duy nhất, và vùng đó có kích thước gấp nhiều '
  'lần một lon nên bị phép kiểm tra hình dáng loại bỏ.')
P('Hậu quả nặng hơn vẻ ngoài của nó. Vật bị che thì đương nhiên không định vị được, nhưng **vật '
  'không bị che cũng mất theo**, và vì khâu chọn ứng viên lấy vùng lớn nhất của mỗi màu nên **lon '
  'thứ ba đứng riêng một chỗ cũng bị vạ lây**: vùng gộp lớn hơn nó, giành mất lớp màu, rồi bị '
  'loại. Một lần chạm nhau làm hỏng toàn bộ cảnh.')
P('Giải pháp đã cài đặt gồm hai phần. Thứ nhất, khâu chọn ứng viên **ưu tiên hình dáng trước kích '
  'cỡ**: giữ mọi vùng của một màu rồi chọn vùng đạt phép kiểm tra hình dáng, thay vì chốt vùng lớn '
  'nhất khi còn chưa biết vùng nào hợp lệ. Thứ hai, vùng nào đã trượt phép kiểm tra thì được **tách '
  'theo màu**: điểm ảnh thuộc từng lớp màu làm hạt giống, phần không mang màu (nắp bạc, vành nhãn) '
  'về hạt giống **gần nhất theo khoảng cách**.')
P('Ba lựa chọn kỹ thuật trong phần tách này đều được chọn sau khi cách làm hiển nhiên hơn đã thất '
  'bại, nên đáng ghi lại.')
N([
    '**Không dùng thuật toán phân vùng theo đường phân thủy** (watershed), dù đó là công cụ quen '
    'thuộc cho bài toán tách vùng chạm nhau. Nó đi theo gradient độ sáng, mà vỏ lon kim loại có '
    'vệt lóa nên đường biên chạy loằng ngoằng sang vật bên cạnh: mảnh thu được rộng gấp đôi một '
    'lon mà chỉ đặc 0,53, và nó lấy mất khoảng 30 % điểm ảnh của lon kề bên. Phép gán theo khoảng '
    'cách cho đường biên **thẳng đứng**, đúng với hình học hai hình trụ đứng cạnh nhau, và không '
    'phụ thuộc độ sáng.',
    '**Phải tính khoảng cách riêng cho từng màu.** Hàm biến đổi khoảng cách kèm nhãn của thư viện '
    'đánh nhãn theo **thành phần liên thông** của tập hạt giống; mà hai lon chạm nhau thì hạt '
    'giống hai màu cũng chạm nhau nên gộp thành một thành phần, và toàn bộ vùng về màu nào có '
    'nhiều điểm ảnh hơn.',
    '**Chỉ mảng lớn nhất của mỗi màu được làm hạt giống.** Nhãn lon mang nhiều màu: logo Pepsi có '
    'mảng đỏ, lon 7Up có vành đỏ. Những mảng đó nằm trên vật khác nhưng vẫn là "đỏ", nên nếu dùng '
    'làm hạt giống thì chúng kéo cả vùng quanh vật kia về phía vật mang màu đó.',
])

T('8.7',
  ['Tình huống', 'Trước khi tách vùng', 'Sau khi tách vùng'],
  [
      ('Lon đứng riêng, cùng cảnh', 'Mất (bị vùng gộp giành lớp màu)',
       'Nhận đúng, tỉ lệ nhìn thấy 1,02, tin cậy'),
      ('Lon phía trước (không bị che)', 'Mất', 'Tách ra đúng kích thước, vẫn bị từ chối'),
      ('Lon phía sau (bị che một phần)', 'Mất', 'Tách ra đúng kích thước, tỉ lệ nhìn thấy 0,71–0,80'),
      ('Ngưỡng tỉ lệ nhìn thấy', '0,90', '0,90 (giữ nguyên)'),
  ],
  widths=[5.0, 5.4, 5.4])

P('Như Bảng 8.7 cho thấy, phần tách vùng đã lấy lại được **lon đứng riêng** — tức chấm dứt việc '
  'một lần chạm nhau làm hỏng cả cảnh — nhưng **hai lon chạm nhau vẫn bị từ chối**, vì tỉ lệ nhìn '
  'thấy của chúng rơi xuống 0,71–0,80 trong khi ngưỡng là 0,90.')
P('Việc **giữ nguyên ngưỡng 0,90** là một quyết định có ý thức. Ngưỡng này là thứ bảo đảm mệnh đề '
  '"hễ hệ thống báo tin cậy thì sai số nằm trong dung sai gắp"; hạ nó xuống cho hai lon kia lọt '
  'qua thì mọi vật bị che một phần cũng lọt, và robot sẽ hút lệch tâm — đúng kiểu hỏng đã gặp và '
  'đã sửa ở Chương 6. Con số báo cáo sẽ đẹp hơn trong khi hệ thống tệ đi.')
P('Một hướng sửa đã **thử và bác bỏ** cũng nên ghi lại. Phần còn trượt là bề rộng của mảnh đỏ, bị '
  'phồng vì hai vệt phản chiếu dính liền nhau và được gán cho một vật. Đã thử đo bề rộng bằng '
  '**trung vị theo từng hàng** và bằng **phân vị 85–95** để né mấy hàng dị thường đó. Cả hai đều '
  'tệ hơn: mặt nạ do trừ nền sinh ra có mép lởm chởm nên chỉ đặc khoảng 0,68 so với khung bao, và '
  'trung vị kéo **lon lành lặn** xuống −25 % so với dự đoán. Nói cách khác, cách sửa đó phá hỏng '
  'trường hợp thường gặp để cứu một trường hợp hiếm — một đánh đổi sai hướng.')
P('**Điều kiện vận hành rút ra:** các vật cần đặt cách nhau ít nhất một bề rộng vật (khoảng 60 mm '
  'trên bàn thật). Trong điều kiện đó, hệ thống nhận đủ ba lon với tỉ lệ nhìn thấy 1,01–1,06 và '
  '93/93 khung hình đều tin cậy. Đây là một ràng buộc bố trí, không phải một lỗi ngẫu nhiên: hệ '
  'thống **hỏng một cách an toàn** — nó từ chối chứ không đưa ra vị trí sai — nên ràng buộc này '
  'không gây rủi ro cho thao tác gắp, chỉ giới hạn các bố trí có thể dùng.')
H3('8.8.2. Mỗi màu chỉ ứng với đúng một vật')

P('**Mỗi màu chỉ ứng với đúng một vật.** Toàn bộ chuỗi xử lý, từ khâu nhận dạng tới khâu '
  'lập kế hoạch, đều giả định ba vật có ba màu phân biệt và gọi vật theo tên. Muốn xử lý nhiều vật '
  'cùng màu thì phải chuyển từ mô hình "ba vật biết trước" sang mô hình "N thực thể phát hiện '
  'được", kéo theo thay đổi ở hầu hết các module. Đây là phần việc lớn nhất còn lại và được xếp '
  'vào hướng phát triển.')

H1('Chương 9. BẢN SAO SỐ VÀ ĐIỀU KHIỂN BÁM THEO VẬT')

P('Chương 8 dừng lại ở chỗ hệ thống biết vị trí của các vật thật trong hệ tọa độ ảo. Chương này '
  'khép kín vòng điều khiển: vị trí đó được ghi vào mô phỏng để các vật ảo đi theo các vật thật, '
  'và robot được điều khiển bám theo vật ảo. Kết quả là một chuỗi hoàn chỉnh từ thế giới thật tới '
  'chuyển động của robot.')

H2('9.1. Bản sao số: khái niệm và mức độ tích hợp')

P('Thuật ngữ "bản sao số" (digital twin) được dùng khá rộng rãi và không phải lúc nào cũng nhất '
  'quán. Cách phân loại của Kritzinger và cộng sự phân biệt ba mức theo **chiều luồng dữ liệu '
  'giữa đối tượng thật và mô hình số**, và cách phân loại này giúp xác định chính xác hệ thống '
  'trong khóa luận thuộc mức nào.')

T('9.1',
  ['Mức', 'Luồng dữ liệu', 'Đặc điểm'],
  [
      ('Mô hình số', 'Không tự động theo chiều nào',
       'Mô hình được dựng và cập nhật thủ công; thay đổi ở vật thật không tự phản ánh vào mô hình'),
      ('Bóng số', 'Tự động một chiều: thật → số',
       'Trạng thái vật thật tự động cập nhật vào mô hình; mô hình không tác động ngược lại'),
      ('Bản sao số', 'Tự động hai chiều',
       'Mô hình cũng điều khiển ngược lại đối tượng thật'),
  ],
  widths=[3.0, 4.6, 8.2])

P('Hệ thống trong khóa luận này đạt mức **bóng số** theo đúng định nghĩa: vị trí các lon thật tự '
  'động cập nhật vào mô phỏng, nhưng mô phỏng không tác động ngược lại các lon thật. Chiều ngược '
  'lại sẽ chỉ hoàn chỉnh khi có một robot vật lý thực hiện thao tác trên bàn thật, nằm ngoài phạm '
  'vi đề tài. Việc nêu rõ điều này quan trọng hơn là dùng thuật ngữ cho kêu: phần đã làm được là '
  'luồng nhận thức tự động từ thật sang số, và đó cũng chính là phần khó về mặt thị giác máy tính.')
P('Một điểm cần làm rõ về vai trò của các điểm mốc: chúng **không định nghĩa camera mà định nghĩa '
  'hệ quy chiếu chung** giữa hai thế giới. Nhờ vậy, khi camera bị dời đi hoặc đổi góc nhìn, hệ '
  'thống vẫn cho vị trí vật trong cùng hệ tọa độ cũ — bản sao số không bị ảnh hưởng. Đây chính là '
  'lý do ngoại tham số được giải lại ở từng khung hình như đã trình bày ở mục 8.3.2.')

H2('9.2. Kiến trúc và vị trí của chỗ nối')

P('Chuỗi xử lý hoàn chỉnh gồm sáu khâu:')
CODE([
    'lon thật  ->  camera C270  ->  node thị giác thật  ->  node bản sao số',
    '          ->  lon ảo trong Gazebo  ->  node bám theo  ->  robot',
])
P('Điều đáng chú ý về mặt thiết kế là **chỗ nối giữa hai thế giới mỏng một cách có chủ ý**. Node '
  'bản sao số không đọc ảnh, không biết gì về điểm ảnh, không thực hiện phép đổi tỉ lệ nào: nó '
  'nhận vị trí vật **đã ở trong hệ tọa độ ảo** và chỉ cộng thêm cao độ của đế robot trước khi ghi '
  'vào mô phỏng. Toàn bộ công việc chuyển đổi đã được thực hiện ở tầng dưới, mà như đã trình bày ở '
  'mục 8.1.1, phần lớn lại không cần làm gì cả vì tọa độ ảo đã được đưa vào ngay từ khâu hiệu '
  'chuẩn. Một chỗ nối mỏng như vậy dễ kiểm chứng và dễ thay thế: muốn đổi nguồn vị trí vật, chỉ '
  'cần thay node phía trước.')
IMG('9.1')

P('Hình 9.1 là công cụ quan sát dùng trong quá trình kiểm chứng. Ba cột tọa độ là cùng một vật '
  'nhìn từ ba chỗ: camera đo được trên bàn thật; cũng số đó chia cho hệ số tỉ lệ, tức tọa độ mà '
  'khối điều khiển thật sự dùng; và vị trí vật ảo **đang nằm** trong Gazebo đọc ngược từ odometry. '
  'Cột cuối là khoảng cách giữa hai cột sau, thường dưới 2 mm; nó chỉ lớn khi bản sao số **cố ý '
  'không ghi**, nên cột này không đo sai số mà cho thấy các lớp lọc ở mục 9.3 đang làm việc.')

P('Về mặt kỹ thuật, việc ghi vị trí vào Gazebo được thực hiện qua **dịch vụ đã được cầu nối sang '
  'ROS**. Lựa chọn này xuất phát từ một phép đo: gọi công cụ dòng lệnh của Gazebo bằng tiến trình '
  'con mất khoảng 0,37 giây mỗi lần, nên ba vật đã mất hơn một giây — không thể theo kịp camera '
  'chạy ở 10 hình/giây. Khi cầu nối thành dịch vụ ROS thì mỗi lệnh ghi chỉ là một lời gọi dịch vụ '
  'thông thường. Lời gọi phải thực hiện **bất đồng bộ**: gọi đồng bộ bên trong một hàm xử lý sự '
  'kiện sẽ gây khóa chết, vì hàm đó chờ phản hồi trong khi phản hồi lại cần chính bộ điều phối '
  'đang bị chiếm để xử lý.')

H2('9.3. Những gì bản sao số từ chối làm')

P('Phần lớn chất lượng của node bản sao số không nằm ở những gì nó làm mà ở những gì nó **từ chối '
  'làm**. Mỗi quy tắc dưới đây đều ra đời từ một tình huống hỏng quan sát được.')

T('9.2',
  ['Quy tắc', 'Căn cứ'],
  [
      ('Bỏ qua vật mà cờ tin cậy nghi ngờ',
       'Ghi một vị trí không tin được vào mô phỏng là làm hỏng trạng thái của cả cảnh; giữ nguyên '
       'vị trí cũ là lựa chọn an toàn vì vật không tự di chuyển'),
      ('Chỉ ghi khi vật đã dịch quá 6 mm trên bàn thật',
       'Nhiễu đo được là 0,5 – 0,9 mm; ghi lại vị trí ở mỗi khung hình sẽ dịch cứng vật ảo mười '
       'lần mỗi giây, không cho bộ giải vật lý kịp làm việc'),
      ('Không đụng tới vật mà giác hút đang giữ',
       'Khi robot đang giữ vật thì vị trí vật ảo do robot quyết định; camera cũng không nhìn thấy '
       'vật thật nào đang bay vì vật thật vẫn nằm trên bàn'),
      ('Cú dịch chuyển xa phải được năm khung hình liên tiếp xác nhận',
       'Ràng buộc vật lý: một lon không thể dịch 284 mm trong một phần mười giây. Khi người dùng '
       'nhấc lon đặt sang chỗ khác thì vị trí mới **trụ lại**, còn nhiễu thoáng qua thì không'),
  ],
  widths=[5.6, 10.2])

P('Quy tắc cuối cùng đáng được giải thích thêm vì nó bổ khuyết cho một điểm yếu đã phân tích ở mục '
  '8.6: cờ tin cậy dựa trên tỉ lệ diện tích **về nguyên tắc không phát hiện được vị trí sai**. Khi '
  'tất cả các phép kiểm tra dựa trên một khung hình đơn lẻ đều có thể bị đánh lừa, ràng buộc còn '
  'lại phải đến từ **mối quan hệ giữa các khung hình**, và ràng buộc tự nhiên nhất là tính liên '
  'tục của chuyển động vật lý. Điều tinh tế là phép lọc phải phân biệt được "nhảy đi rồi quay về" '
  'với "nhảy đi rồi ở lại": một bộ lọc chặn mọi cú nhảy thì sạch nhiễu nhưng cũng vô dụng vì nó '
  'chặn luôn cả chuyển động thật. Yêu cầu xác nhận qua nhiều khung hình giải quyết được cả hai, '
  'với cái giá là độ trễ nửa giây khi vật được đặt sang vị trí mới.')
P('Cách tiếp cận này trùng tinh thần với cơ chế **trí nhớ quan sát** đã xây dựng ở Chương 6 cho '
  'bài toán che khuất giữa các vật: trong cả hai trường hợp, lời giải đều là không tin vào một '
  'khung hình đơn lẻ.')

H3('9.3.1. Kiểm chứng các lớp lọc')

P('Các lớp lọc được kiểm chứng bằng cách cố ý tạo nhiễu: người thực hiện đưa tay vào khung hình và '
  'di chuyển các lon nhiều lần trong khi hệ thống chạy. Trong toàn bộ quá trình, **không có cú '
  'dịch chuyển giả nào** được ghi vào mô phỏng.')
P('Dấu vết hoạt động của từng lớp được ghi lại trong nhật ký. Lớp kiểm tra kích thước hình bóng đã '
  'loại bỏ hoàn toàn các lon bị tay che — thể hiện qua 25 lần hệ thống báo chỉ nhìn thấy một hoặc '
  'hai vật thay vì ba. Lớp xác nhận nhiều khung hình đã giữ lại 12 khung hình có cú nhảy xa chưa '
  'được xác nhận. Quan trọng nhất, **trong cùng khoảng thời gian đó hai lon được di chuyển thật sự '
  '170 mm và 177 mm, và cả hai đều tới đúng vị trí mới** — bộ lọc chặn nhiễu mà không chặn nhầm '
  'chuyển động thật.')
P('Sự phân công giữa hai lớp khá rõ ràng và đáng ghi nhận: lớp kiểm tra hình dáng nói *"tôi không '
  'biết vật ở đâu"* — thà im lặng còn hơn đoán bừa; lớp xác nhận nói *"vị trí mới này phải trụ lại '
  'đã"* — phân biệt chuyển động thật với nhiễu thoáng qua.')

H2('9.4. Điều khiển bám theo vật')

P('Khâu cuối cùng là đưa robot bám theo vật. Có một lựa chọn thiết kế cần giải thích: node bám '
  'theo **lấy vị trí từ vật ảo trong mô phỏng chứ không lấy thẳng kết quả của khối thị giác**. Lý '
  'do là vị trí vật ảo đã đi qua toàn bộ các lớp lọc mô tả ở mục 9.3, nên robot thừa hưởng các cơ '
  'chế bảo vệ đó và không bao giờ lao theo một khung hình nhiễu. Đây cũng là cách thể hiện đúng '
  'chuỗi mà đề tài muốn chứng minh: thế giới thật điều khiển robot **thông qua** bản sao số.')
P('Về mặt điều khiển, bài toán bám đuổi khác hẳn bài toán đi tới một điểm. Bộ điều khiển xây dựng '
  'ở Chương 4 lập trọn quỹ đạo rồi mới chạy — đúng cho lệnh "đi tới đó" nhưng sai cho bám đuổi, vì '
  'đích thay đổi ngay trong lúc robot đang di chuyển. Vì vậy một **vòng điều khiển kiểu servo** '
  'được xây dựng: ở mỗi nhịp, điểm lệnh được kéo về phía đích một đoạn ngắn có giới hạn bởi tốc độ '
  'tối đa, rồi giải động học ngược và phát lệnh khớp.')
P('Chính giới hạn tốc độ là cơ chế làm mượt. Camera cập nhật ở 10 hình/giây còn vòng điều khiển '
  'chạy ở 50 nhịp/giây, nên một bước nhảy của ước lượng được rải ra thành nhiều nhịp nhỏ thay vì '
  'làm robot giật một cái. Ba cơ chế an toàn được bổ sung: một vùng chết 1,5 mm để robot không '
  'rung quanh đích vì nhiễu đo; một ngưỡng thời gian hai giây, quá hạn đó mà không nhận được vị '
  'trí mới thì robot dừng tại chỗ thay vì bám theo số liệu cũ; và khi điểm đích nằm ngoài tầm với '
  'thì robot giữ nguyên vị trí hợp lệ gần nhất thay vì nhích tiếp cho tới khi động học ngược không '
  'còn nghiệm.')
P('Cao độ bám được chọn sao cho mặt dưới bàn máy cách đỉnh lon 60 mm trên bàn thật, đủ để quan sát '
  'thấy rõ robot đang bám chứ không chạm vào vật.')

T('9.3',
  ['Phép đo', 'Kết quả'],
  [
      ('Sai lệch bám khi vật đứng yên', '3 mm trên bàn thật'),
      ('Sai lệch bám khi vật đang di chuyển', '3 – 4 mm, giữ ổn định suốt quá trình'),
      ('Quãng đường vật di chuyển trong phép thử', '79 mm rồi 170 mm'),
      ('Sai lệch cao độ so với lệnh', '0,2 mm khi đứng yên; 0,3 mm khi đang di chuyển ngang'),
      ('Ảnh hưởng của vật khác di chuyển cùng lúc', 'Không — robot không bị kéo theo vật thứ hai '
       'dịch 177 mm trong cùng khoảng thời gian'),
  ],
  widths=[7.4, 8.4])

P('Kết quả cho thấy robot bám ổn định, không dao động quanh đích và không bị chùng cao độ khi di '
  'chuyển ngang. Việc robot **không bị kéo theo** một vật khác đang di chuyển cùng lúc tuy đơn '
  'giản nhưng là bằng chứng rằng khâu gán danh tính vật hoạt động đúng trong điều kiện động.')

H2('9.5. Tổng hợp sai số toàn chuỗi')

P('Ghép các kết quả của Chương 8 và Chương 9 lại, có thể theo dõi sai số tích lũy qua từng khâu: '
  'khối thị giác ước lượng vị trí vật với sai số **4,50 mm** quy đổi; bản sao số chép vị trí đó '
  'sang mô phỏng với sai lệch dưới **1 mm** trên bàn thật, phần lớn là do vùng chết cố ý; và robot '
  'bám theo với sai lệch **3 – 4 mm** trên bàn thật.')
P('Cần lưu ý rằng ba con số này không cộng trực tiếp được vì chúng đo trong các hệ quy chiếu khác '
  'nhau và một phần sai số là hệ thống chứ không ngẫu nhiên. Điều có thể khẳng định là toàn bộ '
  'chuỗi hoạt động trong phạm vi dung sai của thao tác gắp, và khâu quyết định độ chính xác tổng '
  'thể vẫn là **khối thị giác**, đúng như kỳ vọng đối với một đề tài lấy thị giác máy tính làm '
  'trọng tâm.')

H1('KẾT LUẬN')

H2('1. Các kết quả chính đã đạt được')

P('Khóa luận đã xây dựng hoàn chỉnh một hệ thống trong đó thị giác máy tính cung cấp vị trí vật '
  'thể cho robot delta ba bậc tự do thực hiện thao tác gắp–thả tự động trong môi trường mô phỏng '
  'ROS 2 và Gazebo. Các kết quả cụ thể gồm:')
N([
    'Xây dựng và kiểm chứng **mô hình động học** của robot delta dạng quay: công thức động học '
    'ngược dạng đóng giải bằng phép thế Weierstrass kèm tiêu chí chọn nhánh khuỷu ra ngoài, và '
    'công thức động học thuận bằng phép giao ba mặt cầu. Vòng lặp ngược–thuận trên 5 424 điểm cho '
    'sai số dưới 5×10⁻¹³ m; trên mô phỏng vật lý, sai lệch vị trí bàn máy nhỏ hơn 1 mm.',
    'Xây dựng **môi trường tương tác** gồm bàn, ba vật thể có hình dạng và màu khác nhau, khay ba '
    'ô, sáu marker hiệu chuẩn và một giác hút ảo có dung sai giống giác hút thật.',
    'Xây dựng **bộ quy hoạch quỹ đạo** biên dạng bậc năm với quỹ đạo an toàn ba đoạn và cơ chế '
    'kiểm tra trước toàn tuyến, cùng **lớp lệnh cấp cao** có khả năng tự kiểm chứng kết quả sau '
    'mỗi thao tác.',
    'Xây dựng **khối thị giác** hoàn chỉnh: nhận dạng vật theo màu trong không gian HSV; hiệu '
    'chuẩn ngoại tham số camera bằng sáu marker ArUco đạt sai lệch vị trí 0,35 mm và sai lệch '
    'hướng 0,017°; chuyển tọa độ ảnh sang tọa độ robot bằng phép giao tia với mặt phẳng; và bộ '
    'ước lượng có xét che khuất dựa trên hình bóng dự đoán.',
    '**Đánh giá định lượng** trên bộ dữ liệu 172 ảnh có vị trí thật làm đối chứng: sai số ngang '
    'trung bình 1,13 mm trong vùng robot gắp được, 100% số mẫu nằm trong dung sai 12 mm; cơ chế '
    'khớp mép trên giảm sai số với vật trong khay từ 13,44 mm xuống 1,01 mm; cờ tin cậy bắt được '
    '100% số ước lượng sai quá 5 mm.',
    '**Tích hợp toàn hệ thống**: robot điều khiển hoàn toàn bằng camera gắp và thả đúng 30/30 vật '
    'trong 10 bố trí ngẫu nhiên, bằng đúng kết quả khi dùng vị trí thật từ mô phỏng.',
    'Chuyển hệ thống sang **camera thật**: hiệu chuẩn nội tham số đạt sai số chiếu lại 0,222 điểm '
    'ảnh và ngoại tham số đạt 0,93 mm quy đổi; thay phương pháp lấy ngưỡng bằng **trừ nền theo ảnh '
    'tham chiếu**; chuyển đặc trưng định vị từ mép đáy sang **mép trên** để tránh ảnh phản chiếu; '
    'và bổ sung **kiểm tra kích thước hình bóng** để loại các vùng ảnh giả mạo. Sai số định vị đo '
    'được trên bàn thật là 4,50 mm trung bình và 6,31 mm lớn nhất, toàn bộ nằm trong dung sai.',
    'Xây dựng **bản sao số** ở mức bóng số: vị trí lon thật tự động cập nhật sang mô phỏng với sai '
    'lệch dưới 1 mm, có bốn lớp lọc bảo vệ mà phép thử cố ý gây nhiễu không phá được.',
    'Xây dựng **chế độ bám theo vật** bằng vòng điều khiển servo: robot bám vật đang di chuyển với '
    'sai lệch 3 – 4 mm, giữ cao độ trong 0,3 mm, khép kín chuỗi từ vật thật tới chuyển động robot.',
])

H2('2. Đóng góp của đồ án')

P('Về mặt kỹ thuật, đóng góp đáng kể nhất là **cơ chế ước lượng vị trí có xét che khuất**: dùng '
  'hình bóng dự đoán của vật để vừa phát hiện tình trạng bị che, vừa khôi phục vị trí đúng trong '
  'trường hợp vật nằm trong khay. Cách làm này chỉ cần mô hình hình học của vật và mô hình camera '
  'đã hiệu chuẩn, không cần thêm cảm biến hay dữ liệu huấn luyện.')
P('Từ phần làm với camera thật, đóng góp đáng kể là **phép kiểm tra kích thước hình bóng**. Nó '
  'xuất phát từ một nhận xét có tính cấu trúc: phép kiểm tra dựa trên tỉ lệ diện tích **tự chuẩn '
  'hóa** nên về nguyên tắc không thể phát hiện vị trí sai, vì quy trình ước lượng xác định vị trí '
  'trước rồi mới dựng hình bóng dự đoán tại chính vị trí đó. Bề rộng và chiều cao của khung bao '
  'không nằm trong các ràng buộc của phép khớp nên chúng là bằng chứng độc lập, và thực nghiệm cho '
  'thấy chúng loại được đúng những vùng ảnh giả mạo mà tỉ lệ diện tích bỏ lọt.')
P('Cũng từ phần này, việc **đưa tọa độ đã thu nhỏ vào ngay khâu hiệu chuẩn** thay vì quy đổi kết '
  'quả về sau là một thủ thuật đơn giản nhưng hiệu quả: nhờ tính chất của phép chiếu phối cảnh, '
  'toàn bộ khối thị giác xây dựng cho mô phỏng chạy nguyên vẹn trên dữ liệu thật mà không phải sửa '
  'dòng nào.')
P('Về mặt phương pháp, đồ án đề xuất và áp dụng nhất quán một quy trình làm việc: mọi khâu đều '
  'được đo sai số riêng bằng đối chứng từ mô phỏng; mọi thao tác đều được kiểm chứng sau khi thực '
  'hiện; mọi ngưỡng đều được chọn bằng dữ liệu thay vì bằng cảm tính; và phần tính toán được tách '
  'khỏi nền tảng để kiểm thử tự động. Kiến trúc tách **nhận thức** khỏi **phần cứng** giữ cho kết '
  'quả thí nghiệm trung thực với điều kiện của hệ thống thật.')

H2('3. Hướng phát triển')

P('Bốn hướng tiếp theo đã được chuẩn bị sẵn nền tảng trong đồ án này:')
N([
    '**Định vị được vật bị che một phần.** Phần tách vùng gộp trình bày ở mục 8.8.1 đã lấy lại '
    'được các vật không bị che, nhưng hai vật chạm nhau vẫn bị từ chối vì tỉ lệ nhìn thấy của '
    'chúng rơi xuống 0,71–0,80 dưới ngưỡng 0,90. Ngưỡng này không nên hạ; hướng đúng là **thay đại '
    'lượng dùng để định vị**: khi một phần vật bị che, mép trên và tâm ngang không còn đủ, nhưng '
    'đường bao của phần còn nhìn thấy vẫn chứa thông tin — có thể khớp hình bóng dự đoán với phần '
    'quan sát được thay vì chỉ với hai đặc trưng.',
    '**Chuyển từ mô hình "ba vật biết trước" sang "N thực thể phát hiện được".** Giả định mỗi màu '
    'ứng với đúng một vật nằm xuyên suốt toàn bộ chuỗi xử lý, từ khâu nhận dạng tới khâu lập kế '
    'hoạch gọi vật theo tên. Gỡ bỏ giả định này là điều kiện cần để xử lý nhiều vật cùng loại, và '
    'cũng mở đường cho việc **đo chiều cao vật bằng camera đơn** — bài toán ngược của phép khớp '
    'mép trên, trong đó đáy vật trên mặt bàn cho tọa độ ngang còn mép trên cho chiều cao.',
    '**Khép kín chiều còn lại của bản sao số.** Hệ thống hiện đạt mức bóng số: thông tin chảy tự '
    'động từ thật sang số. Chiều ngược lại đòi hỏi một robot vật lý thao tác trên bàn thật, khi đó '
    'mô phỏng trở thành nơi lập kế hoạch và kiểm tra trước khi thực thi.',
    '**Mở rộng phạm vi nhận dạng**: nhận dạng vật theo hình dạng hoặc bằng mô hình học sâu để '
    'không còn phụ thuộc vào màu đã biết trước; ước lượng cả góc xoay của vật để gắp được vật '
    'không đối xứng; và xử lý vật chuyển động trên băng tải.',
])
P('Ngoài ra, một số cải tiến nhỏ đã được xác định rõ trong quá trình thực hiện: chuyển bộ sinh quỹ '
  'đạo sang dùng đồng hồ mô phỏng; bổ sung mô hình hình bóng cho hộp bị xoay; và bố trí lại camera '
  'hoặc dùng hai camera để loại bỏ hẳn vùng bị che.')

# ============================================================================ PHỤ LỤC
H1('PHỤ LỤC')

H2('Phụ lục A. Thông số của hệ thống')

T('A.1',
  ['Đại lượng', 'Ký hiệu', 'Giá trị'],
  [
      ('Bán kính đế cố định', 'f', '0,0417 m'),
      ('Bán kính bàn máy động', 'e', '0,0276 m'),
      ('Chiều dài cánh tay trên', 'r_f', '0,0758 m'),
      ('Chiều dài thanh chống', 'r_e', '0,1668 m'),
      ('Góc pha ba chân', 'φ₁, φ₂, φ₃', '0°, 120°, 240°'),
      ('Giới hạn khớp chủ động', 'θ_min, θ_max', '−1,0297 rad; 1,4312 rad'),
      ('Vị trí gốc của bàn máy', 'P_home', '(0; 0; −0,1405) m'),
      ('Bề dày đầu công tác', '—', '6 mm (± 3 mm quanh tâm)'),
      ('Dung sai lệch tâm khi hút', '—', '12 mm'),
      ('Khoảng khe cho phép khi hút', '—', 'từ −4 mm tới +6 mm'),
  ],
  widths=[6.5, 3.5, 6.0], size=11)

T('A.2',
  ['Đại lượng', 'Giá trị'],
  [
      ('Cao độ mặt bàn', '−0,220 m'),
      ('Cao độ đáy khay', '−0,217 m'),
      ('Tâm khay', '(0,0375; 0,065) m'),
      ('Kích thước lòng khay', '70 × 70 mm, thành cao 20 mm'),
      ('Ô thả A / B / C', '(0,0205; 0,048) / (0,0545; 0,048) / (0,0205; 0,082) m'),
      ('Kích thước vật', 'hộp 30 mm; trụ r = 15 mm cao 30 mm; cầu r = 15 mm'),
      ('Vị trí marker hiệu chuẩn (số hiệu 0 – 5)',
       '(−0,130; 0,075), (−0,130; −0,075), (−0,025; 0,145), (−0,025; −0,145), '
       '(0,140; 0,085), (0,140; −0,085) m'),
      ('Cạnh ô đen của marker', '50 mm'),
      ('Tư thế quan sát', '(0; 0; −0,110) m'),
  ],
  widths=[6.0, 10.0], size=11)

H2('Phụ lục B. Hướng dẫn cài đặt và chạy hệ thống')

P('Môi trường: Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic, OpenCV 4.6.', indent=False)
P('Biên dịch phần mềm điều khiển:', indent=False)
CODE([
    'cd ~/ros2_closed_loop_ws',
    'source /opt/ros/jazzy/setup.bash',
    'colcon build --packages-select delta_controller',
    'source install/setup.bash',
])
P('Khởi động mô phỏng đầy đủ (robot, vật thể, khay, camera, giác hút, khối thị giác):', indent=False)
CODE(['ros2 launch delta_controller pick_place.launch.py'])
P('Mở giao diện điều khiển ở một cửa sổ dòng lệnh khác:', indent=False)
CODE([
    'ros2 run delta_controller cartesian_control',
    '',
    '# Một số lệnh ví dụ:',
    'vat                 # liệt kê vị trí và trạng thái các vật',
    'nguon camera        # dùng vị trí từ thị giác (mặc định)',
    'don                 # dọn mọi vật trên bàn vào khay',
    'reset               # đưa mọi vật trong khay về chỗ cũ',
])
P('Hiệu chuẩn lại camera (khi đổi vị trí camera hoặc chuyển sang camera thật):', indent=False)
CODE(['ros2 run delta_controller calibrate_camera'])
P('Chạy kiểm thử tự động và các thí nghiệm đánh giá:', indent=False)
CODE([
    'colcon test --packages-select delta_controller && colcon test-result --verbose',
    'python3 src/delta_controller/scripts/record_vision_dataset.py   # thu bộ dữ liệu',
    'python3 src/delta_controller/scripts/evaluate_vision.py         # phân tích sai số',
    'python3 src/delta_controller/scripts/run_pick_place_trials.py   # thí nghiệm gắp–thả',
])

H2('Phụ lục C. Danh mục mã nguồn')

T('C.1',
  ['Tệp', 'Số dòng', 'Chức năng'],
  [
      ('delta_kinematics.py', '181', 'Động học thuận và ngược'),
      ('trajectory.py', '85', 'Biên dạng bậc năm và quỹ đạo an toàn'),
      ('scene.py', '93', 'Mô tả cảnh: vật, khay, ô thả, marker, tư thế quan sát'),
      ('gripper_logic.py', '75', 'Điều kiện hút của giác hút'),
      ('task_planner.py', '305', 'Lập kế hoạch cho lệnh cấp cao'),
      ('task_executor.py', '263', 'Thực thi và kiểm chứng kế hoạch'),
      ('color_detector.py', '116', 'Phân đoạn màu và nhận dạng vật trên ảnh'),
      ('camera_model.py', '141', 'Mô hình camera, phép chiếu, hiệu chuẩn PnP'),
      ('vision_estimation.py', '149', 'Hình bóng dự đoán, khớp mép trên, cờ tin cậy'),
      ('vision_eval.py', '152', 'Công cụ đánh giá sai số ngoại tuyến'),
      ('cartesian_control_node.py', '442', 'Node điều khiển chính và giao diện dòng lệnh'),
      ('gripper_node.py', '222', 'Node điều khiển giác hút'),
      ('vision_node.py', '174', 'Node thị giác'),
      ('calibrate_camera_node.py', '166', 'Node hiệu chuẩn camera'),
      ('joint_commander.py', '44', 'Phát lệnh góc tới ba khớp chủ động'),
      ('interactive_control_node.py', '65', 'Node nhập trực tiếp góc khớp'),
      ('test/ (11 tệp)', '≈ 1 100', 'Bộ kiểm thử tự động, 143 trường hợp'),
      ('scripts/ (5 tệp)', '≈ 750', 'Thu dữ liệu, đánh giá, thí nghiệm, sinh marker'),
  ],
  widths=[6.0, 2.2, 7.8], size=11)

H2('Phụ lục D. Đối chiếu thuật ngữ')

P('Bảng dưới đây đối chiếu các thuật ngữ tiếng Việt dùng trong khóa luận với thuật ngữ tiếng Anh '
  'tương ứng, để tiện tra cứu tài liệu gốc.', indent=False)

T('D.1',
  ['Thuật ngữ tiếng Việt', 'Tiếng Anh', 'Ghi chú'],
  [
      ('Robot song song', 'parallel robot', 'Đối lập với robot nối tiếp (serial robot)'),
      ('Bàn máy động', 'moving platform', 'Khâu mang đầu công tác'),
      ('Cánh tay trên', 'upper arm', 'Khâu nối với khớp chủ động'),
      ('Thanh chống', 'forearm', 'Khâu hình bình hành nối tới bàn máy'),
      ('Khớp chủ động', 'actuated joint', 'Khớp có động cơ, ở đây là khớp quay'),
      ('Động học ngược', 'inverse kinematics', 'Từ vị trí tìm góc khớp'),
      ('Động học thuận', 'forward kinematics', 'Từ góc khớp tìm vị trí'),
      ('Điểm kỳ dị', 'singularity', 'Cấu hình mất bậc tự do hoặc mất khả năng truyền lực'),
      ('Không gian làm việc', 'workspace', 'Tập điểm robot với tới được'),
      ('Quỹ đạo giật cực tiểu', 'minimum-jerk trajectory', 'Biên dạng bậc năm'),
      ('Mạch động học kín', 'closed kinematic chain', 'Cấu trúc vòng kín'),
      ('Mô hình lỗ kim', 'pinhole camera model', 'Mô hình chiếu phối cảnh'),
      ('Nội tham số', 'intrinsic parameters', 'Tiêu cự, tâm ảnh, hệ số méo'),
      ('Ngoại tham số', 'extrinsic parameters', 'Vị trí và hướng của camera'),
      ('Sai lệch chiếu ngược', 'reprojection error', 'Thước đo chất lượng hiệu chuẩn'),
      ('Phân đoạn màu', 'colour segmentation', 'Tách vùng ảnh theo ngưỡng màu'),
      ('Phép toán hình thái học', 'morphological operations', 'Phép mở và phép đóng'),
      ('Vùng liên thông', 'connected component', 'Mảng điểm ảnh liền nhau'),
      ('Tâm khối', 'centroid', 'Trung bình tọa độ các điểm ảnh của vùng'),
      ('Khung bao', 'bounding box', 'Hình chữ nhật bao quanh vùng ảnh'),
      ('Hình bóng dự đoán', 'predicted silhouette', 'Bao lồi ảnh các điểm bề mặt vật'),
      ('Che khuất một phần', 'partial occlusion', 'Nguyên nhân sai số chính của hệ thống'),
      ('Tỉ lệ nhìn thấy', 'visible fraction', 'Diện tích thấy được chia cho hình bóng dự đoán'),
      ('Bản sao số', 'digital twin', 'Mô hình ảo phản ánh hệ thống thật'),
      ('Hệ số thời gian thực', 'real time factor', 'Tốc độ mô phỏng so với thời gian thực'),
  ],
  widths=[5.2, 4.8, 6.0], size=11)

# ============================================================================ TÀI LIỆU
H1('TÀI LIỆU THAM KHẢO')

P('**Tiếng Việt**', indent=False)
REFS_VI = [
    'Nguyễn Thiện Phúc, *Robot công nghiệp*, Nhà xuất bản Khoa học và Kỹ thuật, Hà Nội, 2006, '
    'tr. 25–60.',
    'Nguyễn Văn Khang, *Động lực học hệ nhiều vật*, Nhà xuất bản Khoa học và Kỹ thuật, Hà Nội, '
    '2007, tr. 110–145.',
]
REFS_EN = [
    'R. Clavel, *Device for the Movement and Positioning of an Element in Space*, US Patent '
    '4,976,582, 1990.',
    'R. L. Williams II, *The Delta Parallel Robot: Kinematics Solutions*, Ohio University, 2016, '
    'pp. 1–33.',
    'J.-P. Merlet, *Parallel Robots*, 2nd edition, Springer, Dordrecht, 2006, pp. 11–60.',
    'R. Hartley and A. Zisserman, *Multiple View Geometry in Computer Vision*, 2nd edition, '
    'Cambridge University Press, 2004, pp. 153–193.',
    'S. Garrido-Jurado, R. Muñoz-Salinas, F. J. Madrid-Cuevas and M. J. Marín-Jiménez, '
    '“Automatic generation and detection of highly reliable fiducial markers under occlusion”, '
    '*Pattern Recognition*, Vol. 47, 2014, pp. 2280–2292.',
    'G. Terzakis and M. Lourakis, “A consistently fast and globally optimal solution to the '
    'perspective-n-point problem”, *Proceedings of the European Conference on Computer Vision '
    '(ECCV)*, 2020, pp. 478–494.',
    'T. Collins and A. Bartoli, “Infinitesimal plane-based pose estimation”, *International '
    'Journal of Computer Vision*, Vol. 109, 2014, pp. 252–286.',
    'Z. Zhang, “A flexible new technique for camera calibration”, *IEEE Transactions on Pattern '
    'Analysis and Machine Intelligence*, Vol. 22, 2000, pp. 1330–1334.',
    'G. Bradski, “The OpenCV Library”, *Dr. Dobb\'s Journal of Software Tools*, Vol. 25, 2000, '
    'pp. 120–125.',
    'S. Macenski, T. Foote, B. Gerkey, C. Lalancette and W. Woodall, “Robot Operating System 2: '
    'Design, architecture, and uses in the wild”, *Science Robotics*, Vol. 7, 2022, pp. 1–10.',
    'N. Koenig and A. Howard, “Design and use paradigms for Gazebo, an open-source multi-robot '
    'simulator”, *Proceedings of the IEEE/RSJ International Conference on Intelligent Robots and '
    'Systems (IROS)*, 2004, pp. 2149–2154.',
    'T. Flash and N. Hogan, “The coordination of arm movements: an experimentally confirmed '
    'mathematical model”, *The Journal of Neuroscience*, Vol. 5, 1985, pp. 1688–1703.',
    'R. C. Gonzalez and R. E. Woods, *Digital Image Processing*, 4th edition, Pearson, 2018, '
    'pp. 399–450.',
    'B. Siciliano and O. Khatib (editors), *Springer Handbook of Robotics*, 2nd edition, '
    'Springer, 2016, pp. 229–260.',
]


def ref_list(items, start):
    for i, text in enumerate(items, start):
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(-1.0)
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.space_after = Pt(6)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_runs(p, f'[{i}] {text}')
    return start + len(items)


nxt = ref_list(REFS_VI, 1)
doc.add_paragraph()
P('**Tiếng Anh**', indent=False)
ref_list(REFS_EN, nxt)

# ============================================================================ GHI
missing_fig = {k for k, *_ in FIGURES} - FIG_USED
missing_tab = {k for k, _ in TABLES} - TAB_USED
assert not missing_fig, f'Hình khai báo nhưng chưa dùng: {sorted(missing_fig)}'
assert not missing_tab, f'Bảng khai báo nhưng chưa dùng: {sorted(missing_tab)}'
doc.save(OUT)
print(f'Đã ghi {OUT}')
print(f'  {len(FIGURES)} hình, {len(TABLES)} bảng, '
      f'{len(REFS_VI) + len(REFS_EN)} tài liệu tham khảo')
