"""
Dựng công thức Word THẬT (OMML) cho khóa luận.

Vì sao cần: viết công thức bằng chữ thường rồi đổi phông sang Cambria Math chỉ *trông giống*
công thức. Phân số thành "a/b", chỉ số dưới thành chữ thường, ma trận thành mấy dòng lệch nhau,
và Word không coi đó là công thức nên không căn, không sửa, không đánh số được. OMML (Office Math
Markup Language) là định dạng công thức gốc của Word: mở lên là một công thức thật, bấm vào sửa
được, và hiển thị đúng trên mọi máy.

Các hàm ở đây trả về chuỗi XML, ghép lồng nhau được:

    frac(v('a'), v('b'))                     ->  a/b dạng phân số
    sub(v('x'), n('1'))                      ->  x₁
    sqrt(seq(sup(v('a'), n('2')), op('+'), sup(v('b'), n('2'))))

Quy ước: `v` cho biến (nghiêng, đúng chuẩn toán), `n` cho số, `fn` cho tên hàm (sin, cos — phải
ĐỨNG, không nghiêng), `op` cho toán tử (có khoảng trắng hai bên).
"""

from xml.sax.saxutils import escape

M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'


def _run(text, style=None):
    """Một run toán học. style='p' = đứng (plain), 'i' = nghiêng, None = mặc định của Word."""
    prop = f'<m:rPr><m:sty m:val="{style}"/></m:rPr>' if style else ''
    return f'<m:r>{prop}<m:t xml:space="preserve">{escape(text)}</m:t></m:r>'


def v(name):
    """Biến — Word tự in nghiêng, đúng chuẩn trình bày toán học."""
    return _run(name)


def n(number):
    """Số — in đứng."""
    return _run(str(number), style='p')


def fn(name):
    """Tên hàm (sin, cos, arctan) — phải in ĐỨNG, nghiêng là sai chuẩn."""
    return _run(name, style='p')


def op(symbol, space=True):
    """Toán tử; mặc định chừa khoảng trắng hai bên cho dễ đọc."""
    pad = ' ' if space else ''
    return _run(f'{pad}{symbol}{pad}', style='p')


def txt(text):
    """Chữ thường xen trong công thức (vd. 'với mọi')."""
    return _run(text, style='p')


def seq(*parts):
    """Nối các mảnh lại."""
    return ''.join(parts)


def sub(base, index):
    """Chỉ số dưới: base_index."""
    return f'<m:sSub><m:e>{base}</m:e><m:sub>{index}</m:sub></m:sSub>'


def sup(base, power):
    """Số mũ: base^power."""
    return f'<m:sSup><m:e>{base}</m:e><m:sup>{power}</m:sup></m:sSup>'


def subsup(base, index, power):
    """Vừa chỉ số dưới vừa số mũ."""
    return (f'<m:sSubSup><m:e>{base}</m:e><m:sub>{index}</m:sub>'
            f'<m:sup>{power}</m:sup></m:sSubSup>')


def frac(num, den):
    """Phân số nằm ngang, tử trên mẫu dưới."""
    return f'<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>'


def sqrt(radicand):
    """Căn bậc hai."""
    return (f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr>'
            f'<m:deg/><m:e>{radicand}</m:e></m:rad>')


def delim(body, left='(', right=')'):
    """Dấu ngoặc tự giãn theo chiều cao nội dung."""
    return (f'<m:d><m:dPr><m:begChr m:val="{escape(left)}"/>'
            f'<m:endChr m:val="{escape(right)}"/></m:dPr><m:e>{body}</m:e></m:d>')


def matrix(rows, left='[', right=']'):
    """Ma trận; `rows` là danh sách các hàng, mỗi hàng là danh sách ô."""
    cols = len(rows[0])
    spec = (f'<m:mPr><m:mcs><m:mc><m:mcPr><m:count m:val="{cols}"/>'
            f'<m:mcJc m:val="center"/></m:mcPr></m:mc></m:mcs></m:mPr>')
    body = ''.join('<m:mr>' + ''.join(f'<m:e>{cell}</m:e>' for cell in row) + '</m:mr>'
                   for row in rows)
    return delim(f'<m:m>{spec}{body}</m:m>', left, right)


def cases(rows):
    """Hệ/phân nhánh: một ngoặc nhọn mở, mỗi hàng một dòng."""
    spec = ('<m:mPr><m:mcs><m:mc><m:mcPr><m:count m:val="1"/>'
            '<m:mcJc m:val="left"/></m:mcPr></m:mc></m:mcs></m:mPr>')
    body = ''.join(f'<m:mr><m:e>{row}</m:e></m:mr>' for row in rows)
    return delim(f'<m:m>{spec}{body}</m:m>', '{', '')


def nary(symbol, lower, upper, body):
    """Toán tử lớn (tổng, tích) có cận dưới và cận trên."""
    return (f'<m:nary><m:naryPr><m:chr m:val="{escape(symbol)}"/>'
            f'<m:limLoc m:val="undOvr"/></m:naryPr>'
            f'<m:sub>{lower}</m:sub><m:sup>{upper}</m:sup><m:e>{body}</m:e></m:nary>')
