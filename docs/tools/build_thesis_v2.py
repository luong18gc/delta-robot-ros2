#!/usr/bin/env python3
"""
Dựng khóa luận (bản 2) — Chương 1 và Chương 2.

    python3 docs/tools/build_thesis_v2.py

Định dạng và các hàm dựng nằm ở `thesis_style.py`, dùng chung với các tệp chương khác.
Bìa, phụ bìa, tóm tắt và Mở đầu KHÔNG sinh ở đây — người làm đồ án tự viết.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import omml as m                                                   # noqa: E402
import thesis_style as S                                           # noqa: E402
from thesis_style import (                                         # noqa: E402
    B, BREAK, doc, EQ, H1, H2, H3, IMG, N, P, T,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Khoa_luan_v2.docx')
FIGURES = [
    ('1.1', 'So sánh cấu trúc robot nối tiếp và robot song song',
     'kl_noi_tiep_vs_song_song.png', 15.5),
    ('1.2', 'Cấu trúc robot delta ba bậc tự do và tên gọi các bộ phận',
     'kl_cau_truc_delta.png', 14.5),
    ('1.3', 'Kiến trúc hệ thống của đề tài', 'system_architecture.png', 15.5),
    ('1.4', 'Bố trí thực nghiệm với camera thật: sáu điểm mốc hiệu chuẩn, vùng xét giới hạn '
            'theo hình học và ba vật đã được nhận dạng', 'real_camera_detections.png', 15.0),
    ('2.1', 'Thông số hình học của robot delta trên mặt cắt chứa một chân',
     'kl_thong_so_hinh_hoc.png', 14.5),
    ('2.2', 'Hệ trục tọa độ gắn với đế và góc pha của ba chân, nhìn từ trên xuống',
     'kl_he_truc.png', 10.5),
    ('2.3', 'Bài toán động học ngược của một chân, quy về mặt phẳng chứa chân đó',
     'kl_mat_phang_chan.png', 13.0),
    ('2.4', 'Hai nghiệm của phương trình ràng buộc: khuỷu ra ngoài và khuỷu vào trong',
     'kl_hai_nhanh_khuyu.png', 14.0),
    ('2.5', 'Động học thuận: tâm bàn máy là giao điểm của ba mặt cầu',
     'kl_giao_ba_mat_cau.png', 11.5),
    ('2.6', 'Vùng làm việc của robot: bán kính với tới theo mọi hướng tại từng cao độ',
     'kl_vung_lam_viec.png', 14.5),
    ('2.7', 'Biên dạng chuyển động bậc năm', 'kl_bien_dang_bac_nam.png', 13.0),
    ('2.8', 'Quỹ đạo an toàn ba đoạn so với đường đi thẳng',
     'kl_quy_dao_an_toan.png', 14.5),
]
TABLES = [
    ('1.1', 'So sánh đặc tính của robot nối tiếp và robot song song'),
    ('1.2', 'Ba mức tích hợp giữa đối tượng thật và mô hình số theo Kritzinger'),
    ('2.1', 'Thông số hình học của robot, trích từ mô hình URDF'),
    ('2.2', 'Ký hiệu dùng trong chương'),
    ('2.3', 'Bán kính vùng làm việc theo cao độ'),
    ('2.4', 'Kết quả kiểm chứng động học trên mô phỏng vật lý'),
]
S.configure(OUT, FIGURES, TABLES)


# ================================================================== CHƯƠNG 1

H1('CHƯƠNG 1. TỔNG QUAN', page_break=False)

P('Chương này trình bày bối cảnh của đề tài theo ba mạch: cơ cấu robot được điều khiển, vai trò '
  'của thị giác máy tính trong việc cung cấp vị trí vật thể, và khái niệm bản sao số — khung khái '
  'niệm cho việc dùng tín hiệu từ thế giới thật để điều khiển một robot trong mô phỏng. Phần cuối '
  'chương xác định mục tiêu, phạm vi và phương pháp nghiên cứu.')

H2('1.1. Robot song song và robot delta')

H3('1.1.1. Hai cách tổ chức cơ cấu')

P('Theo cách nối các khâu, robot công nghiệp chia thành hai nhóm lớn. **Robot nối tiếp** có các '
  'khâu xâu chuỗi liên tiếp, mỗi khớp mang theo toàn bộ phần cơ cấu phía sau nó. **Robot song '
  'song** có khâu cuối được đỡ đồng thời bởi nhiều chuỗi động học nối từ đế tới, tạo thành một '
  'hoặc nhiều mạch kín (Hình 1.1).')

IMG('1.1')

P('Sự khác nhau về cấu trúc kéo theo khác nhau về đặc tính. Ở robot nối tiếp, động cơ của khớp '
  'thứ nhất phải mang khối lượng của tất cả các khâu còn lại, nên khâu phải đủ cứng và do đó đủ '
  'nặng; quán tính lớn làm hạn chế gia tốc. Ngược lại, robot song song đặt toàn bộ động cơ trên '
  'đế cố định, phần chuyển động chỉ còn các thanh nhẹ, nhờ vậy đạt gia tốc rất cao.')

T('1.1',
  ['Tiêu chí', 'Robot nối tiếp', 'Robot song song'],
  [
      ('Vị trí động cơ', 'Trên các khâu chuyển động', 'Trên đế cố định'),
      ('Quán tính phần chuyển động', 'Lớn', 'Rất nhỏ'),
      ('Gia tốc đạt được', 'Trung bình', 'Rất cao'),
      ('Độ cứng vững', 'Giảm dần về phía khâu cuối', 'Cao, tải chia cho nhiều chuỗi'),
      ('Không gian làm việc', 'Rộng', 'Hẹp hơn nhiều'),
      ('Động học thuận', 'Dạng đóng, đơn giản', 'Phức tạp hơn'),
      ('Động học ngược', 'Phức tạp hơn', 'Dạng đóng, đơn giản'),
  ],
  widths=[4.6, 5.7, 5.7])

P('Bảng 1.1 cho thấy một đặc điểm đáng chú ý: **quan hệ giữa hai bài toán động học bị đảo ngược** '
  'so với robot nối tiếp. Với robot song song, bài toán động học ngược — từ vị trí mong muốn của '
  'khâu cuối suy ra các góc khớp — lại là bài toán dễ hơn và có lời giải dạng đóng. Đây chính là '
  'bài toán mà hệ điều khiển cần giải ở mỗi chu kỳ, nên đặc điểm này là một lợi thế thực tế chứ '
  'không chỉ là chi tiết lý thuyết.')

H3('1.1.2. Robot delta')

P('Robot delta do Reymond Clavel đề xuất năm 1985 và được cấp bằng sáng chế năm 1990 [3] là cơ '
  'cấu song song phổ biến nhất hiện nay. Cấu trúc gồm một đế cố định mang ba động cơ, ba cánh tay '
  'trên, và ba **cặp** thanh chống nối xuống bàn máy động (Hình 1.2).')

IMG('1.2')

P('Điểm cốt lõi của thiết kế nằm ở các **cặp** thanh chống. Mỗi cặp cùng với đoạn cánh tay trên '
  'và đoạn bàn máy tương ứng tạo thành một **hình bình hành không gian**. Hình bình hành giữ cho '
  'đoạn bàn máy luôn song song với đoạn cánh tay, và do ba chân cùng ràng buộc như vậy nên bàn '
  'máy **luôn song song với đế** trong mọi tư thế.')

P('Hệ quả là robot chỉ còn **ba bậc tự do tịnh tiến**, không có bậc tự do quay. Với thao tác gắp '
  'và thả vật có trục đối xứng đứng — chai, lon, viên thuốc, bánh kẹo — ba bậc tự do tịnh tiến là '
  'vừa đủ, và việc loại bỏ các bậc tự do quay chính là thứ cho phép rút gọn cơ cấu tới mức đạt '
  'được gia tốc rất cao.')

P('Nhờ đặc tính đó, robot delta thống trị các dây chuyền gắp–thả tốc độ cao trong công nghiệp '
  'thực phẩm, dược phẩm và đóng gói, nơi robot phải nhặt vật đang chạy trên băng chuyền với nhịp '
  'hàng trăm lần mỗi phút.')

H2('1.2. Thị giác máy tính trong điều khiển robot')

P('Robot chỉ thao tác được với vật ở vị trí biết trước nếu vị trí đó được cố định bằng đồ gá. Khi '
  'vật tới với vị trí không biết trước — chẳng hạn trên băng chuyền — hệ điều khiển phải nhận vị '
  'trí từ một cảm biến ngoài, mà phổ biến nhất là camera.')

H3('1.2.1. Hai cách bố trí camera')

P('Camera có thể gắn **trên khâu cuối** (eye-in-hand) hoặc **cố định ngoài** nhìn bao quát vùng '
  'làm việc (eye-to-hand). Cách thứ nhất cho ảnh cận cảnh và tỉ lệ ổn định, nhưng ảnh thay đổi '
  'theo từng chuyển động của robot và dây cáp phải đi theo phần chuyển động. Cách thứ hai cho một '
  'hệ quy chiếu cố định, quan sát được toàn cảnh và không làm tăng khối lượng phần chuyển động — '
  'phù hợp với robot delta, vốn lấy việc giữ phần chuyển động thật nhẹ làm nguyên tắc thiết kế. '
  'Đề tài này dùng cách thứ hai.')

H3('1.2.2. Các hướng nhận dạng vật thể')

P('Việc xác định vật trong ảnh có ba hướng chính, khác nhau ở thứ được dùng làm đặc trưng:')

B([
    '**Phân đoạn theo màu**: lọc điểm ảnh theo khoảng màu trong một không gian màu tách bạch sắc '
    'độ khỏi độ sáng, thường là HSV. Rất nhanh và không cần dữ liệu huấn luyện, nhưng ngưỡng gắn '
    'chặt với điều kiện chiếu sáng.',
    '**Tách nền rồi phân loại**: trước hết tách vật khỏi nền, sau đó mới xác định vật đó là gì. '
    'Ưu điểm là vùng thu được chính là **hình bóng** của vật, nên mọi phép suy luận hình học dựa '
    'trên nó đều có nghĩa.',
    '**Học sâu**: mạng nơ-ron phát hiện vật trực tiếp từ ảnh. Mạnh và tổng quát nhưng cần dữ liệu '
    'có nhãn và tài nguyên tính toán lớn hơn.',
])

P('Đề tài dùng hai hướng đầu, và việc chọn hướng nào cho môi trường nào là một kết quả của đề '
  'tài chứ không phải quyết định đặt sẵn — được trình bày ở các chương sau.')

H3('1.2.3. Hiệu chuẩn và phép đổi tọa độ')

P('Nhận ra vật trong ảnh mới chỉ cho tọa độ **điểm ảnh**. Muốn robot tới được vật, cần đổi sang '
  'tọa độ trong hệ quy chiếu của robot, và phép đổi đó đòi hỏi **hiệu chuẩn** hai nhóm tham số:')

B([
    '**Nội tham số** — tiêu cự, tâm ảnh và các hệ số méo ống kính; gắn với từng máy cụ thể, kể cả '
    'hai máy cùng kiểu.',
    '**Ngoại tham số** — vị trí và hướng của camera so với hệ quy chiếu của robot.',
])

P('Một camera đơn không đo được chiều sâu, nên phép đổi từ điểm ảnh sang tọa độ không gian chỉ '
  'xác định được khi có thêm một ràng buộc. Trong đề tài này, ràng buộc đó là **vật đứng trên một '
  'mặt phẳng đã biết cao độ**, nhờ vậy tọa độ được xác định bằng phép giao tia nhìn với mặt phẳng.')

H2('1.3. Bản sao số')

P('Việc dùng tín hiệu từ thế giới thật để điều khiển một mô hình số nằm trong khung khái niệm '
  '**bản sao số** (digital twin). Kritzinger và cộng sự [8] phân biệt ba mức theo **chiều của '
  'luồng dữ liệu** giữa đối tượng thật và mô hình số.')

T('1.2',
  ['Mức', 'Luồng dữ liệu', 'Đặc điểm'],
  [
      ('Mô hình số', 'Không tự động theo chiều nào',
       'Mô hình dựng và cập nhật thủ công'),
      ('Bóng số', 'Tự động một chiều: thật → số',
       'Trạng thái vật thật tự động cập nhật vào mô hình'),
      ('Bản sao số', 'Tự động hai chiều',
       'Mô hình cũng tác động ngược lại đối tượng thật'),
  ],
  widths=[3.4, 5.0, 7.6])

P('Cách phân loại này giúp phát biểu chính xác phạm vi của đề tài thay vì dùng thuật ngữ cho kêu, '
  'và sẽ được dùng lại ở chương tích hợp để xác định hệ thống đạt tới mức nào.')

H2('1.4. Mục tiêu, đối tượng và phạm vi nghiên cứu')

H3('1.4.1. Mục tiêu')

P('Xây dựng một hệ thống hoàn chỉnh trong đó **thị giác máy tính từ camera thật** cung cấp vị trí '
  'vật thể cho robot delta ba bậc tự do thực hiện thao tác gắp–thả trong môi trường mô phỏng, và '
  '**đánh giá định lượng** độ chính xác của từng khâu.')

IMG('1.3')

H3('1.4.2. Đối tượng nghiên cứu')

B([
    'Robot delta ba bậc tự do dạng quay, mô phỏng trong ROS 2 và Gazebo với mạch động học kín.',
    'Khối thị giác dùng một camera đơn đặt cố định, quan sát xiên xuống mặt bàn.',
    'Vật thể là lon nước giải khát có ba màu phân biệt, đặt trên mặt bàn thật.',
])

IMG('1.4')

H3('1.4.3. Phạm vi nghiên cứu')

P('Đề tài giới hạn trong các nội dung sau:')

B([
    'Robot nằm **trong mô phỏng**; không chế tạo robot vật lý. Thao tác gắp dùng mô hình giác hút '
    'có dung sai đặt theo giác hút thật.',
    'Camera là **camera thật**, vật là **vật thật**; phần nhận thức hoàn toàn làm trên dữ liệu thật.',
    'Vật được giả thiết đứng trên mặt phẳng đã biết cao độ và có trục đối xứng đứng; không ước '
    'lượng góc xoay của vật.',
    'Mỗi màu ứng với đúng một vật trong cảnh.',
])

H2('1.5. Phương pháp nghiên cứu')

P('Đề tài áp dụng nhất quán bốn nguyên tắc làm việc, và chính các nguyên tắc này quyết định cách '
  'trình bày kết quả ở các chương sau:')

N([
    '**Mọi công thức được kiểm chứng bằng một cấu hình đã biết trước khi tin dùng.** Tư thế gốc '
    'của robot cho một nghiệm biết trước, dùng làm phép thử bắt buộc cho công thức động học.',
    '**Mọi khâu được đo sai số riêng**, với đối chứng lấy từ mô phỏng hoặc từ phép đo bằng thước, '
    'thay vì chỉ đánh giá kết quả cuối cùng.',
    '**Mọi ngưỡng được chọn bằng dữ liệu**, kèm số liệu cho thấy vì sao chọn giá trị đó.',
    '**Phần tính toán tách khỏi nền tảng ROS** để kiểm thử tự động được mà không cần mở mô phỏng.',
])

H2('1.6. Bố cục khóa luận')

B([
    '**Chương 1** trình bày tổng quan về robot song song, thị giác máy tính trong điều khiển '
    'robot và khái niệm bản sao số, cùng mục tiêu và phạm vi của đề tài.',
    '**Chương 2** xây dựng và kiểm chứng mô hình động học của robot delta, gồm động học ngược '
    'dạng đóng, động học thuận và quy hoạch quỹ đạo.',
    '**Chương 3** mô tả việc xây dựng môi trường mô phỏng và cơ cấu tương tác với vật thể.',
    '**Chương 4** trình bày khối thị giác máy tính.',
    '**Chương 5** trình bày việc tích hợp và kết quả thực nghiệm.',
    '**Chương 6** tổng kết và nêu hướng phát triển.',
])

H2('1.7. Kết luận chương')

P('Chương 1 đã xác định robot delta là cơ cấu song song có quán tính nhỏ và gia tốc cao, với đặc '
  'điểm quan trọng là **động học ngược — bài toán mà hệ điều khiển phải giải liên tục — có lời '
  'giải dạng đóng**. Chương cũng đã nêu vai trò của thị giác máy tính trong việc cung cấp vị trí '
  'vật, hai nhóm tham số cần hiệu chuẩn, và khung khái niệm bản sao số dùng để xác định phạm vi '
  'của hệ thống.')

P('Chương tiếp theo xây dựng mô hình động học của robot — nền tảng mà toàn bộ phần điều khiển và '
  'phần thị giác sẽ dựa vào.')


# ================================================================== CHƯƠNG 2
# Viết tắt cho gọn khi dựng công thức
v, nn, fnc, o, sq = m.v, m.n, m.fn, m.op, m.seq
sb, sp, fr, dl, mx, sqr, txt = m.sub, m.sup, m.frac, m.delim, m.matrix, m.sqrt, m.txt
TH, PH = 'θ', 'φ'

H1('CHƯƠNG 2. ĐỘNG HỌC ROBOT DELTA')

P('Chương này xây dựng mô hình động học của robot delta ba bậc tự do: từ thông số hình học đọc '
  'được trong mô hình robot, lập phương trình ràng buộc cho từng chân, giải động học ngược dạng '
  'đóng, giải động học thuận, xác định vùng làm việc và quy hoạch quỹ đạo. Mỗi bước đều kèm phép '
  'kiểm chứng bằng cấu hình đã biết hoặc bằng số liệu đo trên mô phỏng vật lý.')

H2('2.1. Cơ cấu và thông số hình học')

P('Robot trong đề tài là robot delta **dạng quay** theo thiết kế của Clavel: ba khớp chủ động là '
  'khớp quay đặt trên đế, nên đại lượng điều khiển là **góc quay**. Hình 2.1 mô tả bốn thông số '
  'hình học trên mặt cắt chứa một chân.')

IMG('2.1')

T('2.1',
  ['Ký hiệu', 'Ý nghĩa', 'Giá trị'],
  [
      ('*f*', 'Bán kính đế cố định — khoảng cách từ tâm đế tới trục khớp chủ động', '41,7 mm'),
      ('*e*', 'Bán kính bàn máy động — khoảng cách từ tâm bàn máy tới khớp cầu', '27,6 mm'),
      ('*r_f*', 'Chiều dài cánh tay trên', '75,8 mm'),
      ('*r_e*', 'Chiều dài thanh chống', '166,8 mm'),
      ('Giới hạn khớp', 'Khoảng quay cho phép của khớp chủ động', 'Từ −1,0297 tới 1,4312 rad'),
  ],
  widths=[2.8, 9.0, 4.2])

P('Các giá trị trong Bảng 2.1 không phải thông số thiết kế tự chọn mà được **trích từ chính mô '
  'hình robot** dùng trong mô phỏng, cụ thể là các phép tịnh tiến khai báo giữa các khâu trong '
  'tệp mô tả robot. Nhờ vậy mô hình toán và mô hình mô phỏng dùng chung một bộ số, loại trừ khả '
  'năng sai lệch giữa công thức và đối tượng được điều khiển.')

H2('2.2. Hệ trục tọa độ và ký hiệu')

P('Hệ quy chiếu gắn với đế robot, gốc **O** đặt tại tâm đế. Trục *X* hướng ra chân thứ nhất, trục '
  '*Z* hướng **lên trên**, trục *Y* xác định theo quy tắc bàn tay phải. Vì bàn máy luôn nằm phía '
  'dưới đế nên cao độ của nó luôn mang dấu âm.')

IMG('2.2')

P('Ba chân bố trí đối xứng, lệch nhau 120°. Góc pha của chân thứ *i* là:')

EQ(sq(sb(v(PH), v('i')), o('='), dl(sq(v('i'), o('−'), nn(1))), o('·'), nn('120°'), o(','),
      v('i'), o('='), nn('1, 2, 3')), '2.1')

P('Vị trí bàn máy được mô tả bằng tọa độ tâm của nó:')

EQ(sq(v('P'), o('='), mx([[sb(v('x'), nn(0))], [sb(v('y'), nn(0))], [sb(v('z'), nn(0))]])),
   '2.2')

T('2.2',
  ['Ký hiệu', 'Ý nghĩa', 'Đơn vị'],
  [
      ('*x₀, y₀, z₀*', 'Tọa độ tâm bàn máy trong hệ gắn với đế', 'm'),
      ('*θᵢ*', 'Góc quay của khớp chủ động chân thứ *i*', 'rad'),
      ('*φᵢ*', 'Góc pha của chân thứ *i*', 'rad'),
      ('*Aᵢ*', 'Tâm khớp chủ động (vai) của chân thứ *i*', '—'),
      ('*Bᵢ*', 'Khuỷu — nối cánh tay trên với thanh chống', '—'),
      ('*Cᵢ*', 'Khớp cầu nối thanh chống với bàn máy', '—'),
  ],
  widths=[3.0, 9.4, 3.6])

P('Quy ước dấu của góc khớp: *θᵢ* = 0 khi cánh tay trên nằm **ngang**, hướng ra ngoài; *θᵢ* tăng '
  'khi cánh tay hạ xuống. Quy ước này lấy theo mô hình robot, và tư thế *θ₁* = *θ₂* = *θ₃* = 0 là '
  '**tư thế gốc** sẽ được dùng làm phép kiểm chứng ở mục 2.3.5.')

H2('2.3. Động học ngược')

P('Bài toán động học ngược: cho trước vị trí mong muốn của tâm bàn máy, tìm ba góc khớp đưa robot '
  'tới vị trí đó. Đây là bài toán hệ điều khiển phải giải ở mỗi chu kỳ, nên cần lời giải **dạng '
  'đóng**, tính được trong thời gian xác định, thay vì lặp số.')

H3('2.3.1. Quy bài toán về mặt phẳng')

P('Nhờ tính đối xứng, bài toán ba chiều tách thành **ba bài toán phẳng độc lập**. Với mỗi chân, '
  'quay hệ tọa độ quanh trục *Z* một góc *φᵢ* để trục *X* mới trùng với hướng của chân đó:')

EQ(sq(mx([[sb(v('x'), v('i'))], [sb(v('y'), v('i'))], [sb(v('z'), v('i'))]]), o('='),
      mx([[sq(fnc('cos'), sb(v(PH), v('i'))), sq(fnc('sin'), sb(v(PH), v('i'))), nn(0)],
          [sq(o('−', False), fnc('sin'), sb(v(PH), v('i'))),
           sq(fnc('cos'), sb(v(PH), v('i'))), nn(0)],
          [nn(0), nn(0), nn(1)]]),
      mx([[sb(v('x'), nn(0))], [sb(v('y'), nn(0))], [sb(v('z'), nn(0))]])), '2.3')

P('Trong hệ cục bộ này, vai của chân nằm trên trục hoành tại khoảng cách *f* tính từ gốc, còn '
  'khớp cầu trên bàn máy nằm tại khoảng cách *xᵢ* + *e* (Hình 2.3). Chi tiết dấu cộng ở đây rất '
  'dễ nhầm và hậu quả được phân tích ở mục 2.3.5.')

IMG('2.3')

H3('2.3.2. Phương trình ràng buộc')

P('Khuỷu *Bᵢ* nằm trên cánh tay trên, cách vai một đoạn *r_f* theo hướng ứng với góc *θᵢ*:')

EQ(sq(sb(v('B'), v('i')), o('='),
      dl(sq(v('f'), o('+'), sb(v('r'), v('f')), fnc('cos'), sb(v(TH), v('i')),
            txt(' ,  '),
            o('−', False), sb(v('r'), v('f')), fnc('sin'), sb(v(TH), v('i'))))), '2.4')

P('Ràng buộc duy nhất của cơ cấu là **thanh chống không đổi chiều dài**: khoảng cách từ khuỷu tới '
  'khớp cầu trên bàn máy luôn bằng *r_e*. Viết dưới dạng bình phương để tránh căn thức:')

EQ(sq(sp(dl(sq(sb(v('x'), v('i')), o('+'), v('e'), o('−'), v('f'), o('−'),
                sb(v('r'), v('f')), fnc('cos'), sb(v(TH), v('i')))), nn(2)), o('+'),
      sp(sb(v('y'), v('i')), nn(2)), o('+'),
      sp(dl(sq(sb(v('z'), v('i')), o('+'), sb(v('r'), v('f')), fnc('sin'),
                sb(v(TH), v('i')))), nn(2)), o('='), sp(sb(v('r'), v('e')), nn(2))), '2.5')

P('Khai triển và nhóm các số hạng chứa *θᵢ*, phương trình (2.5) rút về dạng tuyến tính theo '
  'cosin và sin của ẩn:')

EQ(sq(sb(v('A'), v('i')), fnc('cos'), sb(v(TH), v('i')), o('+'),
      sb(v('B'), v('i')), fnc('sin'), sb(v(TH), v('i')), o('+'), sb(v('C'), v('i')),
      o('='), nn(0)), '2.6')

P('với các hệ số, sau khi đặt *aᵢ* = *xᵢ* + *e* − *f*:')

EQ(m.cases([
    sq(sb(v('A'), v('i')), o('='), o('−', False), nn(2), sb(v('r'), v('f')), sb(v('a'), v('i'))),
    sq(sb(v('B'), v('i')), o('='), nn(2), sb(v('r'), v('f')), sb(v('z'), v('i'))),
    sq(sb(v('C'), v('i')), o('='), sp(sb(v('a'), v('i')), nn(2)), o('+'),
       sp(sb(v('y'), v('i')), nn(2)), o('+'), sp(sb(v('z'), v('i')), nn(2)), o('+'),
       sp(sb(v('r'), v('f')), nn(2)), o('−'), sp(sb(v('r'), v('e')), nn(2))),
]), '2.7')

H3('2.3.3. Giải bằng phép thế Weierstrass')

P('Phương trình (2.6) chứa đồng thời cosin và sin của cùng một ẩn nên không giải trực tiếp được. '
  'Phép thế Weierstrass đưa nó về phương trình đại số bằng cách đặt:')

EQ(sq(v('t'), o('='), fnc('tan'), fr(sb(v(TH), v('i')), nn(2)), o(','), txt('   '),
      fnc('cos'), sb(v(TH), v('i')), o('='), fr(sq(nn(1), o('−'), sp(v('t'), nn(2))),
                                                sq(nn(1), o('+'), sp(v('t'), nn(2)))),
      o(','), txt('   '),
      fnc('sin'), sb(v(TH), v('i')), o('='), fr(sq(nn(2), v('t')),
                                                sq(nn(1), o('+'), sp(v('t'), nn(2))))), '2.8')

P('Thay vào (2.6) rồi nhân hai vế với 1 + *t*², phương trình trở thành bậc hai theo *t*:')

EQ(sq(dl(sq(sb(v('C'), v('i')), o('−'), sb(v('A'), v('i')))), sp(v('t'), nn(2)), o('+'),
      nn(2), sb(v('B'), v('i')), v('t'), o('+'),
      dl(sq(sb(v('A'), v('i')), o('+'), sb(v('C'), v('i')))), o('='), nn(0)), '2.9')

P('Nghiệm của (2.9) và góc khớp tương ứng:')

EQ(sq(v('t'), o('='), fr(sq(o('−', False), sb(v('B'), v('i')), o('±'),
                            sqr(sq(sp(sb(v('A'), v('i')), nn(2)), o('+'),
                                   sp(sb(v('B'), v('i')), nn(2)), o('−'),
                                   sp(sb(v('C'), v('i')), nn(2))))),
                         sq(sb(v('C'), v('i')), o('−'), sb(v('A'), v('i')))),
      o(','), txt('   '),
      sb(v(TH), v('i')), o('='), nn(2), fnc('arctan'), v('t')), '2.10')

P('Biểu thức dưới dấu căn trong (2.10) cho ngay **điều kiện tồn tại nghiệm**: nếu nó âm thì chân '
  'thứ *i* không với tới điểm đã cho, và điểm đó nằm ngoài vùng làm việc. Đây là cách kiểm tra '
  'tầm với mà không cần phép thử riêng nào khác.')

H3('2.3.4. Chọn nghiệm: hai nhánh khuỷu')

P('Phương trình bậc hai cho **hai nghiệm**, ứng với hai tư thế hình học đều thỏa mãn ràng buộc '
  'chiều dài: khuỷu gập **ra ngoài** hoặc **vào trong** (Hình 2.4).')

IMG('2.4')

P('Một cách chọn nghiệm thường gặp là lấy nghiệm nào nằm trong giới hạn khớp. Cách này **không '
  'đủ**: khảo sát riêng một chân vẫn có những điểm mà **cả hai nghiệm đều nằm trong giới hạn** — '
  'chẳng hạn chân thứ nhất tại *x* = −90 mm, *z* = −20 mm cho hai nghiệm 0,641 rad và −1,020 rad, '
  'đều hợp lệ. Khi đó quy tắc này không quyết định được, và nếu lời giải nhảy qua lại giữa hai '
  'nhánh ở các điểm liên tiếp thì robot sẽ giật.')

P('Tiêu chí đúng là chọn nhánh **liên tục với tư thế gốc**, tức nhánh khuỷu ra ngoài. Nhánh này '
  'được nhận biết bằng dấu của đạo hàm vế trái của (2.6) theo *θᵢ*:')

EQ(sq(o('−', False), sb(v('A'), v('i')), fnc('sin'), sb(v(TH), v('i')), o('+'),
      sb(v('B'), v('i')), fnc('cos'), sb(v(TH), v('i')), o('≤'), nn(0)), '2.11')

P('Hai nghiệm của (2.9) luôn cho đạo hàm trái dấu nhau, nên điều kiện (2.11) tách bạch được hai '
  'nhánh trong mọi trường hợp. Tại tư thế gốc, *θᵢ* = 0 nên vế trái bằng *Bᵢ* = 2*r_f z_i* < 0, '
  'thỏa mãn — xác nhận tư thế gốc nằm trên nhánh được chọn. Chỉ sau khi chọn nhánh, lời giải mới '
  'được kiểm tra với giới hạn khớp.')

H3('2.3.5. Kiểm chứng bằng tư thế gốc')

P('Trước khi tin dùng, công thức được thử với một cấu hình đã biết trước đáp án. Tại tư thế gốc, '
  'mô hình robot cho tâm bàn máy ở (0; 0; −140,5) mm; thay vào (2.7) với chân thứ nhất:')

EQ(sq(sb(v('a'), nn(1)), o('='), v('e'), o('−'), v('f'), o('='),
      o('−', False), nn('0,0141'), txt(' m')), '2.12')

EQ(sq(sb(v('A'), nn(1)), o('+'), sb(v('C'), nn(1)), o('='), nn('0,002138'), o('−'),
      nn('0,002137'), o('≈'), nn(0)), '2.13')

P('Số hạng tự do của (2.9) triệt tiêu, nên *t* = 0 và *θ₁* = 0 — đúng bằng giá trị ghi trong mô '
  'hình robot. Phép thử tuy đơn giản nhưng đã bắt được một lỗi dấu trong phiên bản đầu: khi viết '
  'nhầm *aᵢ* = *xᵢ* − *e* − *f*, tư thế gốc cho cao độ −82,3 mm thay vì −140,5 mm. Sai lệch gần '
  '60 mm này sẽ rất khó truy nếu chỉ nhìn robot chạy trong mô phỏng.')

H2('2.4. Động học thuận')

P('Bài toán ngược lại — từ ba góc khớp suy ra vị trí bàn máy — cần cho hai việc: xác định vị trí '
  'thật của đầu công tác từ cảm biến góc khớp, và kiểm chứng chéo lời giải động học ngược.')

P('Khi ba góc khớp đã biết, ba khuỷu *Bᵢ* có vị trí xác định theo (2.4). Vì thanh chống có chiều '
  'dài không đổi, khớp cầu *Cᵢ* nằm trên **mặt cầu** tâm *Bᵢ* bán kính *r_e*. Tâm bàn máy *P* '
  'cách *Cᵢ* đúng một đoạn *e* theo phương nằm ngang hướng ra chân thứ *i*, nên dịch tâm mỗi mặt '
  'cầu đi một đoạn *e* ngược hướng đó sẽ thu được ba mặt cầu **cùng đi qua** *P*:')

EQ(sq(sb(v('S'), v('i')), o(':'), txt('   '),
      sp(m.delim(sq(v('P'), o('−'), sb(v('B'), v('i')), o('+'), v('e'),
                    sb(v('u'), v('i'))), '‖', '‖'), nn(2)),
      o('='), sp(sb(v('r'), v('e')), nn(2))), '2.14')

P('trong đó *uᵢ* = (cos *φᵢ*, sin *φᵢ*, 0) là vectơ đơn vị hướng ra chân thứ *i*. Vị trí bàn máy '
  'là **giao điểm của ba mặt cầu** (Hình 2.5).')

IMG('2.5')

P('Trừ từng cặp phương trình (2.14) cho nhau sẽ khử hết các số hạng bậc hai, thu được hai phương '
  'trình **tuyến tính** — mỗi phương trình là một mặt phẳng. Giao của hai mặt phẳng là một đường '
  'thẳng; thay tham số của đường thẳng đó vào một mặt cầu bất kỳ sẽ được phương trình bậc hai với '
  'hai nghiệm. Hai nghiệm ứng với hai giao điểm đối xứng nhau qua mặt phẳng chứa ba tâm; **nghiệm '
  'đúng là nghiệm có cao độ nhỏ hơn**, vì bàn máy luôn nằm phía dưới đế.')

P('Hai lời giải được xây dựng hoàn toàn độc lập — một dùng phép thế Weierstrass, một dùng phép '
  'giao ba mặt cầu — nên việc chúng khử lẫn nhau là một phép kiểm chứng mạnh, được trình bày ở '
  'mục 2.7.')

H2('2.5. Vùng làm việc')

P('Vùng làm việc là tập các điểm mà **cả ba chân** cùng với tới và cùng thỏa mãn giới hạn khớp. '
  'Biên của vùng này xác định bằng cách quét: với mỗi cao độ, dò bán kính lớn nhất mà mọi hướng '
  'đều giải được động học ngược (Hình 2.6).')

IMG('2.6')

T('2.3',
  ['Cao độ *z₀*', 'Bán kính với tới theo mọi hướng', 'Ghi chú'],
  [
      ('−140,5 mm', '129 mm', 'Cao độ tư thế gốc'),
      ('−160 mm', '122 mm', 'Cao độ di chuyển an toàn'),
      ('−190 mm', '96 mm', 'Cao độ gắp vật trên bàn'),
      ('−220 mm', '58 mm', 'Cao độ mặt bàn'),
  ],
  widths=[3.6, 6.6, 5.8])

P('Bảng 2.3 cho thấy một đặc điểm quan trọng của robot delta: **vùng làm việc thu hẹp rất nhanh '
  'khi xuống thấp**. Bán kính giảm hơn một nửa khi hạ từ tư thế gốc xuống mặt bàn. Đây là ràng '
  'buộc chi phối việc bố trí vật thể và khay chứa ở các chương sau — vật đặt quá xa tâm sẽ nằm '
  'ngoài tầm với đúng ở cao độ cần hạ xuống để gắp.')

H2('2.6. Quy hoạch quỹ đạo')

P('Giải được động học ngược mới chỉ cho phép đưa robot tới một điểm. Muốn robot di chuyển trơn '
  'tru cần sinh ra **chuỗi điểm trung gian** theo thời gian, sao cho vận tốc và gia tốc liên tục.')

H3('2.6.1. Biên dạng bậc năm')

P('Với đoạn thẳng từ điểm đầu tới điểm cuối, quãng đường đi được theo thời gian dùng đa thức bậc '
  'năm theo thời gian chuẩn hóa *τ* = *t*/*T*:')

EQ(sq(v('s'), dl(v('τ')), o('='), nn(10), sp(v('τ'), nn(3)), o('−'), nn(15),
      sp(v('τ'), nn(4)), o('+'), nn(6), sp(v('τ'), nn(5))), '2.15')

P('Bậc năm là **bậc thấp nhất** thỏa mãn đồng thời sáu điều kiện biên: vị trí, vận tốc và gia tốc '
  'xác định tại cả hai đầu. Cho vận tốc và gia tốc bằng 0 ở hai đầu thì robot khởi hành và dừng '
  'lại êm, không giật (Hình 2.7).')

IMG('2.7')

P('Vận tốc lớn nhất đạt tại giữa quãng đường và liên hệ với chiều dài *L*, thời gian *T* theo:')

EQ(sq(sb(v('v'), txt('max')), o('='), nn('1,875'), fr(v('L'), v('T'))), '2.16')

P('Hệ số 1,875 cho biết vận tốc đỉnh cao hơn vận tốc trung bình 87,5%. Quan hệ này dùng để chọn '
  'thời gian *T* khi đã biết chiều dài đoạn và vận tốc tối đa cho phép.')

H3('2.6.2. Quỹ đạo an toàn ba đoạn')

P('Đi thẳng từ điểm này sang điểm khác ở cao độ thấp sẽ quét ngang qua các vật đang đứng trên '
  'bàn. Quỹ đạo an toàn chia chuyển động thành ba đoạn: **nâng** thẳng đứng lên cao độ an toàn, '
  '**đi ngang** ở cao độ đó, rồi **hạ** thẳng đứng xuống đích (Hình 2.8).')

IMG('2.8')

P('Toàn bộ chuỗi điểm của cả ba đoạn được **giải động học ngược trước khi robot bắt đầu chuyển '
  'động**. Nếu có bất kỳ điểm trung gian nào nằm ngoài vùng làm việc, lệnh bị từ chối ngay và '
  'robot không nhúc nhích. Cách này quan trọng vì điểm đầu và điểm cuối có thể đều hợp lệ trong '
  'khi một điểm giữa đường lại không — kiểm tra hai đầu là không đủ.')

H2('2.7. Kiểm chứng mô hình động học')

P('Mô hình được kiểm chứng theo ba mức độc lập, từ tính tay tới mô phỏng vật lý.')

P('**Mức 1 — kiểm chứng bằng tay.** Thay tư thế gốc vào công thức, thu được *θ₁* = 0 đúng như mô '
  'hình robot (mục 2.3.5).')

P('**Mức 2 — vòng lặp động học ngược rồi thuận.** Với 5 424 điểm phủ khắp vùng làm việc, mỗi điểm '
  'được giải động học ngược ra ba góc khớp rồi giải động học thuận trở lại. Sai lệch lớn nhất '
  'giữa điểm thu được và điểm ban đầu là **5×10⁻¹³ m**, tức cỡ sai số làm tròn của máy tính. Phép '
  'thử này có sức thuyết phục cao vì hai công thức được xây dựng **hoàn toàn độc lập** — một dùng '
  'phép thế Weierstrass, một dùng phép giao ba mặt cầu — nên việc chúng khử lẫn nhau tới mức đó '
  'cho thấy cả hai đều đúng.')

P('**Mức 3 — đo trên mô phỏng vật lý.** Robot được ra lệnh tới chín điểm, sau đó đọc vị trí thật '
  'của đầu công tác từ mô phỏng.')

T('2.4',
  ['Điểm ra lệnh (mm)', 'Vị trí đo được (mm)', 'Sai lệch'],
  [
      ('(0; 0; −140,5)', '(0,2; −0,2; −140,6)', '< 0,3 mm'),
      ('(0; 0; −120)', '(0,1; −0,1; −119,9)', '< 0,2 mm'),
      ('(40; 0; −190)', '(40,3; −0,2; −190,4)', '< 0,6 mm'),
      ('(−40; −30; −190)', '(−40,6; −30,4; −190,8)', '< 1,0 mm'),
  ],
  widths=[5.2, 5.6, 5.2])

P('Sai lệch dưới 1 mm, và phần lớn là do bàn máy võng nhẹ dưới tác dụng của trọng lực cùng sai số '
  'bám của bộ điều khiển khớp — tức là **sai số của cơ cấu, không phải của mô hình toán**. Mức '
  'này nhỏ hơn nhiều so với dung sai của thao tác gắp nên không ảnh hưởng tới chức năng.')

H2('2.8. Kết luận chương')

P('Chương 2 đã xây dựng trọn vẹn mô hình động học của robot delta:')

B([
    '**Động học ngược dạng đóng** giải bằng phép thế Weierstrass, kèm tiêu chí chọn nhánh khuỷu '
    'ra ngoài dựa trên dấu đạo hàm — tiêu chí này chặt chẽ hơn cách chọn theo giới hạn khớp, vốn '
    'không quyết định được ở những điểm mà cả hai nghiệm đều hợp lệ.',
    '**Động học thuận** bằng phép giao ba mặt cầu, với quy tắc chọn nghiệm có cao độ nhỏ hơn.',
    '**Vùng làm việc** xác định bằng quét số, cho thấy bán kính với tới giảm hơn một nửa khi hạ '
    'từ tư thế gốc xuống mặt bàn.',
    '**Quy hoạch quỹ đạo** biên dạng bậc năm với quỹ đạo an toàn ba đoạn và cơ chế kiểm tra toàn '
    'tuyến trước khi chuyển động.',
])

P('Độ chính xác đã được kiểm chứng ở ba mức độc lập, trong đó phép thử mạnh nhất là vòng lặp động '
  'học ngược–thuận trên 5 424 điểm với sai lệch cỡ sai số làm tròn của máy tính.')

P('Chương tiếp theo xây dựng môi trường mô phỏng và cơ cấu tương tác với vật thể, trên nền mô '
  'hình động học vừa thiết lập.')


S.save()
