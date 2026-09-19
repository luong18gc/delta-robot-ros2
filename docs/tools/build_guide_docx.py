#!/usr/bin/env python3
"""
Sinh docs/Huong_dan_do_an_robot_delta.docx — tài liệu giải thích toàn bộ đồ án (Bước 1–9).

Cần python-docx. Máy không có pip; cách đã dùng: tải wheel python_docx từ PyPI, giải nén vào một
thư mục X rồi chạy:  PYTHONPATH=X python3 docs/tools/build_guide_docx.py
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
OUT = os.path.join(WS, 'docs', 'Huong_dan_do_an_robot_delta.docx')
FONT = 'Times New Roman'
MONO = 'Consolas'
ACCENT = RGBColor(0x1F, 0x3A, 0x68)

doc = Document()


# ----------------------------------------------------------------------------- định dạng chung
def setup():
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin, sec.right_margin = Cm(3), Cm(2)
    sec.top_margin, sec.bottom_margin = Cm(2), Cm(2)
    st = doc.styles['Normal']
    st.font.name = FONT
    st.font.size = Pt(13)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    pf = st.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing = 1.25
    for level, size in ((1, 16), (2, 14), (3, 13)):
        h = doc.styles[f'Heading {level}']
        h.font.name = FONT
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.color.rgb = ACCENT
        h.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
        h.paragraph_format.space_before = Pt(14 if level == 1 else 10)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
    for name in ('List Bullet', 'List Number', 'List Bullet 2'):
        s = doc.styles[name]
        s.font.name = FONT
        s.font.size = Pt(13)
    # số trang ở chân trang
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field(p, 'PAGE')
    # Word tự cập nhật mục lục khi mở file. <w:updateFields> phải đứng trước các phần tử dưới đây.
    settings = doc.settings.element
    upd = OxmlElement('w:updateFields')
    upd.set(qn('w:val'), 'true')
    later = {'hdrShapeDefaults', 'footnotePr', 'endnotePr', 'compat', 'docVars', 'rsids',
             'mathPr', 'attachedSchema', 'themeFontLang', 'clrSchemeMapping',
             'doNotIncludeSubdocsInStats', 'doNotAutoCompressPictures', 'forceUpgrade',
             'captions', 'readModeInkLockDown', 'smartTagType', 'schemaLibrary',
             'shapeDefaults', 'doNotEmbedSmartTags', 'decimalSymbol', 'listSeparator'}
    for child in settings:
        if child.tag.split('}')[1] in later:
            child.addprevious(upd)
            break
    else:
        settings.append(upd)
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


INLINE = re.compile(r'(\*\*.+?\*\*|`.+?`)')


def add_runs(p, text, size=None, color=None):
    """Hỗ trợ **đậm** và `mã` trong câu."""
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            r = p.add_run(part[2:-2])
            r.bold = True
        elif part.startswith('`') and part.endswith('`'):
            r = p.add_run(part[1:-1])
            r.font.name = MONO
            r.element.rPr.rFonts.set(qn('w:eastAsia'), MONO)
            r.font.size = Pt((size or 13) - 1.5)
            r.font.color.rgb = RGBColor(0x8B, 0x1E, 0x3F)
            continue
        else:
            r = p.add_run(part)
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = color


def H1(t):
    doc.add_heading(t, 1)


def H2(t):
    doc.add_heading(t, 2)


def H3(t):
    doc.add_heading(t, 3)


def P(t, align=None):
    p = doc.add_paragraph()
    add_runs(p, t)
    if align == 'j' or align is None:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def B(items, style='List Bullet'):
    for it in items:
        p = doc.add_paragraph(style=style)
        add_runs(p, it)


def N(items):
    B(items, 'List Number')


# Thứ tự phần tử theo lược đồ OOXML: <w:shd> phải đứng TRƯỚC các phần tử này.
_AFTER_SHD_PPR = {'tabs', 'suppressAutoHyphens', 'kinsoku', 'wordWrap', 'overflowPunct',
                  'topLinePunct', 'autoSpaceDE', 'autoSpaceDN', 'bidi', 'adjustRightInd',
                  'snapToGrid', 'spacing', 'ind', 'contextualSpacing', 'mirrorIndents',
                  'suppressOverlap', 'jc', 'textDirection', 'textAlignment', 'textboxTightWrap',
                  'outlineLvl', 'divId', 'cnfStyle', 'rPr', 'sectPr', 'pPrChange'}
_AFTER_SHD_TCPR = {'noWrap', 'tcMar', 'textDirection', 'tcFitText', 'vAlign', 'hideMark'}


def shade(cell_or_par, hex_color, is_cell=True):
    el = cell_or_par._tc.get_or_add_tcPr() if is_cell else cell_or_par._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    after = _AFTER_SHD_TCPR if is_cell else _AFTER_SHD_PPR
    for child in el:
        if child.tag.split('}')[1] in after:
            child.addprevious(shd)
            return
    el.append(shd)


def T(header, rows, widths=None, size=11):
    table = doc.add_table(rows=1, cols=len(header))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = table.rows[0].cells[i]
        c.text = ''
        add_runs(c.paragraphs[0], f'**{h}**', size=size)
        shade(c, 'DCE6F2')
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
            for p in c.paragraphs:
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.1
    doc.add_paragraph()


def IMG(name, caption, width=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(FIG, name) if not os.path.isabs(name) else name,
                            width=Cm(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_runs(c, caption, size=11)
    for r in c.runs:
        r.italic = True


def CODE(lines):
    for ln in lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.left_indent = Cm(0.5)
        r = p.add_run(ln if ln else ' ')
        r.font.name = MONO
        r.element.rPr.rFonts.set(qn('w:eastAsia'), MONO)
        r.font.size = Pt(10)
        shade(p, 'F2F2F2', is_cell=False)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def EQ(t):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(t)
    r.font.name = 'Cambria Math'
    r.font.size = Pt(13)
    r.italic = True


def NOTE(title, text, color='FFF4D6'):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.3)
    shade(p, color, is_cell=False)
    add_runs(p, f'**{title}** ' + text, size=12)


def BREAK():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ============================================================================= NỘI DUNG
setup()

# ---------------------------------------------------------------- trang bìa
for _ in range(4):
    doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(p, 'TÀI LIỆU HƯỚNG DẪN TỔNG HỢP', size=14, color=ACCENT)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('ỨNG DỤNG THỊ GIÁC MÁY TÍNH\nTRONG ĐIỀU KHIỂN ROBOT DELTA'.replace('\n', ' '))
r.bold = True
r.font.size = Pt(22)
r.font.color.rgb = ACCENT
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(p, 'Đồ án tốt nghiệp kỹ sư (hệ 4,5 năm) — mô phỏng trên ROS 2 Jazzy và Gazebo Harmonic',
         size=13)
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(p, 'Giải thích những gì đã làm từ Bước 1 đến Bước 9: vì sao làm, làm như thế nào, '
         'kết quả đo được, các vấn đề đã gặp — để hiểu bản chất và báo cáo với giảng viên '
         'hướng dẫn.', size=12)
for _ in range(6):
    doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_runs(p, 'Cập nhật: 19/09/2026 — mã nguồn: github.com/luong18gc/delta-robot-ros2 (private)',
         size=11)
BREAK()

# ---------------------------------------------------------------- mục lục
p = doc.add_paragraph()
r = p.add_run('MỤC LỤC')
r.bold = True
r.font.size = Pt(16)
r.font.color.rgb = ACCENT
p = doc.add_paragraph()
field(p, 'TOC \\o "1-2" \\h \\z \\u')
NOTE('Lưu ý:', 'nếu mục lục trống, trong Word bấm chuột phải vào vùng mục lục → "Update Field" '
     '(Cập nhật trường) → "Update entire table".', 'E8F0FB')
BREAK()

# ---------------------------------------------------------------- 0
H1('Cách đọc tài liệu này')
P('Trong thời gian qua, phần lớn mã nguồn được viết theo yêu cầu của bạn. Tài liệu này giúp bạn '
  '**hiểu bản chất** từng phần để tự trình bày trước giảng viên và hội đồng. Mỗi chương đi theo '
  'cùng một mạch: **vấn đề cần giải quyết → ý tưởng → cách làm cụ thể → kết quả kiểm chứng**.')
B([
    '**Chương 1–2**: bức tranh tổng thể và kiến thức nền (ROS 2, Gazebo). Đọc trước tiên.',
    '**Chương 3–6**: phần robot — mô hình, động học, điều khiển chuyển động, gắp–thả.',
    '**Chương 7**: thị giác máy tính — **trọng tâm của tên đề tài**, nên đọc kỹ nhất.',
    '**Chương 8–9**: số liệu đo và các vấn đề đã gặp. Chương 9 là "kinh nghiệm thực tế" — phần '
    'giảng viên thường đánh giá cao.',
    '**Chương 10–11**: cách chạy demo và việc tiếp theo.',
    '**Phụ lục A**: các câu hỏi giảng viên có thể hỏi kèm gợi ý trả lời.',
])
NOTE('Nguyên tắc xuyên suốt của đồ án:', '**mọi công thức và mọi đoạn mã đều được kiểm chứng bằng '
     'dữ liệu đã biết trước khi tin dùng** (vị trí home, số liệu đo trong mô phỏng, test tự động). '
     'Nhiều lỗi quan trọng được phát hiện chính nhờ nguyên tắc này (xem Chương 9).')

# ---------------------------------------------------------------- 1
H1('1. Tổng quan đề tài')
H2('1.1. Đề tài và mục tiêu')
P('Tên đề tài: **"Ứng dụng thị giác máy tính trong điều khiển Robot delta"**. Mục tiêu cuối cùng là '
  'dùng **camera** để nhận biết vị trí các vật trên bàn, rồi điều khiển **robot delta** tự gắp và '
  'thả vật — giống robot phân loại sản phẩm trên dây chuyền công nghiệp. Toàn bộ robot được '
  '**mô phỏng** trên ROS 2 và Gazebo; về sau sẽ lấy tín hiệu từ **camera thật** để điều khiển robot '
  'trong mô phỏng (bản sao số — digital twin).')
P('Vì sao làm trên mô phỏng trước? Trong mô phỏng ta biết **chính xác** vị trí thật của mọi vật '
  '(gọi là *ground truth*). Nhờ đó đo được sai số của hệ thị giác **bằng milimét** — điều rất khó '
  'làm với camera thật. Khi thuật toán đã được kiểm chứng kỹ, mới chuyển sang camera thật.')

H2('1.2. Kết quả đạt được đến nay')
B([
    '**Động học** thuận/ngược dạng giải tích (closed-form) cho robot delta quay; kiểm chứng trên '
    'Gazebo: platform tới đúng vị trí lệnh với sai số **< 1 mm**.',
    '**Điều khiển chuyển động** theo tọa độ (x, y, z) với quỹ đạo thẳng êm (min-jerk) và đường đi '
    'an toàn tránh va vật.',
    '**Môi trường tương tác**: bàn, 3 vật (hộp, trụ, cầu), khay 3 ô, giác hút ảo; lệnh cấp cao '
    'như "nhặt hộp đỏ", "dọn hết vào khay", "lấy ra về chỗ cũ".',
    '**Thị giác máy tính**: camera mô phỏng, nhận dạng vật theo màu, hiệu chuẩn camera bằng marker '
    'ArUco, đổi pixel → tọa độ robot. Sai số trong vùng robot gắp được: **trung bình 1,13 mm**.',
    '**Xử lý che khuất**: dự đoán hình bóng vật để phát hiện vật bị che và ước lượng lại vật trong '
    'khay (sai số 13,4 → 1,0 mm).',
    '**Gắp–thả hoàn toàn dựa trên camera**: 10 bố trí ngẫu nhiên → **30/30** vật vào khay, **30/30** '
    'vật về chỗ cũ — ngang bằng khi dùng vị trí thật của mô phỏng.',
    '**143 bài kiểm thử tự động** (test) đều đạt.',
])

H2('1.3. Kiến trúc hệ thống')
IMG('system_architecture.png', 'Hình 1.1 — Luồng dữ liệu: từ ảnh camera đến chuyển động của robot')
P('Hệ thống chia thành ba khối, giống cách một con người làm việc:')
B([
    '**Nhận thức (mắt)** — màu xanh: camera chụp ảnh → nhận dạng vật theo màu → đổi vị trí trên ảnh '
    '(pixel) thành vị trí trong không gian (mm) → đánh giá mức tin cậy (vật có bị che không).',
    '**Ra quyết định và chuyển động (não)** — màu vàng: lập kế hoạch nhiệm vụ (nhặt vật nào, thả ô '
    'nào) → sinh quỹ đạo → động học ngược đổi tọa độ thành góc khớp → kiểm chứng kết quả.',
    '**Robot (tay)** — màu xanh lá: bộ điều khiển PID của từng khớp, robot delta mạch kín, giác hút.',
])
P('Vòng phản hồi: góc khớp đo được (như encoder) → **động học thuận** → biết platform đang ở đâu, '
  'dùng làm điểm xuất phát cho quỹ đạo tiếp theo. Sau mỗi thao tác, hệ thống **tự kiểm tra** kết '
  'quả (vật đã được nhấc lên chưa, đã nằm đúng ô chưa) thay vì tin là đã thành công.')

H2('1.4. Các bước đã thực hiện')
T(['Bước', 'Nội dung', 'Kết quả chính'], [
    ['1–2', 'Xác định thông số hình học, xây dựng công thức động học ngược', 'Kiểm chứng bằng tay tại vị trí home'],
    ['3', 'Lập trình động học (Python), test tự động', '28/28 test đạt'],
    ['4', 'Điều khiển theo tọa độ x, y, z', 'Sai số < 1 mm trên 9 điểm'],
    ['5', 'Môi trường: bàn, 3 vật', 'Robot tới được trên cả 3 vật'],
    ['6', 'Va chạm, quỹ đạo, gắp–thả bằng giác hút ảo', 'Gắp cả 3 vật vào khay'],
    ['7', 'Lệnh cấp cao, lấy ra, reset', 'Gắp đúng cả khi vật bị đẩy lệch'],
    ['8.1', 'Camera mô phỏng nhìn xiên', 'Thấy trọn vùng làm việc'],
    ['8.2', 'Nhận dạng vật theo màu (HSV)', '99,5% khung ảnh thấy đủ 3 vật'],
    ['8.3', 'Hiệu chuẩn camera (ArUco + PnP)', 'Vị trí camera lệch 0,35 mm'],
    ['8.4', 'Đo sai số hệ thống (172 ảnh)', 'TB 1,13 mm trong vùng gắp được'],
    ['8.5', 'Xử lý che khuất', 'Vật trong khay 13,4 → 1,0 mm'],
    ['9', 'Gắp–thả hoàn toàn dựa trên camera', '30/30 vào khay, 30/30 về chỗ'],
], widths=[1.6, 8.0, 6.4])

# ---------------------------------------------------------------- 2
H1('2. Kiến thức nền: ROS 2 và Gazebo')
H2('2.1. ROS 2 là gì?')
P('ROS 2 (Robot Operating System 2) **không phải hệ điều hành**, mà là bộ thư viện và công cụ giúp '
  'các chương trình của robot "nói chuyện" với nhau. Một hệ thống robot được chia thành nhiều '
  'chương trình nhỏ, mỗi chương trình làm một việc. Các khái niệm cần nắm:')
T(['Khái niệm', 'Giải thích', 'Ví dụ trong đồ án'], [
    ['**Node**', 'Một chương trình chạy độc lập, làm một việc', '`vision` (nhận dạng), `gripper` (giác hút), `cartesian_control` (điều khiển)'],
    ['**Topic**', 'Kênh phát tin một chiều, liên tục: một bên phát, nhiều bên nghe', '`/side_camera/image` (ảnh), `/joint_states` (góc khớp)'],
    ['**Message**', 'Kiểu dữ liệu của tin trên topic', '`sensor_msgs/Image`, `vision_msgs/Detection3DArray`'],
    ['**Service**', 'Hỏi–đáp: gửi yêu cầu, chờ trả lời', '`/gripper/grip` (hút vật), trả về thành công/thất bại'],
    ['**Launch file**', 'Kịch bản khởi động nhiều node cùng lúc', '`pick_place.launch.py`'],
    ['**Package**', 'Một thư mục mã nguồn đóng gói', '`delta_controller` (package tự viết)'],
    ['**colcon build**', 'Lệnh biên dịch/cài đặt các package', '`colcon build --packages-select delta_controller`'],
], widths=[3.0, 6.0, 7.0])
H2('2.2. Gazebo Harmonic')
P('Gazebo là **phần mềm mô phỏng vật lý**: tính trọng lực, va chạm, lực, và hiển thị hình ảnh 3D '
  '(kể cả ảnh camera mô phỏng). Robot được mô tả bằng file **URDF/xacro** (các khâu, khớp, kích '
  'thước, khối lượng); môi trường (bàn, vật, đèn, camera) mô tả bằng file **SDF** gọi là *world*. '
  'Các tính năng thêm vào mô phỏng gọi là **plugin** (ví dụ plugin điều khiển khớp, plugin camera, '
  'plugin gắn/tháo khớp). Một **cầu nối** (`ros_gz_bridge`) chuyển dữ liệu qua lại giữa Gazebo và '
  'ROS 2.')
H2('2.3. Các node khi chạy hệ thống')
IMG('ros_graph.png', 'Hình 2.1 — Các node ROS 2 và kênh dữ liệu giữa chúng')
P('Khi chạy `ros2 launch delta_controller pick_place.launch.py`, Gazebo khởi động cùng robot, bàn, '
  'vật, camera; các cầu nối chuyển ảnh, góc khớp, trạng thái giác hút sang ROS; node `vision` nhận '
  'ảnh và phát vị trí vật; node `gripper` quản lý giác hút. Người dùng chạy thêm '
  '`cartesian_control` để gõ lệnh. Node này nhận vị trí vật từ `vision`, góc khớp từ '
  '`/joint_states`, gửi lệnh góc khớp tới Gazebo và gọi dịch vụ hút/nhả.')
H2('2.4. Package tự viết `delta_controller`')
T(['File', 'Vai trò'], [
    ['`delta_kinematics.py`', 'Động học ngược và thuận (thuần Python)'],
    ['`trajectory.py`', 'Sinh quỹ đạo thẳng min-jerk, đường an toàn'],
    ['`joint_commander.py`', 'Gửi lệnh 3 góc khớp tới Gazebo'],
    ['`cartesian_control_node.py`', 'Node điều khiển: gõ lệnh, chạy quỹ đạo, chọn nguồn vị trí vật'],
    ['`scene.py`', 'Mô tả cảnh: vật, bàn, khay, ô thả, marker, tư thế quan sát'],
    ['`task_planner.py`', 'Lập kế hoạch lệnh cấp cao thành chuỗi thao tác'],
    ['`task_executor.py`', 'Thực thi kế hoạch và kiểm chứng kết quả'],
    ['`gripper_logic.py`, `gripper_node.py`', 'Giác hút ảo: điều kiện hút, dịch vụ hút/nhả'],
    ['`color_detector.py`', 'Nhận dạng vật theo màu (OpenCV)'],
    ['`camera_model.py`', 'Mô hình camera, hiệu chuẩn PnP, đổi pixel → tọa độ'],
    ['`vision_estimation.py`', 'Ước lượng vị trí có xét che khuất'],
    ['`vision_node.py`', 'Node thị giác: ảnh → vị trí vật'],
    ['`calibrate_camera_node.py`', 'Công cụ hiệu chuẩn camera bằng marker'],
    ['`vision_eval.py`', 'Đánh giá sai số thị giác trên bộ dữ liệu'],
    ['`test/`', '143 bài kiểm thử tự động'],
], widths=[6.0, 10.0])
NOTE('Thiết kế quan trọng:', 'các phần tính toán (động học, quỹ đạo, nhận dạng, mô hình camera, lập '
     'kế hoạch) viết bằng **Python thuần, không phụ thuộc ROS**. Nhờ vậy kiểm thử được tự động mà '
     'không cần mở Gazebo, và dùng lại được cho camera thật.')

# ---------------------------------------------------------------- 3
H1('3. Mô hình robot delta trong mô phỏng')
H2('3.1. Robot delta dạng quay (kiểu Clavel)')
P('Robot delta do Reymond Clavel phát minh (bằng sáng chế Mỹ 4.976.582, 1990). Cấu tạo: **đế cố '
  'định** mang 3 động cơ đặt cách đều 120°; **3 cánh tay trên** quay quanh trục nằm ngang (đây là 3 '
  'khớp chủ động duy nhất θ₁, θ₂, θ₃); **3 thanh chống** nối với cánh tay và bàn máy bằng khớp cầu; '
  '**bàn máy động (platform)** mang đầu công tác. Nhờ cấu trúc hình bình hành, platform **luôn song '
  'song với đế** — chỉ tịnh tiến theo x, y, z, không xoay. Ưu điểm: nhẹ, nhanh, chính xác, rất phổ '
  'biến trong dây chuyền đóng gói, phân loại.')
H2('3.2. Mạch động học kín trong Gazebo')
P('File URDF chỉ mô tả được **cây** (mỗi khâu chỉ có một khâu cha), nhưng robot delta là **mạch kín** '
  '(ba chân cùng nối vào platform). Repo gốc giải quyết bằng plugin Gazebo **DetachableJoint**: hàn '
  'hai khâu lại với nhau **lúc chạy**. Các khâu cần hàn được thiết kế trùng nhau tại vị trí home nên '
  'mối hàn không gây giật. Platform treo trên chuỗi **3 khớp trượt bị động X–Y–Z**, nên luôn nằm '
  'ngang và có đúng 3 bậc tự do tịnh tiến.')
P('`/joint_states` chỉ chứa **góc 3 khớp chủ động** — giống robot thật, nơi encoder chỉ gắn ở động '
  'cơ. Vì vậy muốn biết platform ở đâu phải dùng **động học thuận** (Chương 4).')
H2('3.3. Thông số hình học')
T(['Ký hiệu', 'Ý nghĩa', 'Giá trị'], [
    ['f', 'Bán kính đế (tâm đế → khớp chủ động)', '41,7 mm'],
    ['e', 'Bán kính platform (tâm platform → khớp cầu)', '27,6 mm'],
    ['r_f', 'Chiều dài cánh tay trên', '75,8 mm'],
    ['r_e', 'Chiều dài thanh chống', '166,8 mm'],
    ['θ', 'Giới hạn góc khớp', '−59,0° … +82,0°'],
    ['Home', 'θ₁ = θ₂ = θ₃ = 0 ⟺ platform tại', '(0; 0; −140,5) mm'],
], widths=[2.2, 9.3, 4.5])
H2('3.4. Hệ tọa độ')
B([
    'Gốc O tại **tâm đế** robot. Trục **X** hướng ra chân 1; trục **Z hướng lên** → platform luôn ở '
    'dưới nên z luôn **âm**; trục Y theo quy tắc bàn tay phải. Ba chân đặt ở góc 0°, 120°, 240°.',
    'θ = 0 khi cánh tay trên nằm ngang hướng ra ngoài; θ tăng khi cánh tay hạ xuống.',
    'Trong Gazebo, đế robot đặt ở độ cao 1,0 m, nên tọa độ robot = tọa độ Gazebo trừ (0; 0; 1,0).',
])

# ---------------------------------------------------------------- 4
H1('4. Động học robot')
P('Chi tiết đầy đủ kèm công thức hiển thị đẹp có trong `docs/bao_cao_kinematics.md` và trang web '
  'báo cáo động học. Chương này tóm tắt bản chất.')
IMG('delta_leg_diagram.png', 'Hình 4.1 — Một chân robot: khớp chủ động, khuỷu E, khớp cầu B, '
    'platform P', width=11)
H2('4.1. Ràng buộc cơ bản')
P('Mọi phương trình động học đều xuất phát từ một điều: **thanh chống có chiều dài không đổi**. Với '
  'mỗi chân i, khoảng cách từ khuỷu tay E_i tới khớp cầu B_i trên platform luôn bằng r_e:')
EQ('‖B_i − E_i‖ = r_e      (i = 1, 2, 3)')
B([
    '**Động học ngược (IK)**: biết vị trí platform P = (x, y, z) → tìm 3 góc θ. Dùng để **điều '
    'khiển**: muốn platform tới đâu thì tính góc khớp tương ứng.',
    '**Động học thuận (FK)**: biết 3 góc θ → tìm P. Dùng để **biết robot đang ở đâu** từ encoder.',
])
H2('4.2. Động học ngược')
P('Xoay điểm P về hệ tọa độ riêng của từng chân (quay quanh Z một góc −φ_i) để công thức 3 chân '
  'giống hệt nhau. Khai triển ràng buộc thu được một phương trình lượng giác:')
EQ('A·cos θ + B·sin θ + C = 0,   với  A = −2·r_f·a,  B = 2·r_f·z,  C = a² + y² + z² + r_f² − r_e²')
P('trong đó a = (x_i + e) − f. Đặt t = tan(θ/2) (phép thế Weierstrass) được phương trình bậc hai:')
EQ('(C − A)·t² + 2B·t + (A + C) = 0   →   t = [−B ± √(A² + B² − C²)] / (C − A),   θ = 2·arctan t')
B([
    'Biệt thức Δ = A² + B² − C² < 0 → **điểm ngoài tầm với**; Δ = 0 → cánh tay và thanh chống duỗi '
    'thẳng hàng: **biên không gian làm việc, điểm kỳ dị**.',
    '**Chọn nghiệm**: mỗi chân có 2 nghiệm (2 cách lắp). Robot thật lắp kiểu **"khuỷu ra ngoài"**, '
    'tương ứng điều kiện −A·sin θ + B·cos θ ≤ 0 (dấu đạo hàm). Quy tắc đơn giản hơn "lấy nghiệm nằm '
    'trong giới hạn khớp" **không đủ**: khi quét lưới đã tìm thấy điểm mà cả 2 nghiệm đều trong giới '
    'hạn.',
])
H2('4.3. Động học thuận')
P('Viết lại ràng buộc: ‖P − C_i‖ = r_e với C_i = E_i − e·u_i là một **điểm đã biết** khi biết θ_i. '
  'Vậy P là **giao điểm của 3 mặt cầu** cùng bán kính r_e (phép định vị ba điểm — trilateration). '
  'Hai giao điểm đối xứng qua mặt phẳng 3 tâm; chọn điểm **nằm dưới** vì platform treo dưới đế.')
H2('4.4. Kiểm chứng')
T(['Phép kiểm tra', 'Kết quả'], [
    ['Thay vị trí home vào IK (tính tay)', 'A + C = 0 → t = 0 → θ = 0 ✓ khớp URDF'],
    ['Chiều dài thanh chống sau khi giải IK', 'Sai số < 10⁻⁹ m'],
    ['Vòng IK → FK trên 5.424 điểm', 'Sai số lớn nhất 5×10⁻¹³ m (sai số làm tròn máy tính)'],
    ['Ra lệnh 9 điểm trên Gazebo, đo vị trí thật', 'Sai số < 1 mm (tới ~1,5 mm khi tay duỗi xa)'],
], widths=[8.0, 8.0])
NOTE('Bài học:', 'phiên bản đầu viết nhầm dấu a = (x − e) − f; thử ngay với vị trí home ra z = −82,3 mm '
     'thay vì −140,5 mm nên phát hiện lỗi tức thì. Vòng IK → FK mạnh vì hai công thức xây dựng '
     '**độc lập** (Weierstrass và giao 3 mặt cầu) mà khử lẫn nhau tới 10⁻¹³ m.')
H2('4.5. Không gian làm việc')
T(['Độ cao z (mm)', '−110', '−140', '−160', '−180', '−200', '−220', '−240'],
  [['Bán kính với tới mọi hướng (mm)', '138', '128', '118', '105', '85', '57', '0']], size=10)

# ---------------------------------------------------------------- 5
H1('5. Điều khiển chuyển động')
H2('5.1. Từ tọa độ tới góc khớp')
P('Node `cartesian_control` nhận lệnh tọa độ (ví dụ `0.06 0 -0.185`), giải IK ra 3 góc khớp rồi gửi '
  'tới bộ điều khiển PID của Gazebo qua 3 topic `cmd_pos`. Điểm xuất phát của mỗi chuyển động lấy '
  'từ **FK của góc khớp đo được** (không phải lệnh cuối cùng), nên vẫn đúng cả khi robot bị vật cản '
  'chặn lại.')
H2('5.2. Quỹ đạo thẳng min-jerk')
P('Nếu gửi thẳng góc khớp đích, mỗi khớp tự chạy theo PID riêng → platform đi đường cong khó đoán. '
  'Thay vào đó, đoạn thẳng từ điểm đầu tới điểm cuối được chia nhỏ (50 điểm/giây), mỗi điểm giải IK. '
  'Vị trí theo thời gian dùng **đa thức bậc 5 (minimum-jerk)**:')
EQ('s(τ) = 10τ³ − 15τ⁴ + 6τ⁵,   τ = t / T ∈ [0, 1],   v_max = 1,875·L / T')
P('Vận tốc và gia tốc bằng 0 ở hai đầu → robot khởi động và dừng êm. Toàn bộ quỹ đạo được giải IK '
  '**trước khi chạy**: nếu một điểm giữa đường ngoài tầm với thì báo lỗi, robot chưa di chuyển.')
H2('5.3. Đường an toàn nâng – ngang – hạ')
P('Để không quét trúng vật trên bàn: nâng lên độ cao an toàn (z = −160 mm, hoặc −140 mm khi đang mang '
  'vật) → đi ngang → hạ xuống. Đo trên Gazebo: platform bám đường này lệch ≤ 4,4 mm, vật không bị '
  'chạm.')

# ---------------------------------------------------------------- 6
H1('6. Môi trường tương tác và gắp – thả')
H2('6.1. Bàn, vật và khay')
T(['Vật', 'Hình dạng', 'Vị trí ban đầu (mm)'], [
    ['red_box (hộp đỏ)', 'Hộp 3 cm', '(60; 0), đỉnh z = −190'],
    ['green_cylinder (trụ xanh lá)', 'Trụ bán kính 1,5 cm, cao 3 cm', '(−30; 52)'],
    ['blue_sphere (cầu xanh dương)', 'Cầu bán kính 1,5 cm (+ đế chống lăn vô hình)', '(−30; −52)'],
    ['drop_bin (khay)', 'Lòng 7×7 cm, thành cao 2 cm, 3 ô A/B/C', 'tâm (37,5; 65)'],
], widths=[5.0, 6.5, 4.5])
H2('6.2. Va chạm')
P('Chỉ **platform** có hình va chạm (hộp 5×5×0,6 cm); các thanh khác chỉ có hình hiển thị. Đo được: '
  'platform đẩy vật đúng như tính toán, bị mặt bàn chặn đúng chỗ. Hạn chế: ép platform xuống vật '
  'đang nằm trên bàn thì platform **lún dần** vào vật (hạn chế của bộ giải vật lý) → khi gắp chỉ hạ '
  'tới đúng đỉnh vật, không hạ thấp hơn.')
H2('6.3. Giác hút ảo')
P('Giác hút thật dùng chân không. Trong mô phỏng, "hút" = dùng plugin **DetachableJoint** hàn vật vào '
  'platform, "nhả" = tháo mối hàn. Node `gripper` chỉ cho hút khi platform **chạm đỉnh vật** (lệch '
  'ngang ≤ 12 mm, khe hở −4…+6 mm) — giống giác hút thật chỉ hút được khi tiếp xúc.')
B([
    'Cạm bẫy 1: 4 mối hàn mạch kín của robot dùng chung topic mặc định. Nếu giác hút gửi lệnh "nhả" '
    'vào topic đó, **cả robot rã ra**. Giác hút phải dùng topic riêng.',
    'Cạm bẫy 2: plugin **tự hàn ngay khi khởi động** → robot bị 3 vật giữ cứng. Node `gripper` gửi '
    'lệnh nhả tất cả lúc bắt đầu.',
])
H2('6.4. Lệnh cấp cao')
T(['Lệnh (có tên tiếng Việt)', 'Tác dụng'], [
    ['`vat` (objects)', 'Vị trí và trạng thái từng vật'],
    ['`nhat <vật>` (pick)', 'Hạ xuống chạm đỉnh vật → hút → nhấc lên'],
    ['`tha [ô]` (place)', 'Mang vật đang giữ tới ô khay → nhả'],
    ['`chuyen <vật> [ô]`', 'Nhặt rồi thả'],
    ['`don` (sort)', 'Dọn hết vật trên bàn vào khay'],
    ['`lay_ra <vật> [x y]`', 'Lấy vật từ khay ra đặt lên bàn'],
    ['`reset`', 'Lấy hết vật trong khay về chỗ cũ'],
    ['`nguon camera | nguon that`', 'Vị trí vật lấy từ camera hay vị trí thật của mô phỏng'],
], widths=[6.0, 10.0])
P('Mỗi lệnh được chia thành chuỗi thao tác Đi → Hút → Đi → Nhả. Hệ thống kiểm tra trước khi làm '
  '(ô đã có vật chưa, chỗ đặt có chồng khay không, có trong tầm với không) và **kiểm chứng sau khi '
  'làm** (vật đã nằm đúng ô chưa).')

# ---------------------------------------------------------------- 7
H1('7. Thị giác máy tính — trọng tâm đề tài')
P('Bài toán: từ **một ảnh 2D**, tìm vị trí **3D** của vật trong hệ tọa độ robot, đủ chính xác để giác '
  'hút gắp được (sai ≤ 12 mm). Chuỗi xử lý gồm 4 khâu: camera → nhận dạng → hiệu chuẩn và đổi tọa '
  'độ → xử lý che khuất.')
H2('7.1. Camera mô phỏng (Bước 8.1)')
P('Camera đặt **nhìn xiên** từ phía sau bàn (cách tâm bàn 40 cm, cao hơn mặt bàn 25 cm, chúc xuống '
  '32°), vì đặt thẳng từ trên xuống thì **đế robot che mất** vùng làm việc. Ảnh 640×480, 10 ảnh/giây. '
  'Vị trí chính xác của camera được ghi lại **chỉ để đánh giá** kết quả hiệu chuẩn.')
H2('7.2. Nhận dạng vật theo màu (Bước 8.2)')
P('Ảnh màu thường ở dạng BGR (xanh dương – xanh lá – đỏ), trong đó độ sáng trộn lẫn với màu: vật '
  'nằm trong bóng tối có giá trị BGR khác hẳn. Vì vậy chuyển sang không gian **HSV**: H (sắc độ – '
  '"màu gì"), S (độ bão hòa – "màu đậm hay nhạt"), V (độ sáng). Vật trong bóng chỉ giảm V, **giữ '
  'nguyên H**.')
N([
    'Đổi ảnh sang HSV.',
    'Lọc theo ngưỡng từng màu → mặt nạ nhị phân (pixel thuộc màu = trắng).',
    'Lọc nhiễu bằng phép **mở** (xóa hạt lẻ) và **đóng** (lấp lỗ nhỏ).',
    'Tìm vùng liên thông, bỏ vùng nhỏ hơn 30 pixel.',
    '**Gộp mọi mảnh cùng màu** (mỗi màu là đúng một vật — vật bị cánh tay cắt đôi vẫn là một vật), '
    'lấy **tâm khối** và khung bao.',
])
T(['Vùng', 'H', 'S', 'Ghi chú'], [
    ['Hộp đỏ (trong bóng)', '0', '174', 'V chỉ 95 — rất tối nhưng H vẫn đúng'],
    ['Trụ xanh lá', '68', '155', ''],
    ['Cầu xanh dương', '108', '164', ''],
    ['Khay cam', '20', '165', 'Dễ nhầm với đỏ → ngưỡng đỏ chỉ H ≤ 8'],
    ['Platform vàng', '29', '159', ''],
    ['Mặt bàn', '17', '77', 'S thấp → loại bằng ngưỡng S ≥ 90'],
], widths=[5.0, 1.5, 1.5, 8.0])
P('Ngưỡng được chọn **từ số đo thật** trên ảnh camera (không đoán). Màu đỏ nằm ở cả hai đầu vòng màu '
  '(H gần 0 và gần 180) nên dùng hai khoảng. Thời gian xử lý ~12 ms/ảnh.')
IMG('vision_objects_mm.png', 'Hình 7.1 — Ảnh camera có chú thích: tên vật, tọa độ (mm), marker ArUco '
    'trên bàn', width=13)
H2('7.3. Mô hình camera và hiệu chuẩn (Bước 8.3)')
P('**Mô hình lỗ kim (pinhole)**: một điểm 3D X được chiếu lên ảnh theo công thức')
EQ('[u, v, 1]ᵀ ~ K · (R · X + t)')
B([
    '**Nội tham số K** (đặc tính của camera): tiêu cự fx, fy và tâm ảnh cx, cy. Camera mô phỏng: '
    'fx = fy ≈ 772,5 pixel, cx = 320, cy = 240. Camera thật còn có **méo ống kính** và phải hiệu '
    'chuẩn bằng bàn cờ.',
    '**Ngoại tham số R, t** (camera đặt ở đâu, nhìn hướng nào so với robot): tìm bằng **hiệu chuẩn**.',
])
P('**Hiệu chuẩn bằng marker ArUco**: 6 marker ô vuông đen trắng (mỗi marker có một số hiệu riêng) '
  'dán trên bàn ở vị trí **biết trước**. Camera nhận dạng marker → có 6 cặp điểm (vị trí 3D trên '
  'bàn ↔ vị trí 2D trên ảnh) → giải bài toán **PnP (Perspective-n-Point)** tìm R, t.')
B([
    'Tâm marker trên ảnh lấy bằng **giao điểm hai đường chéo**, không lấy trung bình 4 góc: phép chiếu '
    'phối cảnh bảo toàn giao điểm đường chéo nên đó mới đúng là ảnh của tâm thật.',
    'Giải PnP bằng thuật toán **SQPnP** rồi tinh chỉnh Levenberg–Marquardt. Thuật toán IPPE (chuyên '
    'cho điểm đồng phẳng) cho **nghiệm sai hoàn toàn** trên ảnh thật dù đúng trên dữ liệu giả lập.',
    'Kết quả: sai số chiếu lại **0,14 pixel**; vị trí camera tính được lệch vị trí thật **0,35 mm**, '
    'hướng nhìn lệch **0,017°**.',
])
IMG('calibration_markers.png', 'Hình 7.2 — Hiệu chuẩn: marker được nhận dạng (khung xanh) và điểm '
    'chiếu lại từ kết quả PnP', width=13)
H2('7.4. Đổi pixel thành tọa độ robot')
P('Một pixel trên ảnh tương ứng với cả một **tia nhìn** trong không gian, không phải một điểm. Muốn '
  'ra một điểm cần thêm thông tin: vật **nằm trên bàn**, nên tâm vật ở độ cao đã biết (mặt bàn + nửa '
  'chiều cao vật). Giao tia nhìn với mặt phẳng nằm ngang ở độ cao đó → vị trí (x, y, z).')
NOTE('Điểm tinh tế:', 'nếu giao tia với **mặt bàn** thay vì mặt phẳng **độ cao tâm vật**, sai số lên '
     'tới ~12 mm (vì camera nhìn xiên). Kiểm chứng: chiếu tâm 3D thật của vật lên ảnh rơi cách tâm '
     'khối nhận dạng chỉ 0,7–1,2 pixel → với vật cao ≈ rộng, tâm phần nhìn thấy ≈ hình chiếu tâm 3D.')
H2('7.5. Xử lý che khuất (Bước 8.5)')
P('Khi đo hệ thống (Bước 8.4), mọi sai số lớn đều do **vật bị che một phần**: tâm khối là tâm **phần '
  'nhìn thấy**, phần bị che làm tâm dịch đi. Ví dụ vật trong khay bị thành khay che nửa dưới → tính '
  'ra xa hơn thật 12–20 mm, **vượt dung sai giác hút**. Giải pháp dựa trên **dự đoán hình bóng**:')
B([
    '**Hình bóng dự đoán**: lấy nhiều điểm trên bề mặt vật (hộp, trụ, cầu), chiếu lên ảnh bằng mô '
    'hình camera, lấy **bao lồi** (convex hull). Với vật lồi, bao lồi này chính là hình bóng vật trên '
    'ảnh. Kiểm chứng: vật không bị che có tỉ lệ nhìn thấy ≈ 0,99.',
    '**(a) Cờ tin cậy**: tỉ lệ nhìn thấy = diện tích nhìn thấy / diện tích dự đoán. Nhỏ hơn **0,90** '
    'hoặc chạm mép ảnh → vị trí **không tin cậy** (score = 0), robot không dùng.',
    '**(b) Khớp mép trên** cho vật trong khay: mặt trên của vật luôn lộ ra (camera nhìn xuống). Tìm '
    '(x, y) sao cho **mép trên** và **tâm ngang** của hình bóng dự đoán trùng với ảnh: 2 phương trình '
    '2 ẩn, giải bằng phương pháp **Newton**. Sai số vật trong khay: **13,4 → 1,0 mm**.',
])
H2('7.6. Tích hợp vào điều khiển (Bước 9)')
B([
    '**Tư thế quan sát**: trước khi đo, robot nâng platform lên (0; 0; −110 mm) để không che camera '
    '(ở vị trí home, platform che vật phía xa: sai 17 mm; ở tư thế quan sát: 0,3 mm).',
    '**Chỉ tin ảnh mới**: chỉ dùng khung ảnh chụp **sau khi robot đã dừng**; chỉ dùng vật có score > 0.',
    '**Kiểm chứng**: "đã nhấc lên" dựa vào giác hút (camera không đo được vật lơ lửng); "đã thả đúng '
    'ô" dựa vào camera sau khi quan sát lại.',
    '**Tách nhận thức khỏi phần cứng**: bộ lập kế hoạch dùng camera; giác hút mô phỏng vẫn dùng vật lý '
    '(giống giác hút thật không "biết" vị trí vật).',
    '**Vật che vật**: vật bị vật khác che được coi là "chưa rõ"; robot gắp vật phía trước trước, quan '
    'sát lại, lúc đó vật phía sau đã lộ ra.',
])

# ---------------------------------------------------------------- 8
H1('8. Kết quả đánh giá')
H2('8.1. Sai số thị giác (172 ảnh, Bước 8.4 – 8.5)')
P('Bộ dữ liệu thu tự động: dời từng vật qua 61 điểm lưới trên bàn, robot lơ lửng che vật ở nhiều độ '
  'cao, vật đặt trong 3 ô khay; mỗi ảnh kèm vị trí thật. Sai số = khoảng cách ngang giữa vị trí camera '
  'ước lượng và vị trí thật.')
T(['Nhóm', 'Sai số TB', 'Lớn nhất', 'Ghi chú'], [
    ['**Vùng robot gắp được** (58 mẫu)', '**1,13 mm**', '6,2 mm', '100% trong dung sai 12 mm'],
    ['Mọi điểm vật trọn trong ảnh', '2,0 mm', '20,6 mm', 'Sai số lớn đều ngoài tầm với'],
    ['Vật trong khay — trước cải tiến', '13,4 mm', '19,7 mm', 'Thành khay che nửa dưới'],
    ['Vật trong khay — **sau cải tiến**', '**1,0 mm**', '1,9 mm', 'Khớp mép trên'],
    ['Chỉ các ước lượng "tin cậy"', '0,9 mm', '3,4 mm', 'Cờ bắt 100% ước lượng > 5 mm'],
], widths=[6.0, 2.3, 2.3, 5.4])
IMG('vision_error_map.png', 'Hình 8.1 — Bản đồ sai số trên bàn (nhìn từ phía camera); dấu × = vật bị '
    'cắt mép ảnh', width=16)
IMG('vision_robustness.png', 'Hình 8.2 — Độ bền với nhiễu Gauss và thay đổi độ sáng', width=16)
P('Độ bền: không ảnh hưởng tới nhiễu σ = 10 mức xám; ổn định khi độ sáng thay đổi 0,5×–1,6×. Lưu ý: '
  'camera mô phỏng **không có nhiễu thật**, nên nhiễu được thêm nhân tạo khi đánh giá.')
H2('8.2. Gắp – thả dựa trên camera (Bước 9)')
T(['Chế độ', 'Vật vào ô', 'Lượt dọn trọn vẹn', 'Vật về chỗ cũ', 'Thời gian / lượt'], [
    ['**Camera**', '**30/30**', '**10/10**', '**30/30**', '58 + 55 s'],
    ['Vị trí thật (mô phỏng)', '30/30', '10/10', '30/30', '43 + 36 s'],
], widths=[4.0, 2.6, 3.4, 2.8, 3.2])
P('10 bố trí ngẫu nhiên, mỗi lượt `don` rồi `reset`, chấm bằng vị trí thật. Robot dựa hoàn toàn vào '
  'camera đạt **cùng độ tin cậy** với khi biết vị trí thật; chậm hơn ~35% do phải về tư thế quan sát.')
H2('8.3. Hiệu năng mô phỏng')
T(['Cấu hình', 'Tốc độ mô phỏng (so với thời gian thực)'], [
    ['Card Intel, có cửa sổ Gazebo + camera', '~0,35'],
    ['Card Intel, không cửa sổ', '~0,94'],
    ['Card NVIDIA, trước khi sửa lỗi tải CPU', '0,56'],
    ['Card NVIDIA, sau khi sửa', '0,77 (0,76–0,99 ở chế độ hiệu năng cao)'],
], widths=[9.0, 7.0])

# ---------------------------------------------------------------- 9
H1('9. Các vấn đề đã gặp và cách giải quyết')
P('Phần này thể hiện quá trình làm việc thực tế: **phát hiện vấn đề bằng đo đạc → tìm nguyên nhân → '
  'sửa → đo lại**. Một số chẩn đoán ban đầu **sai** và đã được đính chính — đây là điều bình thường '
  'và nên trình bày trung thực.')
T(['Vấn đề', 'Nguyên nhân (đã kiểm chứng)', 'Cách giải quyết'], [
    ['IK cho z = −82,3 mm thay vì −140,5 mm', 'Sai dấu (x − e) thay vì (x + e)', 'Kiểm chứng bằng vị trí home'],
    ['Chọn nghiệm IK "trong giới hạn khớp" không đủ', 'Có điểm mà cả 2 nghiệm đều hợp lệ', 'Tiêu chí hình học "khuỷu ra ngoài"'],
    ['Lệnh đầu tiên bị mất', 'Gửi trước khi cầu nối kết nối xong', 'Chờ kết nối trước khi nhận lệnh'],
    ['Robot bị giữ cứng khi khởi động', 'Plugin giác hút tự hàn vật lúc đầu', 'Nhả tất cả vật khi khởi động'],
    ['Quả cầu lăn khỏi ô, lăn 25–51 mm', 'Bộ giải vật lý không có lực cản lăn', 'Đế chống lăn vô hình'],
    ['Mô phỏng chậm (0,35×) khi có camera', 'Cửa sổ Gazebo + camera tranh card Intel', 'Cài driver NVIDIA, tùy chọn không cửa sổ'],
    ['Node giác hút ăn 100% CPU', '`use_sim_time` → nhận `/clock` 2000 lần/s (lúc đầu đổ nhầm cho /joint_states)', 'Bỏ use_sim_time; giảm /joint_states xuống 100 Hz'],
    ['PnP cho vị trí camera sai hoàn toàn', 'Thuật toán IPPE không ổn định trên dữ liệu thật', 'Dùng SQPnP'],
    ['Nhiễu camera khai báo nhưng không có', 'Thẻ noise không tác dụng trong phiên bản này', 'Thêm nhiễu nhân tạo khi đánh giá'],
    ['Vật trong khay sai 13–20 mm', 'Thành khay che nửa dưới vật', 'Khớp mép trên (Newton)'],
    ['Vật phía xa sai 17–19 mm', 'Platform che vật', 'Tư thế quan sát trước khi đo'],
    ['Hộp bị hút lệch, thả trượt sang ô khác', 'Vật che vật; cờ tin cậy 0,85 bỏ lọt (lúc đầu nghi thanh chống — sai)', 'Ngưỡng 0,90 + gắp vật phía trước trước'],
], widths=[5.0, 5.8, 5.2], size=10)

# ---------------------------------------------------------------- 10
H1('10. Hướng dẫn chạy demo')
P('Mỗi terminal mới chạy trước hai lệnh:')
CODE(['source /opt/ros/jazzy/setup.bash', 'source ~/ros2_closed_loop_ws/install/setup.bash'])
P('Nên cắm sạc và bật chế độ hiệu năng: `powerprofilesctl set performance`.')
H2('10.1. Khởi động')
CODE(['# Terminal 1: mô phỏng + giác hút + nhận dạng',
      'ros2 launch delta_controller pick_place.launch.py',
      '',
      '# Terminal 2: xem camera nhận dạng',
      'ros2 run rqt_image_view rqt_image_view /vision/debug_image',
      '',
      '# Terminal 3: điều khiển',
      'ros2 run delta_controller cartesian_control'])
H2('10.2. Kịch bản demo đề xuất khi báo cáo')
N([
    '`vat` — robot lên tư thế quan sát, báo vị trí 3 vật theo camera (so với Hình 7.1).',
    '`don` — dọn hết vào khay, hoàn toàn dựa trên camera.',
    '`vat` — camera thấy 3 vật trong ô A/B/C.',
    '`reset` — lấy ra, đặt về chỗ cũ (dùng kỹ thuật khớp mép trên).',
    '`nguon that` rồi `don` — so sánh với chế độ vị trí thật.',
    'Tùy chọn: đặt vật lệch bằng lệnh `gz service` (xem hướng dẫn trong repo) để minh họa robot tìm '
    'vật ở vị trí mới và xử lý vật bị che.',
])
H2('10.3. Chạy lại các thí nghiệm')
CODE(['cd ~/ros2_closed_loop_ws',
      'colcon test --packages-select delta_controller && colcon test-result --verbose',
      'python3 src/delta_controller/scripts/evaluate_vision.py        # sai số thị giác',
      'python3 src/delta_controller/scripts/run_pick_place_trials.py 3 2026   # gắp–thả (cần sim)'])

# ---------------------------------------------------------------- 11
H1('11. Việc tiếp theo')
T(['Bước', 'Nội dung', 'Cần chuẩn bị'], [
    ['10', 'Camera thật + bản sao số: vật thật trên bàn thật → vật ảo trong Gazebo đặt đúng vị trí → '
     'robot tự gắp', 'Webcam USB nhìn được xuống bàn; 3 khối màu đỏ/xanh lá/xanh dương; in marker'],
    ['11', 'Chế độ bám theo tay hoặc marker (demo)', '—'],
    ['12', 'Đánh giá tổng hợp (độ chính xác, độ trễ, tỉ lệ thành công) và viết báo cáo', '—'],
], widths=[1.5, 8.5, 6.0])
P('**File marker để in**: `docs/calibration/aruco_markers_A4.pdf` — trang 1 hướng dẫn và sơ đồ bố '
  'trí, trang 2–4 là 6 marker đúng kích thước (ô đen 50 mm). In ở tỉ lệ 100% (tắt "Fit to page") và '
  'kiểm tra thước 100 mm trên mỗi trang. Camera thật cần thêm bước **hiệu chuẩn nội tham số** bằng '
  'bàn cờ (vì có méo ống kính) — sẽ làm ở Bước 10.')

# ---------------------------------------------------------------- phụ lục A
H1('Phụ lục A. Câu hỏi thường gặp khi báo cáo')
QA = [
    ('Vì sao chọn nhận dạng theo màu mà không dùng học sâu (YOLO…)?',
     'Vật có màu phân biệt rõ, nhận dạng màu chạy nhanh (~12 ms/ảnh), không cần dữ liệu huấn luyện, '
     'dễ giải thích và kiểm chứng. Đo được 99,5% khung ảnh thấy đủ vật và sai số ~1 mm — đủ cho giác '
     'hút. Học sâu là hướng mở rộng khi vật đa dạng hơn.'),
    ('Vì sao dùng không gian màu HSV?',
     'Tách "màu gì" (H) khỏi "sáng hay tối" (V). Vật nằm trong bóng robot có V giảm mạnh (95/255) '
     'nhưng H giữ nguyên, nên vẫn nhận dạng đúng.'),
    ('Làm sao từ ảnh 2D ra được vị trí 3D?',
     'Mỗi pixel là một tia nhìn. Biết vật nằm trên bàn nên biết độ cao tâm vật; giao tia với mặt phẳng '
     'ở độ cao đó ra điểm 3D. Cần mô hình camera (K, R, t) đã hiệu chuẩn.'),
    ('Hiệu chuẩn camera để làm gì, làm thế nào?',
     'Để biết camera đặt ở đâu, nhìn hướng nào so với robot (R, t). Dùng 6 marker ArUco ở vị trí biết '
     'trước → 6 cặp điểm 3D–2D → giải PnP. Kết quả lệch vị trí thật 0,35 mm.'),
    ('Sai số hệ thống là bao nhiêu, đến từ đâu?',
     'Trong vùng gắp được: TB 1,13 mm, lớn nhất 6,2 mm. Sai số lớn đến từ che khuất một phần (tâm phần '
     'nhìn thấy lệch khỏi tâm thật), đã xử lý bằng dự đoán hình bóng và tư thế quan sát.'),
    ('Nếu vật bị che thì sao?',
     'Tính tỉ lệ nhìn thấy so với hình bóng dự đoán; dưới 0,90 thì không tin. Robot quan sát ở tư thế '
     'không che; vật bị vật khác che thì gắp vật phía trước trước rồi quan sát lại. Vật trong khay '
     'dùng khớp mép trên.'),
    ('Vì sao động học ngược chọn nghiệm "khuỷu ra ngoài"?',
     'Mỗi chân có 2 cách lắp; robot thật chỉ lắp một cách. Tiêu chí hình học (dấu đạo hàm) đảm bảo '
     'nghiệm liên tục với vị trí home. Chọn theo "nằm trong giới hạn khớp" không đủ vì có điểm cả 2 '
     'nghiệm đều hợp lệ.'),
    ('Làm sao biết công thức động học đúng?',
     'Ba mức: tính tay tại home; vòng IK → FK trên 5.424 điểm sai 10⁻¹³ m (hai công thức độc lập); ra '
     'lệnh trên Gazebo và đo vị trí thật sai < 1 mm.'),
    ('Tại sao giác hút dùng vị trí thật của mô phỏng, có phải "gian lận"?',
     'Không. Giác hút là mô phỏng PHẦN CỨNG: hút được hay không do vật lý quyết định (có chạm vật '
     'không). Bộ não (lập kế hoạch, chọn điểm hạ xuống) chỉ dùng camera. Nếu camera sai, platform hạ '
     'lệch và giác hút sẽ hút hụt — đúng như thực tế.'),
    ('Kết quả mô phỏng có áp dụng được cho thực tế không?',
     'Phần thuật toán (nhận dạng, hiệu chuẩn, đổi tọa độ) dùng lại nguyên vẹn. Khác biệt: camera thật '
     'có nhiễu, méo ống kính, ánh sáng thay đổi. Đã đánh giá độ bền với nhiễu/độ sáng nhân tạo; Bước 10 '
     'sẽ kiểm chứng với camera thật.'),
    ('Hạn chế hiện tại là gì?',
     'Vật phải có màu phân biệt; vùng ngay sau khay bị che; hình bóng giả định hộp không xoay; mô phỏng '
     'có hạn chế vật lý (platform lún vào vật khi ép, một lần vật văng khi robot gắp vật bên cạnh).'),
]
for i, (q, a) in enumerate(QA, 1):
    p = doc.add_paragraph()
    add_runs(p, f'**Câu {i}. {q}**')
    p.paragraph_format.space_after = Pt(2)
    P(a)

# ---------------------------------------------------------------- phụ lục B
H1('Phụ lục B. Thuật ngữ')
T(['Thuật ngữ', 'Nghĩa'], [
    ['Ground truth', 'Giá trị thật (đáp án) — ở đây là vị trí thật của vật do Gazebo cung cấp'],
    ['IK / FK', 'Động học ngược / thuận'],
    ['Điểm kỳ dị (singularity)', 'Cấu hình robot mất khả năng chuyển động theo một hướng'],
    ['Min-jerk', 'Quỹ đạo làm cực tiểu độ giật, khởi động và dừng êm'],
    ['HSV', 'Không gian màu: sắc độ (Hue), độ bão hòa (Saturation), độ sáng (Value)'],
    ['Mặt nạ (mask)', 'Ảnh nhị phân đánh dấu pixel thỏa điều kiện'],
    ['Tâm khối (centroid)', 'Trọng tâm các pixel của vật trên ảnh'],
    ['Nội / ngoại tham số', 'Đặc tính riêng của camera (K) / vị trí–hướng camera so với robot (R, t)'],
    ['ArUco', 'Loại marker vuông đen trắng mang số hiệu, dễ nhận dạng bằng máy tính'],
    ['PnP', 'Bài toán tìm vị trí–hướng camera từ n cặp điểm 3D–2D'],
    ['Sai số chiếu lại', 'Khoảng cách (pixel) giữa điểm đo được và điểm chiếu lại từ mô hình'],
    ['Bao lồi (convex hull)', 'Đa giác lồi nhỏ nhất bao tất cả các điểm'],
    ['RTF (real-time factor)', 'Tốc độ mô phỏng so với thời gian thực (1,0 = bằng thời gian thực)'],
    ['Digital twin (bản sao số)', 'Mô hình ảo phản ánh trạng thái đối tượng thật'],
], widths=[5.0, 11.0])

# ---------------------------------------------------------------- phụ lục C
H1('Phụ lục C. Tài liệu trong repo')
T(['Đường dẫn', 'Nội dung'], [
    ['`CLAUDE.md`', 'Ghi chép kỹ thuật đầy đủ nhất, cập nhật theo từng bước'],
    ['`docs/bao_cao_kinematics.md`', 'Phần động học viết dạng báo cáo'],
    ['`docs/results/vision_eval.md`, `vision_eval_nhan_xet.md`', 'Số liệu và nhận xét sai số thị giác'],
    ['`docs/results/pick_place_trials.md`, `pick_place_nhan_xet.md`', 'Số liệu và nhận xét gắp–thả'],
    ['`docs/figures/`', 'Hình dùng cho báo cáo/slide'],
    ['`docs/calibration/aruco_markers_A4.pdf`', 'Marker để in cho camera thật'],
    ['`datasets/vision_eval/`', 'Bộ dữ liệu 172 ảnh + vị trí thật'],
    ['`calibration/side_camera.yaml`', 'Kết quả hiệu chuẩn camera mô phỏng'],
], widths=[7.5, 8.5])

doc.save(OUT)
print('Da ghi', OUT)
