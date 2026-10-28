#!/usr/bin/env python3
"""
Dựng khóa luận bản 3 — cấu trúc BỐN CHƯƠNG theo yêu cầu của giảng viên hướng dẫn.

    python3 docs/tools/build_thesis_v3.py

Khác bản 2 ở khung chứ không ở nội dung: bản 2 có sáu chương, mỗi chương chia nhỏ theo mạch kể
chuyện; bản này gom lại thành bốn chương, mỗi chương ĐÚNG bốn mục, mỗi mục nhiều nhất bốn tiểu mục.
Khung này lấy theo khóa luận mẫu (`docs/BachelorThesis_HaiNN.pdf`).

Việc gom lại không làm nhạt phần thị giác — nó vẫn là phần dài nhất, nhưng trải qua bốn chỗ thay vì
dồn vào một chương: lý thuyết ở 2.3–2.4, cài đặt ở 3.2, kết quả ở 4.1, và quá trình giảm sai số ở
4.2. Cách chia này theo đúng chức năng của từng chương, nên người đọc tìm thông tin theo loại chứ
không phải theo thứ tự thời gian làm việc.

Bìa, phụ bìa, tóm tắt và Mở đầu KHÔNG sinh ở đây — người làm đồ án tự viết.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import omml as m                                                   # noqa: E402
import thesis_style as S                                           # noqa: E402
from thesis_style import B, EQ, H1, H2, H3, IMG, N, P, T           # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Khoa_luan_v3.docx')

FIGURES = [
    ('1.1', 'So sánh cấu trúc robot nối tiếp và robot song song',
     'kl_noi_tiep_vs_song_song.png', 15.5),
    ('1.2', 'Cấu trúc robot delta ba bậc tự do và tên gọi các bộ phận',
     'kl_cau_truc_delta.png', 14.5),
    ('1.3', 'Luồng thông tin của vòng điều khiển khép kín hai chiều',
     'kl456_vong_kin.png', 15.5),
    ('1.4', 'Kiến trúc tổng thể của hệ thống', 'system_architecture.png', 15.5),
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
    ('2.8', 'Quỹ đạo an toàn ba đoạn so với đường đi thẳng', 'kl_quy_dao_an_toan.png', 14.5),
    ('2.9', 'Từ điểm ảnh về tọa độ ba chiều bằng phép giao tia với mặt phẳng đã biết cao độ',
     'kl34_mo_hinh_camera.png', 15.0),
    ('2.10', 'Sáu điểm mốc ArUco dùng cho hiệu chuẩn ngoại tham số',
     'calibration_markers.png', 14.0),
    ('2.11', 'Vì sao phải khớp mép trên khi mặt bàn phản chiếu', 'kl34_khop_mep.png', 15.0),
    ('3.1', 'Mô hình URDF chỉ mô tả được cấu trúc cây; mạch kín được đóng lúc chạy',
     'kl34_mach_kin.png', 15.5),
    ('3.2', 'Bố trí cảnh mô phỏng nhìn từ trên xuống', 'kl34_bo_tri_canh.png', 13.5),
    ('3.3', 'Ba khay phân loại có nhãn tên loại, nhìn từ camera mô phỏng',
     'bin_labels.png', 14.0),
    ('3.4', 'Cửa sổ dung sai cho phép hút thành công', 'kl34_cua_so_hut.png', 13.5),
    ('3.5', 'So sánh mặt nạ thu được bằng ngưỡng màu cố định và bằng phép trừ ảnh nền',
     'foreground_comparison.png', 15.0),
    ('3.6', 'Kết quả nhận dạng trên camera thật', 'real_camera_detections.png', 15.0),
    ('3.7', 'Bốn lớp phát hiện kết quả không đáng tin', 'kl34_lop_phong_ve.png', 15.0),
    ('3.8', 'Đối chiếu vị trí vật thật và vật ảo', 'twin_coordinates.png', 14.5),
    ('3.9', 'Máy trạng thái của vòng băng tải và chỗ bàn giao quyền quyết định vị trí',
     'kl456_may_trang_thai.png', 16.0),
    ('3.10', 'Đồ thị các nút và chủ đề ROS 2 của hệ thống', 'ros_graph.png', 15.5),
    ('4.1', 'Phân bố sai số định vị trên mặt bàn trong mô phỏng', 'vision_error_map.png', 15.0),
    ('4.2', 'Bảy phép khắc phục sai số, đo trước và sau khi áp dụng',
     'kl456_giam_sai_so.png', 15.5),
    ('4.3', 'Độ bền của khâu nhận dạng với nhiễu cảm biến và với mức sáng',
     'vision_robustness.png', 15.0),
]
TABLES = [
    ('1.1', 'So sánh đặc tính của robot nối tiếp và robot song song'),
    ('1.2', 'Ba mức tích hợp giữa đối tượng thật và mô hình số theo Kritzinger'),
    ('1.3', 'Mục tiêu và chỉ tiêu định lượng của đề tài'),
    ('2.1', 'Thông số hình học của robot, trích từ mô hình URDF'),
    ('2.2', 'Ký hiệu dùng trong chương'),
    ('2.3', 'Bán kính vùng làm việc theo cao độ'),
    ('2.4', 'Kết quả hiệu chuẩn camera'),
    ('2.5', 'Đặc trưng hình học dùng để khớp hình bóng theo từng tình huống'),
    ('3.1', 'Cấu trúc động học của một chân trong mô hình mô phỏng'),
    ('3.2', 'Hai nguyên nhân quá tải tính toán và cách khắc phục'),
    ('3.3', 'Quy đổi kích thước giữa thế giới thật và mô hình số với hệ số tỉ lệ k = 3'),
    ('3.4', 'Dung sai của cơ cấu hút'),
    ('3.5', 'Ngưỡng phân lớp màu trong không gian HSV'),
    ('3.6', 'Hai kiểu hỏng ngược nhau của ngưỡng cố định'),
    ('3.7', 'So sánh hai phương pháp tách vật trên cùng một khung hình camera thật'),
    ('3.8', 'Bốn lớp phát hiện kết quả không đáng tin'),
    ('3.9', 'Thông số đo được của băng tải'),
    ('3.10', 'Các mô-đun phần mềm và số lượng kiểm thử tự động'),
    ('4.1', 'Sai số định vị của hệ thống thị giác'),
    ('4.2', 'Kết quả kiểm chứng động học'),
    ('4.3', 'Bảy phép khắc phục sai số chính, đo trước và sau'),
    ('4.4', 'Quá trình hiệu chỉnh cờ tin cậy'),
    ('4.5', 'Những hướng đã thử và bị bác bỏ'),
    ('4.6', 'Kết quả thử nghiệm gắp–thả tự động'),
    ('4.7', 'Kiểm chứng bản sao số và hai lớp phòng vệ'),
    ('4.8', 'Độ bền của khâu nhận dạng'),
    ('4.9', 'Đối chiếu mục tiêu đề ra và kết quả đạt được'),
    ('4.10', 'Giới hạn đã biết của hệ thống'),
]
S.configure(OUT, FIGURES, TABLES)

v, nn, fnc, o, sq = m.v, m.n, m.fn, m.op, m.seq
sb, sp, fr, dl, mx, sqr, txt = m.sub, m.sup, m.frac, m.delim, m.matrix, m.sqrt, m.txt
TH, PH = 'θ', 'φ'


# ================================================================== CHƯƠNG 1
H1('CHƯƠNG 1. TỔNG QUAN', page_break=False)

P('Chương này trình bày bối cảnh của đề tài theo ba mạch — cơ cấu robot được điều khiển, vai trò '
  'của thị giác máy tính trong điều khiển robot, và khái niệm bản sao số — rồi từ đó xác định mục '
  'tiêu và phạm vi.')

H2('1.1. Robot song song và robot delta')

H3('1.1.1. Hai nhóm cấu trúc')

P('Theo cách nối các khâu, robot công nghiệp chia thành hai nhóm lớn. **Robot nối tiếp** có các '
  'khâu nối đuôi nhau thành một chuỗi hở, giống cánh tay người: mỗi khớp mang theo toàn bộ phần '
  'còn lại của cánh tay. **Robot song song** có khâu cuối được nhiều chuỗi động học cùng nối tới '
  'đế, tạo thành mạch kín.')

IMG('1.1')

P('Sự khác nhau về cấu trúc kéo theo khác nhau về đặc tính. Ở robot nối tiếp, động cơ của khớp '
  'gần đế phải mang cả khối lượng các khâu phía sau, nên quán tính lớn và sai số của từng khớp '
  '**cộng dồn** ra khâu cuối. Ở robot song song, động cơ thường đặt cố định trên đế và tải được '
  'chia cho nhiều chuỗi, nên quán tính nhỏ và sai số các chuỗi có xu hướng **triệt tiêu** lẫn nhau.')

T('1.1', ['Đặc tính', 'Robot nối tiếp', 'Robot song song'],
  [
      ('Vị trí động cơ', 'phân tán trên các khâu', 'cố định trên đế'),
      ('Quán tính của phần chuyển động', 'lớn', 'nhỏ'),
      ('Sai số các khớp', 'cộng dồn ra khâu cuối', 'có xu hướng triệt tiêu'),
      ('Vùng làm việc', 'rộng', 'hẹp hơn'),
      ('Độ cứng vững', 'thấp hơn', 'cao'),
      ('Động học thuận', 'dễ (dạng đóng)', 'khó (thường phải giải lặp)'),
      ('Động học ngược', 'khó hơn', 'dễ (dạng đóng)'),
  ],
  widths=[5.6, 5.2, 5.2])

P('Hai dòng cuối của Bảng 1.1 cho thấy một đặc điểm đáng chú ý: **quan hệ giữa hai bài toán động '
  'học bị đảo ngược** giữa hai nhóm. Với robot song song, bài toán thường dùng nhất khi điều khiển '
  '— từ vị trí mong muốn tính ra góc khớp — lại là bài toán dễ hơn.')

H3('1.1.2. Robot delta')

P('Robot delta do Reymond Clavel đề xuất năm 1985 và được cấp bằng sáng chế năm 1990 [3] là cơ '
  'cấu song song được dùng rộng rãi nhất trong công nghiệp đóng gói và phân loại. Đặc điểm cốt '
  'lõi: ba chuỗi động học giống hệt nhau, mỗi chuỗi gồm một cánh tay chủ động và một thanh chống '
  'dạng hình bình hành.')

IMG('1.2')

P('Chính cấu trúc hình bình hành tạo ra tính chất đặc trưng: **bàn máy luôn song song với đế**, '
  'không quay. Robot vì vậy có đúng ba bậc tự do tịnh tiến, đủ cho thao tác gắp–thả mà không cần '
  'điều khiển hướng. Nhờ quán tính nhỏ, robot delta đạt gia tốc rất cao — các mẫu công nghiệp làm '
  'được trên 100 thao tác gắp–thả mỗi phút.')

P('Robot dùng trong đề tài là **delta dạng quay** (ba khớp chủ động là khớp quay), không phải dạng '
  'tịnh tiến. Thông số hình học cụ thể trình bày ở Chương 2.')

H2('1.2. Thị giác máy tính trong điều khiển robot')

H3('1.2.1. Vì sao cần thị giác')

P('Một robot chỉ biết góc khớp của chính nó thì chỉ lặp lại được một chuỗi động tác đã lập trình '
  'sẵn. Nó không biết vật ở đâu, không biết vật có còn ở đó không, và không phát hiện được khi '
  'thao tác thất bại. Thị giác máy tính cung cấp thông tin về **thế giới bên ngoài**, biến robot '
  'từ một cơ cấu lặp lại thành một hệ thống phản ứng với môi trường.')

P('Trong dây chuyền thật, điều này cho phép vật thể tới ở vị trí bất kỳ thay vì phải được định vị '
  'bằng đồ gá cơ khí — vốn đắt, kém linh hoạt và phải làm lại khi đổi sản phẩm.')

H3('1.2.2. Các cách bố trí camera')

P('Có hai cách gắn camera. **Camera trên tay** (*eye-in-hand*) gắn vào khâu cuối, nhìn gần nên độ '
  'phân giải cao, nhưng ảnh thay đổi theo mỗi chuyển động của robot. **Camera cố định** '
  '(*eye-to-hand*) đặt ngoài, nhìn toàn cảnh, nên quan sát được cả vật lẫn robot và không bị rung '
  'theo robot.')

P('Đề tài dùng **camera cố định** vì bài toán là định vị vật trên một mặt phẳng đã biết, và vì '
  'robot chỉ tồn tại trong mô phỏng nên không thể gắn camera lên nó.')

H3('1.2.3. Bài toán định vị từ camera đơn')

P('Phép chiếu phối cảnh làm mất một chiều: mọi điểm nằm trên cùng một tia nhìn đều cho cùng một '
  'điểm ảnh. Một camera đơn vì vậy **không đủ** để xác định vị trí ba chiều, trừ khi có thêm ràng '
  'buộc. Các ràng buộc thường dùng: camera kép (ảnh nổi), cảm biến chiều sâu, hoặc giả thiết hình '
  'học về cảnh.')

P('Đề tài dùng ràng buộc hình học — **vật đứng trên mặt phẳng đã biết cao độ** — vì nó không cần '
  'thêm thiết bị và đúng với mọi bài toán gắp vật đặt trên bàn hoặc trên băng tải. Cơ sở toán học '
  'trình bày ở mục 2.3.')

H2('1.3. Bản sao số')

H3('1.3.1. Ba mức tích hợp')

P('Quan hệ giữa một đối tượng vật lý và mô hình số của nó được Kritzinger và cộng sự [8] phân '
  'thành ba mức, phân biệt bởi **chiều và mức tự động của luồng thông tin**:')

T('1.2', ['Mức', 'Luồng thông tin', 'Ví dụ'],
  [
      ('Mô hình số (*digital model*)', 'không tự động, cập nhật thủ công',
       'bản vẽ CAD của một dây chuyền'),
      ('Bóng số (*digital shadow*)', 'tự động, **một chiều** thật → số',
       'cảm biến ghi trạng thái máy lên màn hình giám sát'),
      ('Bản sao số (*digital twin*)', 'tự động, **hai chiều**',
       'mô hình số nhận trạng thái máy và ra lệnh ngược lại cho máy'),
  ],
  widths=[4.6, 5.4, 6.0])

P('Phân biệt này không mang tính hình thức: nó cho biết **điều gì còn thiếu** để một hệ thống đạt '
  'mức cao hơn. Rất nhiều hệ thống được gọi là "bản sao số" thực ra chỉ dừng ở mức bóng số, vì '
  'thông tin chỉ đi một chiều.')

H3('1.3.2. Bản sao số trong đề tài')

P('Đề tài xây dựng hệ thống trong đó robot tồn tại **trong mô phỏng** còn vật thể là **thật**. '
  'Camera quan sát vật thật, kết quả định vị được ghi vào mô phỏng để vật ảo luôn nằm đúng chỗ vật '
  'thật — đó là chiều thuận, tức mức bóng số.')

IMG('1.3')

P('Chiều ngược được đóng lại bằng một **băng tải thật**: mô phỏng quyết định khi nào vật đã tới '
  'điểm gắp và ra lệnh dừng băng. Khi đó thông tin đi cả hai chiều và hệ thống đạt mức bản sao số '
  'đầy đủ.')

IMG('1.4')

H2('1.4. Mục tiêu và phạm vi đề tài')

H3('1.4.1. Mục tiêu')

P('Mục tiêu tổng quát: **dùng tín hiệu từ camera thật để điều khiển robot delta trong môi trường '
  'mô phỏng**, thực hiện thao tác nhận dạng, định vị và phân loại vật thể.')

T('1.3', ['Mục tiêu cụ thể', 'Chỉ tiêu định lượng'],
  [
      ('Xây dựng mô hình động học robot delta', 'sai lệch vòng lặp ngược–thuận dưới 1 µm'),
      ('Mô phỏng robot tương tác vật lý với vật thể',
       'thao tác gắp–thả bị ràng buộc bởi va chạm, không phải phép gán tọa độ'),
      ('Nhận dạng và định vị vật bằng camera đơn',
       'sai số nhỏ hơn dung sai của cơ cấu hút (12 mm trong hệ mô phỏng)'),
      ('Đánh giá mức độ tin cậy của từng kết quả',
       'ước lượng được chấp nhận phải nằm trong dung sai'),
      ('Thực hiện gắp–thả tự động dựa trên thị giác',
       'tỉ lệ thành công tương đương khi dùng vị trí lý tưởng'),
      ('Đóng vòng điều khiển hai chiều', 'mô phỏng điều khiển được một thiết bị thật'),
  ],
  widths=[7.0, 9.0])

H3('1.4.2. Phạm vi')

P('Đề tài giới hạn trong các điều kiện sau:')

B([
    'Vật thể là **lon nước ngọt** hình trụ, ba loại phân biệt bằng màu; mỗi màu ứng với đúng một '
    'vật trong cảnh.',
    'Vật **đứng trên mặt phẳng đã biết cao độ** — mặt bàn hoặc mặt băng tải.',
    'Camera **cố định**, đã hiệu chuẩn, nhìn chếch xuống mặt bàn.',
    'Robot chỉ tồn tại trong mô phỏng; thiết bị thật duy nhất được điều khiển là băng tải.',
    'Thế giới thật và mô hình số liên hệ qua một **hệ số tỉ lệ** k = 3, vì lý do trình bày ở '
    'mục 3.1.',
])

H3('1.4.3. Bố cục khóa luận')

P('**Chương 2** xây dựng cơ sở lý thuyết: động học robot delta, quy hoạch quỹ đạo, mô hình camera '
  'và phương pháp ước lượng vị trí vật thể từ ảnh. **Chương 3** trình bày việc xây dựng hệ thống: '
  'môi trường mô phỏng, khâu thị giác, bản sao số kèm băng tải, và kiến trúc phần mềm. **Chương 4** '
  'trình bày kết quả đo đạc, quá trình giảm sai số, các thử nghiệm đầu-cuối và đánh giá chung.')


# ================================================================== CHƯƠNG 2
H1('CHƯƠNG 2. CƠ SỞ LÝ THUYẾT')

P('Chương này xây dựng bốn khối lý thuyết mà hệ thống dựa vào: động học của cơ cấu, cách sinh quỹ '
  'đạo chuyển động, mô hình camera cùng phép hiệu chuẩn, và phương pháp suy ra vị trí vật thể từ '
  'một ảnh phẳng.')

P('Hai khối đầu thuộc về điều khiển robot và có lời giải dạng đóng. Hai khối sau thuộc về thị giác '
  'máy tính và phải giải bằng phương pháp số — đây cũng là phần chiếm trọng tâm của đề tài.')

H2('2.1. Động học robot delta')

H3('2.1.1. Thông số hình học và hệ trục tọa độ')

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

H3('2.1.2. Động học ngược')

P('Bài toán động học ngược: cho trước vị trí mong muốn của tâm bàn máy, tìm ba góc khớp đưa robot '
  'tới vị trí đó. Đây là bài toán hệ điều khiển phải giải ở mỗi chu kỳ, nên cần lời giải **dạng '
  'đóng**, tính được trong thời gian xác định, thay vì lặp số.')

P('**Quy bài toán về mặt phẳng.**')

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

P('**Phương trình ràng buộc.**')

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

P('**Giải bằng phép thế Weierstrass.**')

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

P('**Chọn nghiệm — hai nhánh khuỷu.**')

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

P('**Kiểm chứng bằng tư thế gốc.**')

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

H3('2.1.3. Động học thuận')

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

H3('2.1.4. Vùng làm việc')

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

H2('2.2. Quy hoạch quỹ đạo')

P('Giải được động học ngược mới chỉ cho phép đưa robot tới một điểm. Muốn robot di chuyển trơn '
  'tru cần sinh ra **chuỗi điểm trung gian** theo thời gian, sao cho vận tốc và gia tốc liên tục.')

H3('2.2.1. Biên dạng bậc năm')

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

H3('2.2.2. Quỹ đạo an toàn ba đoạn')

P('Đi thẳng từ điểm này sang điểm khác ở cao độ thấp sẽ quét ngang qua các vật đang đứng trên '
  'bàn. Quỹ đạo an toàn chia chuyển động thành ba đoạn: **nâng** thẳng đứng lên cao độ an toàn, '
  '**đi ngang** ở cao độ đó, rồi **hạ** thẳng đứng xuống đích (Hình 2.8).')

IMG('2.8')

P('Toàn bộ chuỗi điểm của cả ba đoạn được **giải động học ngược trước khi robot bắt đầu chuyển '
  'động**. Nếu có bất kỳ điểm trung gian nào nằm ngoài vùng làm việc, lệnh bị từ chối ngay và '
  'robot không nhúc nhích. Cách này quan trọng vì điểm đầu và điểm cuối có thể đều hợp lệ trong '
  'khi một điểm giữa đường lại không — kiểm tra hai đầu là không đủ.')



H3('2.2.3. Kiểm tra toàn tuyến trước khi chuyển động')

P('Toàn bộ quỹ đạo được giải động học ngược **trước khi** robot bắt đầu đi. Nếu có bất kỳ điểm nào '
  'ngoài vùng làm việc, hệ thống báo lỗi và robot chưa hề di chuyển.')

P('Cách làm này quan trọng hơn vẻ ngoài. Một điểm nằm ngoài vùng làm việc ở **giữa** đường đi sẽ '
  'không bị phát hiện nếu chỉ kiểm tra điểm đầu và điểm cuối; khi đó robot dừng giữa chừng ở tư thế '
  'bất kỳ, có thể đang mang vật, và việc phục hồi khó hơn nhiều so với việc từ chối ngay từ đầu.')

H2('2.3. Mô hình camera và hiệu chuẩn')

H3('2.3.1. Mô hình lỗ kim')

P('Camera được mô hình hóa theo mô hình lỗ kim. Một điểm trong không gian, biểu diễn trong hệ tọa '
  'độ robot, trước hết được đưa về hệ tọa độ camera bằng phép biến đổi cứng:')

EQ(sq(sb(v('X'), v('c')), o('='), v('R'), sb(v('X'), v('r')), o('+'), v('t')), '2.17')

P('rồi chiếu lên mặt phẳng ảnh bằng ma trận nội tham số **K**:')

EQ(sq(v('s'), mx([[v('u')], [v('v')], [nn(1)]]), o('='), v('K'), sb(v('X'), v('c')),
      o(','), txt('   '), v('K'), o('='),
      mx([[sb(v('f'), v('x')), nn(0), sb(v('c'), v('x'))],
          [nn(0), sb(v('f'), v('y')), sb(v('c'), v('y'))],
          [nn(0), nn(0), nn(1)]])), '2.18')

P('Trong đó **R**, **t** là **ngoại tham số** — tư thế camera so với robot; **K** là **nội tham '
  'số** — tiêu cự và tâm ảnh của riêng thiết bị. Hệ số **s** là độ sâu, và chính nó là nguồn gốc '
  'của khó khăn nêu ở mục 1.2.3: phép chiếu làm mất một chiều.')

H3('2.3.2. Ràng buộc mặt phẳng và phép giao tia')

IMG('2.9')

P('Ràng buộc dùng trong đề tài: **vật đứng trên mặt phẳng đã biết cao độ**. Khi đó tâm vật nằm ở '
  'cao độ bằng cao độ mặt đỡ cộng nửa chiều cao vật, và tọa độ ngang tìm được bằng cách giao tia '
  'nhìn với mặt phẳng đó:')

EQ(sq(sb(v('X'), v('r')), o('='), sp(v('R'), txt('T')),
      dl(sq(v('λ'), sp(v('K'), txt('−1')), mx([[v('u')], [v('v')], [nn(1)]]), o('−'), v('t'))),
      o(','), txt('   '), v('λ'), txt(' sao cho '), sb(v('z'), v('r')), o('='),
      sb(v('z'), txt('đỡ')), o('+'), fr(v('h'), nn(2))), '2.19')

P('Khi cảnh có **nhiều mặt đỡ** ở các cao độ khác nhau — mặt bàn và mặt băng tải — hệ thống xét '
  'từng giả thiết rồi chọn giả thiết **tự nhất quán**: giả thiết "vật đứng trên băng" chỉ được '
  'chấp nhận nếu vị trí suy ra từ chính nó rơi đúng vào phạm vi mặt băng. Đây là một dạng kiểm tra '
  'tính nhất quán nội tại — một giả thiết chỉ được nhận khi kết luận của nó không mâu thuẫn với '
  'tiền đề của nó.')

P('Chọn sai mặt đỡ gây sai số rất lớn, lớn hơn trực giác nhiều: với camera nhìn chúc 46°, sai '
  '50 mm cao độ làm vị trí ngang lệch **76 mm** (số liệu đo ở mục 4.2).')

H3('2.3.3. Hiệu chuẩn nội tham số')

P('Nội tham số gắn với **thiết bị cụ thể** — hai camera cùng kiểu vẫn khác nhau — nhưng không đổi '
  'khi di chuyển camera, nên chỉ cần đo **một lần cho mỗi máy**. Phương pháp dùng bàn cờ phẳng '
  'chụp ở nhiều tư thế; bài toán quy về cực tiểu hóa sai số chiếu lại.')

P('Camera dùng trong đề tài là loại **lấy nét cố định**. Đây là ưu điểm chứ không phải hạn chế: '
  'tiêu cự không thể trôi sau khi hiệu chuẩn, nên kết quả có giá trị lâu dài.')

H3('2.3.4. Hiệu chuẩn ngoại tham số và quy ước tỉ lệ')

P('Ngoại tham số là tư thế camera so với robot, xác định bằng sáu điểm mốc ArUco dán trên mặt bàn '
  'tại các tọa độ đã biết. Bài toán tìm tư thế từ các cặp điểm–ảnh là bài toán **PnP** '
  '(*Perspective-n-Point*).')

IMG('2.10')

P('Hai chi tiết kỹ thuật đáng nêu, và điều quan trọng là **cả hai chỉ lộ ra trên ảnh thật** — với '
  'dữ liệu tổng hợp thì mọi cách làm đều cho kết quả đúng:')

N([
    '**Cách lấy tâm điểm mốc.** Lấy trung bình bốn góc cho kết quả lệch khi nhìn xiên, vì phép '
    'chiếu phối cảnh **không bảo toàn trung điểm**. Phải lấy **giao điểm hai đường chéo** — đại '
    'lượng mà phép chiếu phối cảnh có bảo toàn.',
    '**Thuật toán giải PnP.** Một thuật toán chuyên dùng cho điểm mốc đồng phẳng cho nghiệm sai '
    'hẳn trên ảnh thật (sai số chiếu lại 434 điểm ảnh) dù vẫn đúng với điểm tổng hợp. Phải thay '
    'bằng thuật toán tổng quát kèm bước tinh chỉnh phi tuyến.',
])

T('2.4', ['Đại lượng', 'Camera mô phỏng', 'Camera thật'],
  [
      ('Độ phân giải', '640 × 480', '1280 × 720'),
      ('Góc chúc', '32°', '46,1°'),
      ('Sai số chiếu lại khi hiệu chuẩn', '0,14 điểm ảnh', '0,222 điểm ảnh'),
      ('Sai lệch vị trí camera so với giá trị thật', '0,35 mm', '—'),
      ('Sai số ngoại tham số quy ra hệ mô phỏng', '—', '0,93 mm'),
      ('Nhiễu cảm biến (độ lệch chuẩn)', 'không có tác dụng', '2,2 mức xám'),
  ],
  widths=[6.4, 4.8, 4.8])

P('**Quy ước tỉ lệ.** Thế giới thật và mô hình số liên hệ qua hệ số k = 3 (lý do ở mục 3.1). Câu '
  'hỏi thiết kế là áp dụng phép chia này ở đâu. Lựa chọn của đề tài là đưa **tọa độ của mô hình '
  'số** vào bài toán PnP **ngay từ khâu hiệu chuẩn**, thay vì hiệu chuẩn theo milimét thật rồi '
  'chia kết quả về sau.')

P('Cơ sở: thu nhỏ toàn bộ thế giới k lần chỉ làm **vectơ tịnh tiến của camera chia cho k**; ma '
  'trận nội tham số, hệ số méo và bản thân phép chiếu đều **không đổi**. Nhờ vậy toàn bộ khối thị '
  'giác phía sau chạy nguyên trong hệ tọa độ mô phỏng mà **không phải sửa một dòng nào** khi '
  'chuyển từ camera mô phỏng sang camera thật.')

H2('2.4. Ước lượng vị trí vật thể từ ảnh')

H3('2.4.1. Tâm khối và sai sót hệ thống của nó')

P('Cách đơn giản nhất để suy ra vị trí là lấy **tâm khối** của vùng ảnh thuộc về vật rồi giao tia. '
  'Cách này có một sai sót **hệ thống**: tâm khối là tâm của **phần nhìn thấy**, không phải hình '
  'chiếu của tâm vật.')

P('Với vật không bị che và có kích thước cân đối thì hai điểm này gần trùng nhau. Nhưng khi vật bị '
  'che một phần — bởi thành khay, bởi vật khác, hay bởi chính robot — tâm khối dịch theo **hướng '
  'nhìn**, và sai lệch tăng theo mức độ che. Đo trên bộ dữ liệu đánh giá: vật nằm trong khay bị '
  'thành khay che nửa dưới cho sai số trung bình **13,4 mm**, vượt dung sai của cơ cấu hút.')

H3('2.4.2. Khớp hình bóng')

P('Phương pháp dùng trong đề tài là **khớp hình bóng**. Từ mô hình hình học của vật — hình trụ, '
  'hộp hay cầu, kèm kích thước — và mô hình camera, dựng **hình bóng dự đoán**, tức bao lồi của '
  'ảnh các điểm trên bề mặt vật. Sau đó tìm vị trí (x, y) sao cho một **đặc trưng hình học** của '
  'hình bóng dự đoán trùng với đặc trưng tương ứng đo được trên ảnh:')

EQ(sq(fnc('F'), dl(sq(v('x'), o(','), v('y'))), o('='),
      mx([[sq(sb(v('v'), txt('đo')), o('−'), sb(v('v'), txt('dự đoán')),
              dl(sq(v('x'), o(','), v('y'))))],
          [sq(sb(v('u'), txt('đo')), o('−'), sb(v('u'), txt('dự đoán')),
              dl(sq(v('x'), o(','), v('y'))))]]), o('='), nn(0)), '2.20')

P('Hệ hai phương trình hai ẩn này giải bằng phương pháp Newton. Cao độ z không phải ẩn vì đã bị '
  'ràng buộc bởi giả thiết mặt đỡ (công thức 2.19).')

P('Điểm xuất phát của phép lặp có ảnh hưởng lớn hơn dự kiến. Xuất phát từ tâm khối — vốn bị kéo '
  'lệch bởi ảnh phản chiếu trên mặt bàn — làm bộ giải rơi vào nghiệm lạ: mọi vật đặt tại cùng một '
  'chỗ đều cho **cùng một đáp án sai**, bất kể đó là vật nào. Sự giống hệt nhau đó là dấu hiệu '
  'phân kỳ chứ không phải sai số đo, vì sai số đo thì phải tản mạn.')

H3('2.4.3. Chọn đặc trưng theo tình huống')

IMG('2.11')

T('2.5', ['Tình huống', 'Đặc trưng dùng', 'Vì sao'],
  [
      ('Vật trong khay', 'mép trên', 'thành khay che nửa dưới nên mép đáy vô nghĩa'),
      ('Vật trên bàn, mặt nạ theo màu', 'mép đáy',
       'thân vật có màu xuống tận đáy, và đáy tì trên mặt phẳng đã biết'),
      ('Vật trên bàn thật, mặt bàn phản chiếu', 'mép trên',
       'ảnh phản chiếu dính liền chân vật, luôn nằm phía dưới nên mép trên miễn nhiễm'),
  ],
  widths=[5.0, 3.4, 7.6])

P('Hai dòng cuối của Bảng 2.5 cho hai kết luận **trái ngược nhau về cùng một đặc trưng**, và đó '
  'không phải mâu thuẫn: ý nghĩa của mặt nạ khác nhau trong hai trường hợp. Với mặt nạ theo màu, '
  'mép trên là mép của **vùng màu** — bị nắp và vành nhãn làm nhòe. Với mặt nạ thu bằng phép trừ '
  'nền, mép trên là **vành miệng vật**, một đặc trưng hình học sạch.')

H3('2.4.4. Đánh giá độ tin cậy của kết quả')

P('Ngoài vị trí, hệ thống còn phải đưa ra **mức độ chắc chắn** của kết quả, vì lớp điều khiển cần '
  'biết khi nào không nên hành động. Đại lượng tự nhiên nhất là **tỉ lệ nhìn thấy**:')

EQ(sq(v('ρ'), o('='), fr(sb(v('A'), txt('đo được')), sb(v('A'), txt('hình bóng dự đoán')))), '2.21')

P('Vật không bị che cho ρ ≈ 1; vật bị che một phần cho ρ nhỏ hơn. Ngưỡng dưới của ρ vì vậy phát '
  'hiện được che khuất.')

P('Nhưng đại lượng này có một giới hạn **mang tính cấu trúc**, và việc nhận ra nó là bước ngoặt '
  'của cả phần thị giác: **ρ không thể phát hiện được vị trí sai.** Lý do là quy trình ước lượng '
  'xác định vị trí **trước**, rồi mới dựng hình bóng dự đoán **tại chính vị trí vừa tìm được**. '
  'Nếu vùng ảnh lớn hơn vật thật, phép khớp đẩy vật về gần camera hơn, và hình bóng dự đoán tại vị '
  'trí mới đó **cũng lớn hơn** — nên ρ **tự chuẩn hóa** về gần 1 dù vị trí sai hàng trăm milimét.')

P('Khắc phục bằng cách thêm những kiểm tra dùng **thông tin độc lập với phép khớp**. Phép khớp '
  '(công thức 2.20) chỉ ràng buộc mép trên và tâm ngang, nên **bề rộng** và **chiều cao** của '
  'khung bao là hai đại lượng mà nó không tự điều chỉnh cho khớp được. Cài đặt cụ thể của bốn lớp '
  'kiểm tra trình bày ở mục 3.2.4.')


# ================================================================== CHƯƠNG 3
H1('CHƯƠNG 3. XÂY DỰNG HỆ THỐNG')

P('Chương này trình bày việc hiện thực hóa các cơ sở lý thuyết ở Chương 2 thành một hệ thống chạy '
  'được: môi trường mô phỏng có tương tác vật lý, khâu thị giác, cơ chế bản sao số kèm băng tải, '
  'và kiến trúc phần mềm gắn kết chúng.')

H2('3.1. Môi trường mô phỏng')

H3('3.1.1. Mô hình hóa cơ cấu mạch kín')

P('Khó khăn đầu tiên nằm ở định dạng mô tả robot. URDF — định dạng chuẩn của ROS — chỉ biểu diễn '
  'được **cấu trúc cây**: mỗi khâu có đúng một khâu cha. Robot delta lại là cơ cấu **mạch kín**, '
  'trong đó bàn máy được ba chân cùng nối tới. Cấu trúc đó không tồn tại trong một cây.')

IMG('3.1')

P('Giải pháp là mô tả cơ cấu dưới dạng ba nhánh rời nhau, rồi **đóng mạch lúc chạy** bằng cơ chế '
  'hàn hai khâu của trình mô phỏng. Khi mô phỏng khởi động, ba mối hàn được tạo và cơ cấu trở '
  'thành mạch kín thật sự.')

T('3.1', ['Thành phần', 'Biểu diễn trong mô hình', 'Vai trò'],
  [
      ('Khớp chủ động', '1 khớp quay, có bộ điều khiển vị trí',
       'nhận lệnh góc; tương ứng động cơ thật'),
      ('Khớp cầu hai đầu thanh chống', 'mối hàn + chuỗi 3 khớp quay',
       'tái tạo 3 bậc tự do quay của khớp cầu'),
      ('Liên kết bàn máy', 'mối hàn tạo lúc chạy', 'đóng mạch kín'),
      ('Treo bàn máy', '3 khớp trượt bị động theo x, y, z',
       'giữ bàn máy luôn nằm ngang, đúng 3 bậc tự do tịnh tiến'),
  ],
  widths=[4.6, 6.0, 5.4])

P('Điều kiện bắt buộc là **hai khâu được hàn phải trùng khung tọa độ tại tư thế gốc**. Hệ quả rất '
  'quan trọng cho phần sau: **không thể tùy tiện đổi kích thước hình học của robot**, vì làm vậy '
  'sẽ phá các mối hàn ngay khi mô phỏng khởi động.')

H3('3.1.2. Hệ số tỉ lệ')

P('Vật thể thật dùng trong đề tài là lon nước ngọt, đường kính 57,5 mm và cao 147 mm. Vùng làm '
  'việc của robot chỉ cao khoảng 120 mm tính từ mặt bàn. Đặt một lon thật vào đó thì **đỉnh lon '
  'chạm trần vùng làm việc**: robot với tới được nhưng không nhấc lên được, và khay cũng không '
  'chứa nổi.')

P('Phóng to robot không phải lựa chọn, vì lý do nêu ở mục 3.1.1. Giải pháp là **thu nhỏ thế '
  'giới**: vật ảo giữ đúng tỉ lệ hình dạng của vật thật nhưng kích thước chia cho hệ số k = 3, và '
  'mọi tọa độ cũng vậy.')

T('3.3', ['Đại lượng', 'Thế giới thật', 'Mô hình số (chia cho k = 3)'],
  [
      ('Đường kính vật', '57,5 mm', '19,2 mm'),
      ('Chiều cao vật', '147 mm', '49,0 mm'),
      ('Chiều dài băng tải', '230 mm', '76,7 mm'),
      ('Chiều cao mặt băng so với bàn', '50 mm', '16,7 mm'),
      ('Dung sai cho phép của cơ cấu hút', '36 mm', '12 mm'),
  ],
  widths=[6.4, 4.8, 4.8])

P('Hệ số k = 3 không chọn tùy ý. Với k = 2,5, khi robot mang một vật đi **qua phía trên** một vật '
  'khác đang đứng thì đầu công tác phải ở cao độ −99,4 mm, vượt trần vùng làm việc; trong thực '
  'nghiệm điều này biểu hiện thành việc vật đang mang **đè vào** vật đang đứng và làm đổ nó.')

P('Một tính chất quan trọng: **phép tỉ lệ không làm sai số thị giác xấu đi**. Camera phủ vùng rộng '
  'gấp k lần nên số milimét ứng với một điểm ảnh tăng k lần, nhưng khi quy kết quả về không gian '
  'mô phỏng thì sai số lại chia cho k. Hai tác động triệt tiêu nhau.')

H3('3.1.3. Cảnh làm việc và cơ cấu gắp–thả')

IMG('3.2')

P('Toàn bộ tọa độ và kích thước của cảnh được khai báo tại **một vị trí duy nhất** trong mã nguồn; '
  'mọi thành phần khác đều đọc từ đó. Nguyên tắc này tỏ ra có giá trị trong thực nghiệm: khi băng '
  'tải thật lắp xong và phát hiện chạy ngược chiều dự kiến, dây động cơ đã hàn cố định nên không '
  'đảo cực được — việc xử lý chỉ là **đổi một con số** và toàn hệ thống đi theo.')

IMG('3.3')

P('Ba khay được dán nhãn tên loại ở mặt quay về phía camera. Chi tiết này có vai trò trình bày: '
  'nếu ba khay giống hệt nhau thì người xem không phân biệt được robot đang **phân loại** hay chỉ '
  'thả vật vào một ô trống bất kỳ. Nhãn dùng chữ trắng trên nền xám — không dùng màu của vật — vì '
  'khay có màu bão hòa sẽ bị chính khâu nhận dạng hiểu nhầm là vật.')

P('Cơ cấu hút chân không được mô phỏng bằng cùng cơ chế hàn hai khâu đã dùng để đóng mạch kín. Mối '
  'hàn **giữ nguyên vị trí tương đối tại thời điểm tạo**, nên vật đi theo robot đúng từng milimét '
  'mà không bị giật về tâm đầu hút — đúng hành vi của giác hút thật.')

IMG('3.4')

T('3.4', ['Điều kiện', 'Giá trị cho phép (hệ mô phỏng)', 'Tương đương thật'],
  [
      ('Lệch ngang giữa tâm đầu hút và tâm vật', '≤ 12 mm', '≤ 36 mm'),
      ('Khe giữa mặt dưới đầu hút và đỉnh vật', 'từ −4 mm đến +6 mm', 'từ −12 mm đến +18 mm'),
  ],
  widths=[7.6, 4.4, 4.0])

P('Giá trị **12 mm** trở thành chỉ tiêu thiết kế cho toàn bộ khâu thị giác: hệ thống thị giác chỉ '
  'có ích nếu sai số định vị của nó nhỏ hơn con số này.')

H3('3.1.4. Hiệu năng và hai lỗi tải tính toán')

P('Trong quá trình phát triển, hệ thống chạy chậm hơn thời gian thực đáng kể. Truy nguyên cho hai '
  'nguyên nhân, cả hai đều không nằm ở thuật toán mà ở **tần suất trao đổi dữ liệu**.')

T('3.2', ['Nguyên nhân', 'Biểu hiện', 'Cách khắc phục'],
  [
      ('Nút điều khiển đăng ký đồng hồ mô phỏng',
       'trình mô phỏng phát đồng hồ ở mỗi bước tính (≈ 2000 Hz); một nút Python chiếm 103 % một lõi',
       'chỉ bật đồng bộ đồng hồ cho nút thật sự cần; tải còn 21 %'),
      ('Trạng thái khớp phát ở tần số bước tính',
       'bộ phát không có tùy chọn giảm tần số; nút điều khiển chiếm 88 % một lõi',
       'chèn một nút giảm tần số xuống 100 Hz; tải còn 14 %'),
  ],
  widths=[4.4, 6.4, 5.2])

P('Hai lỗi này tiêu biểu cho một lớp vấn đề của hệ thống phân tán: **chi phí nằm ở chỗ truyền tin, '
  'không nằm ở chỗ tính toán**. Không có thuật toán nào được cải tiến; chỉ giảm số thông điệp phải '
  'xử lý. Sau khi khắc phục, hệ số thời gian thực tăng từ 0,56 lên 0,77–0,99.')

H2('3.2. Khâu thị giác')

H3('3.2.1. Tách vật thể khỏi nền')

P('Khâu đầu tiên của đường ống là xác định những vùng ảnh nào thuộc về vật. Đề tài đã dùng **hai '
  'phương pháp khác nhau cho hai thế giới**, và đây là một kết luận về bản chất bài toán chứ không '
  'phải một giải pháp chắp vá.')

P('**Phân ngưỡng theo màu.** Ảnh được chuyển sang không gian HSV rồi phân ngưỡng theo lớp màu. '
  'Không gian HSV tách riêng sắc màu khỏi độ sáng nên bền với bóng đổ hơn RGB.')

T('3.5', ['Lớp màu', 'Sắc màu H', 'Độ bão hòa S', 'Độ sáng V'],
  [
      ('Đỏ', '[0; 8] ∪ [172; 180]', '≥ 90', '≥ 40'),
      ('Lục', '[45; 85]', '≥ 90', '≥ 40'),
      ('Lam', '[95; 125]', '≥ 90', '≥ 40'),
  ],
  widths=[3.6, 5.6, 3.4, 3.4])

P('Lớp đỏ phải khai báo thành hai khoảng vì sắc màu là đại lượng tuần hoàn và màu đỏ nằm vắt qua '
  'điểm 0°. Ngưỡng độ sáng V ≥ 40 thoạt nhìn có vẻ thừa, nhưng với mặt bàn tối nó lại là ngưỡng '
  'quan trọng nhất: do định nghĩa S = (max − min)/max, mẫu số tiến về 0 ở vùng tối nên **điểm ảnh '
  'tối có độ bão hòa cao giả tạo** — đo trên ảnh thật, trong vùng V < 40 có tới 85 % điểm ảnh vượt '
  'ngưỡng bão hòa.')

P('**Vì sao ngưỡng cố định không bền.** Trên camera thật, bộ ngưỡng cố định thất bại theo hai kiểu '
  '**ngược nhau về cơ chế**, tùy điều kiện chiếu sáng.')

T('3.6', ['Điều kiện', 'Cơ chế hỏng', 'Hậu quả'],
  [
      ('Ban ngày, rèm mở', 'mặt bàn sáng lên và ám màu', 'mặt bàn lọt vào mặt nạ'),
      ('Thắp một đèn', 'mặt bàn quá tối, độ bão hòa hóa nhiễu',
       'gần như **cả mặt bàn** lọt vào'),
  ],
  widths=[4.0, 7.0, 5.0])

P('Vì hai kiểu hỏng ngược chiều nhau nên **không tồn tại bộ ngưỡng nào xử lý được cả hai**. Đã '
  'quét toàn dải phơi sáng và độ khuếch đại của camera, không cấu hình nào cứu được.')

P('**Trừ ảnh nền.** Giải pháp là so ảnh hiện tại với ảnh mặt bàn trống chụp trước đó. Đại lượng '
  'được so là **sự thay đổi**, không phải giá trị tuyệt đối, nên nó độc lập với mức sáng chung.')

IMG('3.5')

P('Trên cảnh không có vật nào: cách lấy ngưỡng báo **12,06 %** diện tích ảnh là "vật", phép trừ '
  'nền báo **0,00 %**, trong khi nhiễu cảm biến chỉ cỡ 1 mức xám so với ngưỡng 30.')

P('Cái giá phải trả là ảnh nền **gắn cứng với vị trí camera và điều kiện chiếu sáng**: camera xê '
  'dịch 8,7 điểm ảnh đã làm tỉ lệ nền trước vọt từ gần 0 lên 17 %. Nguy hiểm hơn, kiểu hỏng này '
  '**không báo lỗi**. Hệ thống vì vậy tự đối chiếu vị trí các điểm mốc hiện tại với vị trí của '
  'chúng trong chính ảnh nền và cảnh báo khi lệch quá 3 điểm ảnh.')

H3('3.2.2. Hai thế giới, hai bộ nhận dạng')

P('Phép trừ nền **không dùng được cho cảnh mô phỏng**: ở đó ba khay màu xám cũng "không phải mặt '
  'bàn", nên vật nằm trong khay dính liền với khay thành một vùng. Ngược lại, phân ngưỡng theo màu '
  '**không dùng được cho vật thật**, vì một lý do sâu hơn.')

P('Toàn bộ khâu ước lượng ngầm giả định **mặt nạ thu được chính là hình bóng của vật**. Giả định '
  'đó đúng với vật mô phỏng có thân một màu đặc, nhưng sai hẳn với lon thật: màu nằm thành vành, '
  'xen mảng trắng và logo lớn.')

T('3.7', ['Đại lượng đo trên cùng một khung hình', 'Theo màu', 'Trừ nền'],
  [
      ('Tỉ lệ cao/rộng của ba vật (vật thật: 2,56)', '2,28 / 1,88 / **0,93**',
       '2,45 / 2,26 / 2,65'),
      ('Diện tích ba vật (điểm ảnh)', '14 645 / 5 603 / 2 003', '28 449 / 22 261 / 22 240'),
      ('Nhiễu vị trí theo x (mm thật)', '3,4 / 5,9 / 13,8', '3,0 / 7,1 / 4,4'),
      ('Tỉ lệ nhìn thấy ρ', 'phải đoán bằng hằng số', '**0,99 ± 0,01**'),
      ('Cờ tin cậy', 'hai vật bị coi là bị che ở **mọi** khung', '**60/60 khung tin cậy**'),
  ],
  widths=[7.0, 4.6, 4.4])

P('Ba vật **cùng kích thước** mà nhận theo màu cho diện tích chênh nhau **bảy lần**, và một vật có '
  'tỉ lệ cao/rộng 0,93 trong khi vật thật là 2,56 — nghĩa là phép đo đang đo **thiết kế nhãn** chứ '
  'không đo vật. Còn ρ = 0,99 ± 0,01 nghĩa là hình bóng đo được khớp hình bóng dự đoán, nhờ đó cơ '
  'chế phát hiện che khuất lấy lại đúng định nghĩa ban đầu của nó (công thức 2.21).')

P('**Kết luận:** bản sao số cần giống nhau về **hình học**, còn khâu nhận dạng là bài toán riêng '
  'của từng thế giới. Đây cũng là câu trả lời cho băn khoăn "vật ảo trông không giống vật thật": '
  'nó không cần giống về bề ngoài, chỉ cần giống về hình học.')

IMG('3.6')

H3('3.2.3. Tách vùng khi hai vật chạm nhau')

P('Hai vật chạm nhau trong ảnh — chưa cần che nhau — bị gộp thành một vùng liên thông, nên chỉ '
  'được gán **một danh tính** và trượt mọi phép kiểm tra hình dáng. Hậu quả nặng hơn vẻ ngoài: '
  'vùng gộp **giành mất lớp màu**, nên vật thứ ba đứng riêng cũng biến mất theo.')

P('Cách xử lý gồm ba phần: giữ **mọi** vùng của mỗi màu rồi mới chọn, thay vì chốt ngay vùng lớn '
  'nhất; tách vùng đã trượt bằng cách gán phần không mang màu về hạt giống màu **gần nhất theo '
  'khoảng cách**; và chỉ đếm phần ảnh **phía trên chân vật dự đoán** để ảnh phản chiếu không được '
  'tính vào.')

P('Kết quả: vật đứng riêng lấy lại được, nhưng **hai vật chạm nhau vẫn bị từ chối** (ρ = 0,71–0,80 '
  'so với ngưỡng 0,90). Đã thử hạ ngưỡng và **bác bỏ**, vì ngưỡng đó bảo đảm tính chất "hễ báo tin '
  'cậy thì sai số trong dung sai gắp". Trường hợp này được ghi nhận thành **điều kiện vận hành**: '
  'đặt các vật cách nhau ít nhất một bề rộng vật.')

H3('3.2.4. Bốn lớp phát hiện kết quả không đáng tin')

IMG('3.7')

T('3.8', ['Lớp', 'Kiểm tra gì', 'Bắt được loại lỗi nào'],
  [
      ('Hình học', 'vị trí suy ra có nằm trong vùng đặt vật không',
       'dây điện, mép bàn, sàn nhà lọt vào khung hình'),
      ('Hình dáng', 'bề rộng và chiều cao khung bao so với hình bóng dự đoán',
       'bàn tay, mảnh logo bị tách rời, hai vật dính liền'),
      ('Tỉ lệ nhìn thấy', 'ρ nằm ngoài khoảng [0,90; 1,30]', 'vật bị che một phần'),
      ('Xác nhận nhiều khung', 'vị trí nhảy xa phải trụ lại 5 khung liên tiếp',
       'nhiễu thoáng qua, bàn tay lướt ngang'),
  ],
  widths=[3.4, 6.6, 6.0])

P('Bốn lớp này **không chồng lấn**: mỗi lớp bắt một loại lỗi mà lớp khác bỏ sót. Mục 2.4.4 đã giải '
  'thích vì sao lớp thứ ba không thể một mình đảm đương — nó tự chuẩn hóa trước vị trí sai.')

P('Lớp **hình dáng** khắc phục được vì nó dùng thông tin độc lập với phép khớp. Đo trên ảnh thật: '
  'ba vật lành lặn lệch +5 % / +13 % / +8 % bề rộng — đạt; một vùng rộng gấp 2,3 lần — loại; một '
  'mảnh vụn hẹp hơn 59 % — loại. Ngưỡng **chiều cao** phải **không đối xứng** (0,65 đến 1,60) vì '
  'ảnh phản chiếu nằm trong khung bao làm vật lành lặn cao hơn dự đoán 16–28 %.')

P('Lớp **xác nhận nhiều khung** dựa vào ràng buộc mà không phép khớp nào lách được: **vật không '
  'dịch chuyển 284 mm trong một phần mười giây**. Điểm tinh tế là bộ lọc phải chặn nhiễu mà không '
  'chặn nhầm chuyển động thật — kết quả kiểm chứng ở mục 4.3.')


H2('3.3. Bản sao số và băng tải')

H3('3.3.1. Đồng bộ vị trí vật thể')

P('Mối nối giữa hai thế giới mỏng hơn nhiều so với dự kiến ban đầu, và đó là kết quả của quyết '
  'định ở mục 2.3.4: khối thị giác **đã phát tọa độ trong hệ mô phỏng sẵn**, vì tọa độ ấy được đưa '
  'vào bài toán PnP ngay từ khâu hiệu chuẩn. Ở tầng tích hợp này chỉ còn một phép cộng cao độ đế '
  'robot — **không có phép đổi tỉ lệ nào**.')

IMG('3.8')

P('Nút đồng bộ **từ chối làm bốn việc**, và mỗi điều từ chối đều xuất phát từ một lỗi đã gặp:')

N([
    '**Bỏ qua vật có cờ tin cậy bằng 0.** Không có điều này thì mọi ước lượng xấu đều được ghi '
    'thẳng vào mô phỏng.',
    '**Chỉ ghi khi vật thật dịch quá 6 mm.** Dưới mức đó để bộ giải vật lý tự lo, thay vì ghi đè '
    'vị trí mười lần mỗi giây — ghi đè liên tục làm vật ảo không bao giờ được phép rơi, va chạm '
    'hay nằm yên theo quy luật vật lý.',
    '**Không đụng tới vật mà cơ cấu hút đang giữ.** Vật đang lơ lửng thì camera không đo được, vì '
    'nó giả định vật đứng trên mặt phẳng.',
    '**Không ghi một bước nhảy xa nếu chưa được xác nhận** qua năm khung liên tiếp.',
])

H3('3.3.2. Băng tải và chiều ngược của vòng điều khiển')

P('Băng tải được thêm vào với hai lý do. Thứ nhất, nó làm kịch bản giống dây chuyền sản xuất thật '
  'hơn là dùng tay dời vật. Thứ hai — và quan trọng hơn về mặt học thuật — nó cho **mô phỏng ra '
  'lệnh cho một thiết bị thật**, đưa hệ thống từ mức *bóng số* lên mức *bản sao số* đầy đủ theo '
  'phân loại ở mục 1.3.1.')

T('3.9', ['Thông số băng tải', 'Giá trị đo được'],
  [
      ('Tốc độ (đã chạy hết khả năng động cơ)', '16 mm/s thật'),
      ('Quãng trôi sau khi ra lệnh dừng', '**3 mm**'),
      ('Điểm gắp, đo khi vật TỰ CHẠY tới', '+90,2 mm (so với +82,1 mm khi đặt bằng tay)'),
      ('Khoảng cách tối thiểu giữa hai vật', '80 mm thật (vừa 3 vật trên băng)'),
      ('Thời gian hết hạn lệnh chạy', '3 s'),
  ],
  widths=[8.0, 8.0])

P('Hai con số trong bảng dẫn tới quyết định thiết kế. **Quãng trôi chỉ 3 mm** đã bác bỏ một giả '
  'định ban đầu rằng cần một pha giảm tốc trước khi dừng để vật không đổ vì quán tính — ở tốc độ '
  '16 mm/s, quán tính không đáng kể. **Điểm gắp lệch 8 mm** giữa cách đo đặt tay và cách đo để vật '
  'tự chạy tới: số đo đặt tay mô tả một vị trí mà vật đang chạy **không bao giờ ở đó**.')

P('**Lưới an toàn.** Lệnh cho băng chạy được thiết kế không phải là công tắc bật-và-quên mà là một '
  '**lời khẳng định có hạn dùng**: máy tính phải nhắc lại lệnh ít nhất mỗi 3 giây, nếu không băng '
  'tự dừng. Nếu máy tính treo, cáp tuột hay phần mềm chết thì băng dừng theo. Một băng tải tiếp '
  'tục chạy vì phần mềm điều khiển đã chết là trạng thái không được phép tồn tại, và đây là cách '
  'rẻ nhất để loại bỏ nó — không cần nút dừng khẩn cấp, không cần cảm biến.')

H3('3.3.3. Máy trạng thái và bài toán bàn giao quyền')

IMG('3.9')

P('Năm trạng thái đầu là trình tự hiển nhiên. Trạng thái thứ sáu — **nhả quyền** — mới là chỗ khó '
  'duy nhất của cả vòng, và nó không hiện ra cho tới khi hệ thống chạy thật.')

P('Khi robot ảo đã gắp vật và bỏ vào khay, **vật thật vẫn còn nằm trên băng tải**. Bản sao số thì '
  'bám camera. Nếu không làm gì, nó sẽ kéo vật ảo từ trong khay về lại mặt băng — **mười lần mỗi '
  'giây** — tức là xóa sạch việc robot vừa làm, nhanh đúng bằng tốc độ robot làm.')

P('Cách giải: quyền quyết định vị trí vật **tạm chuyển sang mô phỏng** đúng lúc bắt đầu gắp, và '
  'chỉ **nhận lại khi thế giới thật đã đồng bộ** — tức khi tay người đã nhấc vật thật ra khỏi '
  'băng. Yêu cầu này ban đầu được diễn đạt là "tắt camera thực tế"; khi thực hiện thì chính xác '
  'hơn một chút, và sự khác biệt có ý nghĩa: **không tắt camera** — còn phải tiếp tục nhìn, vì '
  '**nhìn chính là cách biết được vật thật đã được nhấc đi hay chưa**. Thứ bị tạm ngừng là quyền '
  '*ghi* vị trí, không phải việc *quan sát*.')

P('Hai bất biến mà máy trạng thái bảo đảm: **không bao giờ có hai nguồn cùng ghi vị trí một vật**, '
  'và **không nhận vật mới khi vật vừa gắp chưa được dọn khỏi băng**. Ràng buộc thứ hai chỉ áp cho '
  'đúng vật đó chứ không áp cho cả mặt băng, nên đặt nhiều vật cùng lúc vẫn hợp lệ.')

H3('3.3.4. Robot bám theo vật trong hành trình')

P('Thay vì đứng chờ ở cuối băng, robot **đưa đầu hút lên trên nắp vật trước**, và băng chỉ chạy '
  'khi đầu hút đã vào vị trí; sau đó đầu hút **bám theo vật suốt hành trình**. Khi băng dừng thì '
  'hút được ngay, không mất thêm quãng đi.')

P('Bám đuổi đòi hỏi cơ chế điều khiển khác với đi tới một điểm: lập trọn quỹ đạo rồi chạy là đúng '
  'cho *"đi tới đó"* nhưng sai cho bám đuổi, vì đích đổi ngay trong lúc đang đi. Mỗi nhịp chỉ kéo '
  'vị trí lệnh về phía đích một đoạn có giới hạn, và chính giới hạn tốc độ đó tạo ra chuyển động '
  'mượt.')

H2('3.4. Phần mềm điều khiển')

H3('3.4.1. Kiến trúc phân tầng')

IMG('3.10')

P('Hệ thống được chia thành các nút ROS 2 trao đổi qua chủ đề và dịch vụ. Nguyên tắc tổ chức quan '
  'trọng nhất: **tách phần quyết định khỏi phần giao tiếp**. Phần lớn mã nghiệp vụ — động học, quỹ '
  'đạo, lập kế hoạch tác vụ, máy trạng thái, ước lượng thị giác — **không phụ thuộc ROS**.')

P('Đây không phải sở thích kiến trúc mà là điều kiện để kiểm thử: nhờ vậy 206 trường hợp kiểm thử '
  'chạy trong khoảng 3 giây mà **không cần mô phỏng, camera hay robot**. Nó cũng giúp phân biệt '
  'hai loại lỗi rất khác nhau — hỏng ở tầng giao tiếp là **hỏng dây nối**, hỏng ở tầng quyết định '
  'là **hỏng suy luận**.')

T('3.10', ['Mô-đun', 'Trách nhiệm', 'Số kiểm thử'],
  [
      ('Lập kế hoạch tác vụ', 'lệnh cấp cao → chuỗi thao tác, kiểm tra tầm với', '40'),
      ('Máy trạng thái băng tải', 'vòng làm việc, bàn giao quyền, nhiều vật', '34'),
      ('Quy hoạch quỹ đạo', 'biên dạng bậc năm, quỹ đạo an toàn', '14'),
      ('Nhận dạng theo màu', 'phân ngưỡng HSV, gộp mảnh', '12'),
      ('Thực thi tác vụ', 'chạy kế hoạch, kiểm chứng bằng đo đạc', '11'),
      ('Mô hình camera', 'phép chiếu, hiệu chuẩn PnP', '10'),
      ('Động học', 'thuận, ngược, chọn nhánh, tầm với', '9'),
      ('Cơ cấu hút', 'cửa sổ dung sai', '9'),
      ('Các mô-đun còn lại', 'tách nền, tư thế camera, ước lượng, đánh giá', '24'),
  ],
  widths=[5.0, 8.0, 3.0])

H3('3.4.2. Lớp điều khiển tác vụ')

P('Lớp này nhận lệnh dạng tác vụ — "chuyển vật này vào khay", "phân loại tất cả" — và tách thành '
  'hai phần có trách nhiệm khác hẳn nhau:')

B([
    '**Bộ lập kế hoạch** — thuần toán: đổi lệnh cấp cao thành chuỗi thao tác di chuyển, hút, nhả; '
    'tính điểm chạm và điểm thả; kiểm tra **toàn bộ** các đích bằng động học ngược **trước khi** '
    'robot chuyển động.',
    '**Bộ thực thi** — chạy kế hoạch và **kiểm chứng bằng đo đạc**: sau khi hút, vật phải được '
    'nhấc lên ít nhất 10 mm; sau khi thả, vật phải thật sự nằm trong khay.',
])

P('Nguyên tắc **kiểm chứng bằng đo đạc** là điểm khác biệt so với một hệ thống chỉ thực thi lệnh. '
  'Thao tác được coi là thành công khi quan sát xác nhận, không phải khi lệnh đã gửi đi.')

P('Một chi tiết tinh tế phát hiện khi tích hợp: trong vòng băng tải, khâu kiểm chứng phải đọc '
  '**thế giới mà robot vừa tác động** — tức thế giới mô phỏng — chứ không phải camera. Hai thế '
  'giới **cố ý khác nhau** ở đúng thời điểm đó (mục 3.3.3), nên hỏi nhầm nguồn sẽ cho kết luận '
  '"thất bại" trong khi thao tác đã thành công.')

H3('3.4.3. Giao diện người dùng')

P('Hệ thống có hai cách điều khiển: dòng lệnh dạng hỏi–đáp, và giao diện cửa sổ. Giao diện cửa sổ '
  '**dùng lại nguyên lớp điều khiển** của dòng lệnh, chỉ thay vòng nhập liệu, nên hai cách không '
  'thể lệch nhau về hành vi.')

P('Ba đặc điểm có chủ ý của giao diện: **khóa toàn bộ nút khi một tác vụ đang chạy** (robot chỉ có '
  'một, hai chuỗi chuyển động chồng nhau thì không chuỗi nào tới đích); **chạy tác vụ ở luồng '
  'riêng** để cửa sổ không đứng hình; và **hiển thị thứ hệ thống đang thấy** — bảng vật thể lấy '
  'thẳng từ khung camera mới nhất kèm cờ tin cậy, nên khi một nút bị từ chối thì nhìn bảng là biết '
  'vì sao.')

H3('3.4.4. Lớp điều khiển băng tải')

P('Băng tải được điều khiển qua vi điều khiển và mạch cầu H. Giao thức serial xử lý **từng ký tự** '
  'thay vì chờ ký tự xuống dòng — chi tiết nhỏ nhưng có lý do: công cụ theo dõi cổng serial mặc '
  'định có thể không gửi ký tự xuống dòng, và khi đó chương trình chờ mãi mà không báo lỗi gì, một '
  'kiểu hỏng rất khó đoán.')

P('Một đặc điểm của mạch đấu thực tế đáng ghi lại: do chân điều khiển không nằm trên chân cho phép '
  'của mạch cầu H mà nằm trên một chân điều hướng, quan hệ giữa tín hiệu và tốc độ bị **đảo '
  'ngược** — giá trị 0 là chạy hết tốc độ, giá trị lớn nhất là phanh. Chương trình tự lật ngược '
  'giá trị ghi ra, nên mọi lệnh bên ngoài giữ đúng nghĩa thông thường.')


# ================================================================== CHƯƠNG 4
H1('CHƯƠNG 4. KẾT QUẢ VÀ ĐÁNH GIÁ')

P('Chương này trình bày kết quả đo đạc của hệ thống: độ chính xác của từng khâu, quá trình giảm '
  'sai số, các thử nghiệm đầu-cuối, và đánh giá chung kèm hướng phát triển.')

P('Nguyên tắc áp dụng xuyên suốt: mọi kết quả đều được chấm bằng **đo đạc độc lập** — vị trí thật '
  'lấy từ mô phỏng hoặc đo bằng thước trên bàn thật — chứ không phải bằng chính thứ đang được kiểm '
  'tra. Một phép kiểm thử chỉ có giá trị khi nó **có thể thất bại**.')

H2('4.1. Độ chính xác')

H3('4.1.1. Kiểm chứng mô hình động học')

T('4.2', ['Nội dung kiểm chứng', 'Tiêu chí', 'Kết quả'],
  [
      ('Vòng lặp động học ngược → thuận trên lưới **5 424 điểm**', 'sai lệch < 1 µm',
       '**~1·10⁻¹³ m**'),
      ('Thay tư thế gốc vào công thức', 'khớp mô hình URDF', 'khớp'),
      ('Ràng buộc chiều dài thanh chống ở mọi tư thế', 'sai lệch < 1 µm', 'đạt'),
      ('Điểm ngoài vùng làm việc', 'phải báo lỗi, không trả nghiệm bừa', 'đạt'),
      ('Đo vị trí thật trong mô phỏng tại 9 điểm', 'lệch < 1 mm', '**< 1 mm**'),
  ],
  widths=[7.4, 4.2, 4.4])

P('Dòng đầu là phép thử mạnh nhất của phần động học: nó không kiểm tra vài điểm chọn sẵn mà **quét '
  'toàn vùng làm việc**, và sai số ở mức làm tròn của máy tính chứng tỏ hai công thức là nghịch '
  'đảo đúng của nhau chứ không phải gần đúng.')

P('Dòng cuối đo trên mô phỏng vật lý, nên sai số dưới 1 mm ở đây là **sai số của cơ cấu** — độ '
  'võng dưới trọng lực và sai số bám của bộ điều khiển khớp — chứ không phải của mô hình toán.')

H3('4.1.2. Sai số định vị của hệ thống thị giác')

P('Bộ dữ liệu đánh giá trong mô phỏng gồm **172 ảnh** có vị trí thật biết trước, thu bằng cách dời '
  'vật qua lưới 61 điểm × 3 vật, kèm các tình huống khó: robot lơ lửng sát vật ở bốn khe hở khác '
  'nhau, vật nằm trong khay, vật bị cắt mép ảnh. Phân tích chạy **ngoại tuyến** trên bộ dữ liệu '
  'đó, tái hiện đúng khâu nhận dạng của hệ thống chạy thật.')

IMG('4.1')

T('4.1', ['Điều kiện đánh giá', 'Trung bình', 'Phân vị 95', 'Lớn nhất'],
  [
      ('Mô phỏng, vùng robot gắp được (58 mẫu)', '**1,13 mm**', '3,7 mm', '6,2 mm'),
      ('Mô phỏng, toàn bộ điểm trong ảnh', '2,0 mm', '—', '20,6 mm'),
      ('Mô phỏng, vật trong khay (sau khi khớp mép trên)', '1,0 mm', '—', '1,9 mm'),
      ('Mô phỏng, ước lượng được gắn cờ tin cậy', '0,90 mm', '—', '**3,42 mm**'),
      ('Camera thật, 18 phép đo', '**4,50 mm**', '—', '6,31 mm'),
      ('Camera thật, bỏ phần lệch hệ thống', '2,35 mm', '—', '—'),
  ],
  widths=[7.8, 2.9, 2.6, 2.7])

P('So với dung sai **12 mm** của cơ cấu hút: mô phỏng đạt với biên an toàn gấp mười lần, camera '
  'thật đạt kể cả ở trường hợp xấu nhất. Các mẫu có sai số lớn trong mô phỏng (tới 20,6 mm) đều '
  'nằm **ngoài tầm với của robot** nên không ảnh hưởng tới chức năng.')

P('Dòng thứ tư là kết quả đáng giá nhất của cả khâu thị giác: **hễ hệ thống báo tin cậy thì sai số '
  'không vượt 3,42 mm.** Đó là thứ biến một phép ước lượng thành một phép ước lượng **dùng được**, '
  'vì lớp điều khiển có thể hành động trên kết quả được chấp nhận mà không cần kiểm tra lại.')

H3('4.1.3. Truy nguyên phần lệch hệ thống của camera thật')

P('Sai số 4,50 mm của camera thật gồm hai phần: **2,35 mm** tản mạn và khoảng **+9,6 mm** lệch hệ '
  'thống theo một hướng. Việc phần tản mạn nhỏ hơn hẳn phần lệch cho biết phép đo rất ổn định và '
  'phần dư là **lỗi mô hình**, không phải nhiễu — tức là có thể truy ra nguyên nhân.')

P('Giả thuyết đầu tiên là sai chiều cao vật. Giả thuyết này bị **bác bỏ bằng dấu của xu hướng**: '
  'sai chiều cao sinh ra lệch **tăng** theo khoảng cách (tính được: −13 → −19,8 mm), trong khi số '
  'liệu đo cho thấy lệch **giảm** (+12,5 / +12,4 / +3,9 mm tại ba khoảng cách). Hai xu hướng ngược '
  'chiều nhau nên giả thuyết sai, bất kể độ lớn có vẻ hợp lý.')

P('Đo riêng từng điểm mốc cho thấy **hai điểm mốc lệch 26 mm và 29 mm** so với tọa độ thiết kế. '
  'Cách khắc phục không cần bóc dán lại: chỉ cần **đo lại tọa độ thật của các điểm mốc và khai báo '
  'đúng** — điểm mốc không cần nằm đúng chỗ thiết kế, chỉ cần **biết đúng** chỗ nó nằm.')

H3('4.1.4. Độ bền')

IMG('4.3')

T('4.8', ['Yếu tố', 'Mức chịu được', 'Mức bắt đầu hỏng'],
  [
      ('Nhiễu cảm biến (độ lệch chuẩn, mức xám)', '≤ 10: không ảnh hưởng',
       '20: còn 99,2 %; 40: còn 83 %'),
      ('Mức sáng (hệ số nhân)', '0,5 – 1,6: ổn định', '0,3: mất 16,5 % số lần nhận dạng'),
      ('Khoảng cách giữa hai vật cạnh nhau', '≥ 60 mm trên bàn, ≥ 80 mm trên băng tải',
       'chạm nhau: bị từ chối'),
      ('Camera xê dịch sau khi chụp ảnh nền', 'dưới 3 điểm ảnh',
       '8,7 điểm ảnh: nền trước vọt lên 17 %'),
  ],
  widths=[5.4, 5.6, 5.0])

P('Camera dùng trong đề tài đo được nhiễu cỡ **2,2 mức xám** — nằm sâu trong vùng an toàn. Con số '
  'này cho phần đánh giá độ bền, vốn thực hiện bằng nhiễu nhân tạo thêm vào ảnh mô phỏng, có một '
  '**mốc thực tế để đối chiếu**.')

P('Khoảng cách tối thiểu trên băng tải (80 mm) lớn hơn trên mặt bàn (60 mm) vì lý do thuần túy '
  'hình học: hai vật cách nhau theo phương dọc băng thì cũng **cách camera xa gần khác nhau**, nên '
  'phối cảnh **nén** khoảng cách giữa chúng trong ảnh. Con số này xác định bằng cách chiếu hình '
  'bóng dự đoán của hai vật qua mô hình camera đã hiệu chuẩn rồi đo khe giữa hai khung bao, chứ '
  'không ước lượng bằng mắt.')

H2('4.2. Quá trình giảm sai số')

P('Mục này trình bày riêng quá trình giảm sai số, vì bản thân quá trình đó là một phần kết quả. '
  'Một con số cuối cùng không cho thấy nó đã được đạt tới bằng cách nào, và cũng không chứng minh '
  'được rằng mỗi phép khắc phục thật sự có tác dụng chứ không phải chỉ đẩy sai số sang chỗ khác.')

P('Nguyên tắc áp dụng: **đo trước, sửa, đo lại trên cùng dữ liệu**. Nhờ giữ lại bộ dữ liệu đánh '
  'giá 172 ảnh có đáp án biết trước, mọi phép khắc phục đều so được với chính nó trước khi sửa, '
  'thay vì so với một lần chạy khác trong điều kiện khác.')

IMG('4.2')

H3('4.2.1. Bảy phép khắc phục chính')

T('4.3', ['Vấn đề', 'Nguyên nhân', 'Cách khắc phục', 'Trước', 'Sau'],
  [
      ('Vật trong khay bị ước lượng xa hơn thật',
       'thành khay che nửa dưới, tâm khối lệch lên',
       'khớp mép trên thay vì tâm khối', '13,4 mm', '**1,0 mm**'),
      ('Vật trên bàn bị ước lượng thấp hơn thật',
       'tâm khối vùng màu lệch xuống 32 px so với tâm hình bóng',
       'khớp mép đáy', '28 mm', '**1,8 mm**'),
      ('Vật trên bàn THẬT lệch đều −33 mm',
       'mặt bàn phản chiếu, ảnh phản chiếu dính chân vật',
       'khớp mép trên, miễn nhiễm với phản chiếu', '11,4 mm', '**4,5 mm**'),
      ('Vật đứng trên băng tải bị quy về mặt bàn',
       'thiếu giả thuyết mặt đỡ thứ hai; sai 50 mm cao độ bị khuếch đại',
       'xét cả hai mặt đỡ, chọn giả thuyết tự nhất quán', '76 mm', '**~1 mm**'),
      ('Vị trí dao động mạnh giữa các khung',
       'ngưỡng màu cố định không bền với ánh sáng',
       'trừ ảnh nền', '3,0–13,8 mm', '**0,5–0,9 mm**'),
      ('Robot hút trượt dù camera báo đúng',
       'quỹ đạo phát theo đồng hồ thật, lệnh trả về khi robot còn đang đi',
       'chờ tới khi vị trí ĐO ĐƯỢC vào trong 2 mm', '46–48 mm', '**< 2 mm**'),
      ('Vật ở vùng xa không nhận ra được',
       'bàn máy ở tư thế gốc che tầm nhìn',
       'nâng lên tư thế quan sát trước khi đo', '17 mm', '**0,3 mm**'),
  ],
  widths=[3.6, 4.4, 4.0, 2.0, 2.0], size=11)

P('Đáng chú ý là **không phép khắc phục nào trong bảng trên là cải tiến thuật toán nhận dạng**. '
  'Tất cả đều là sửa một **giả định sai về hình học hoặc về thời gian**: vật đứng ở đâu, mặt nạ có '
  'ý nghĩa gì, robot đã tới nơi chưa. Đây là đặc điểm đáng nêu của các hệ thống thị giác ứng dụng '
  '— phần lớn sai số không đến từ khâu "nhìn" mà từ khâu "diễn giải cái nhìn thấy".')

H3('4.2.2. Hiệu chỉnh cờ tin cậy')

P('Bản thân cờ tin cậy cũng trải qua quá trình tương tự. Chỉ tiêu ở đây không phải sai số trung '
  'bình mà là **sai số lớn nhất trong số những ước lượng được gắn cờ tin cậy** — vì đó mới là đại '
  'lượng quyết định robot có hút trượt hay không.')

T('4.4', ['Thay đổi', 'Bỏ sót', 'Báo nhầm', 'Sai số lớn nhất khi báo tin cậy'],
  [
      ('Ngưỡng tỉ lệ nhìn thấy 0,85', '1/29', '10/143', '5,65 mm'),
      ('Nâng lên 0,90', '**0/29**', '12/143', '**3,42 mm**'),
      ('Thêm chặn trên 1,30', '0/29', '—', 'chặn được hai vật dính liền'),
      ('Thêm kiểm tra hình dáng', '0/29', '—', 'chặn được bàn tay và mảnh logo'),
  ],
  widths=[6.6, 2.4, 2.6, 4.4])

P('Việc nâng ngưỡng từ 0,85 lên 0,90 làm **tăng** số lần báo nhầm (10 → 12) nhưng **xóa hẳn** số '
  'lần bỏ sót (1 → 0) và giảm sai số lớn nhất từ 5,65 xuống 3,42 mm. Đây là đánh đổi **có chủ ý và '
  'không đối xứng**: một lần bỏ sót khiến robot hút lệch tâm và làm đổ vật, còn một lần báo nhầm '
  'chỉ khiến hệ thống chờ thêm một khung hình.')

H3('4.2.3. Những hướng đã thử và bị bác bỏ')

P('Phần này ghi lại các hướng đã thử nhưng không giữ. Chúng có giá trị vì mỗi hướng bị bác bỏ đều '
  'thu hẹp không gian giải pháp và giải thích vì sao cách đang dùng là cách còn lại.')

T('4.5', ['Đã thử', 'Vì sao bác bỏ'],
  [
      ('Khớp mép trên cho vật trên bàn với mặt nạ màu',
       'cho 5–12 mm so với 0,1–0,7 mm của mép đáy; mép trên của vùng màu bị nắp và vành nhãn làm '
       'nhòe khác nhau tùy khoảng cách'),
      ('Hạ ngưỡng tỉ lệ nhìn thấy để nhận được hai vật chạm nhau',
       'phá vỡ tính chất "hễ tin cậy thì trong dung sai"; mọi vật bị che một phần sẽ lọt'),
      ('Đo bề rộng bằng trung vị theo hàng để né ảnh phản chiếu',
       'mặt nạ trừ nền có mép lởm chởm nên trung vị kéo vật LÀNH LẶN xuống −25 %; phá trường hợp '
       'thường gặp để cứu trường hợp hiếm'),
      ('Thuật toán PnP chuyên cho điểm mốc đồng phẳng',
       'sai số chiếu lại 434 điểm ảnh trên ảnh thật, dù đúng với dữ liệu tổng hợp'),
      ('Quét toàn dải phơi sáng và độ khuếch đại để cứu ngưỡng cố định',
       'hai kiểu hỏng ngược chiều nhau, không cấu hình nào thỏa mãn cả hai'),
      ('Dùng thuật toán phân vùng theo gradient độ sáng để tách hai vật chạm nhau',
       'vệt lóa trên vỏ vật làm biên chạy sang vật bên cạnh, lấy mất ~30 % điểm ảnh'),
  ],
  widths=[6.6, 9.4])

H3('4.2.4. Hai sai sót phương pháp luận')

P('Hai lần suýt rút ra kết luận sai. Cả hai **không phải lỗi lập trình** mà là lỗi suy luận, nên '
  'đáng ghi lại hơn cả lỗi mã nguồn:')

N([
    '**Hai sai số triệt tiêu nhau tạo ra con số đẹp giả tạo.** Trước khi áp dụng phép trừ nền, '
    'cách khớp mép đáy *trông* chính xác hơn — 9,08 mm so với 18,31 mm — nên suýt được chọn. Thực '
    'ra mặt nạ khi đó còn lốm đốm làm phồng **đỉnh**, bù trừ một phần cho ảnh phản chiếu làm phồng '
    '**đáy**. Dọn sạch một sai số mới thấy sai số kia, và thứ tự đúng bị đảo ngược hoàn toàn. '
    '**Bài học: không chọn phương pháp theo con số tổng khi dữ liệu đầu vào còn bẩn.**',
    '**Bộ giải phân kỳ bị nhầm là sai số đo.** Mọi vật đặt tại cùng một chỗ đều cho **cùng một đáp '
    'án sai**, bất kể đó là vật nào. Sự *giống hệt nhau* này là dấu hiệu rơi vào nghiệm lạ, chứ '
    'sai số đo thì phải tản mạn. Đổi điểm xuất phát của phép lặp là hết hẳn.',
])


H2('4.3. Thử nghiệm đầu-cuối')

H3('4.3.1. Gắp–thả tự động dựa trên thị giác')

P('Thí nghiệm chạy trên **5 bố trí ngẫu nhiên** sinh từ một hạt giống cố định, mỗi lượt gồm phân '
  'loại ba vật vào ba khay rồi trả chúng về chỗ cũ. Chấm bằng **vị trí thật lấy từ mô phỏng**, '
  'không phải bằng chính camera.')

T('4.6', ['Nội dung', 'Tiêu chí', 'Kết quả'],
  [
      ('Phân loại vật vào đúng khay của từng loại', 'vật nằm trong khay của loại đó',
       '**15/15 vật · 5/5 lượt**'),
      ('Trả mọi vật về vị trí ban đầu', 'lệch ≤ 10 mm',
       '**15/15 vật** (TB 5,5 mm · max 7,1 mm)'),
      ('Lệch tâm khay khi thả', '— ', '0,3 / 0,5 / 1,8 mm'),
      ('Thời gian mỗi lượt', '—', '106 s + 111 s'),
      ('So với chế độ dùng vị trí lý tưởng (10 bố trí, cảnh trước)', 'không kém hơn',
       '**30/30 ở cả hai chế độ**; camera chậm hơn ~35 %'),
  ],
  widths=[6.4, 4.4, 5.2])

P('Dòng cuối là phép so sánh then chốt của đề tài: nó trả lời câu hỏi *"thay vị trí lý tưởng bằng '
  'camera thì mất gì?"* — và câu trả lời là **không mất tỉ lệ thành công nào**, chỉ chậm hơn vì '
  'phải dừng lại quan sát.')

H3('4.3.2. Bản sao số và hai lớp phòng vệ')

T('4.7', ['Nội dung kiểm chứng', 'Kết quả'],
  [
      ('Vật ảo so với vị trí camera báo, khi vật đứng yên', '**0,0 – 0,4 mm** (hệ mô phỏng)'),
      ('Bám theo khi dời vật thật hơn 100 mm', '**1 mm thật = 0,3 mm** hệ mô phỏng'),
      ('Khởi động lại hệ thống', 'vật ảo tự đồng bộ về vị trí thật'),
      ('Robot bám vật đang di chuyển trên băng', 'giữ sai lệch **3–4 mm thật** suốt quá trình'),
      ('Gây nhiễu có chủ ý: đưa tay vào khung hình nhiều lần',
       '**0 lần dịch chuyển giả**; 25 khung bị lớp hình dáng loại, 12 khung bị giữ chờ xác nhận'),
      ('Chuyển động THẬT trong cùng khoảng thời gian',
       '177 mm và 170 mm — **cả hai đều được ghi nhận đầy đủ**'),
  ],
  widths=[8.0, 8.0])

P('Hai dòng cuối phải đọc cùng nhau. Một lớp phòng vệ chỉ đáng tin khi nó **vừa chặn được cái sai '
  'vừa không chặn nhầm cái đúng** — nếu chỉ chứng minh vế đầu thì việc tắt hẳn hệ thống cũng cho '
  'kết quả y hệt.')

H3('4.3.3. Kiểm thử tự động')

P('Song song với các thử nghiệm trên hệ thống thật, **206 trường hợp kiểm thử tự động** chạy trong '
  'khoảng 3 giây sau mỗi lần sửa mã, không cần mô phỏng, camera hay robot (Bảng 3.10).')

P('Chúng bảo vệ những tính chất khó kiểm bằng tay: động học đúng trên toàn vùng làm việc; bộ lập '
  'kế hoạch từ chối đúng các trường hợp cần từ chối; và máy trạng thái băng tải giữ được bất biến '
  '"không bao giờ hai nguồn cùng ghi vị trí một vật" — tính chất này có **34 trường hợp kiểm thử** '
  'riêng, vì nó là chỗ dễ sai nhất và hậu quả thì không nhìn thấy ngay.')

H2('4.4. Đánh giá và hướng phát triển')

H3('4.4.1. Đối chiếu mục tiêu và kết quả')

T('4.9', ['Mục tiêu (mục 1.4.1)', 'Kết quả đạt được', 'Đánh giá'],
  [
      ('Mô hình động học robot delta',
       'công thức dạng đóng hai chiều; vòng lặp trên 5 424 điểm sai lệch ~1·10⁻¹³ m', 'đạt'),
      ('Mô phỏng tương tác vật lý với vật thể',
       'va chạm, cơ cấu hút, kiểm chứng bằng đo đạc sau mỗi thao tác', 'đạt'),
      ('Nhận dạng và định vị bằng camera đơn',
       '1,13 mm (mô phỏng) · 4,50 mm (camera thật), so với dung sai 12 mm', 'đạt'),
      ('Đánh giá độ tin cậy của từng kết quả',
       'ước lượng được chấp nhận có sai số ≤ 3,42 mm', 'đạt'),
      ('Gắp–thả tự động dựa trên thị giác',
       '15/15 vật vào đúng khay trên 5 bố trí ngẫu nhiên', 'đạt'),
      ('Đóng vòng điều khiển hai chiều',
       'mô phỏng điều khiển băng tải thật; vòng làm việc khép kín', 'đạt'),
  ],
  widths=[4.6, 7.4, 2.4])

H3('4.4.2. Giới hạn của hệ thống')

P('Việc nêu rõ giới hạn quan trọng không kém việc nêu kết quả: một giới hạn được xác định và đo '
  'đạc là thông tin kỹ thuật, còn một giới hạn bị giấu đi sẽ trở thành lỗi bất ngờ khi vận hành.')

T('4.10', ['Giới hạn', 'Biểu hiện', 'Hướng khắc phục'],
  [
      ('Giả định "mỗi màu một vật"', 'không phân biệt được hai vật cùng màu',
       'chuyển từ danh sách vật cố định sang "N thực thể phát hiện được"'),
      ('Hai vật chạm nhau trong ảnh', 'bị từ chối (ρ = 0,71–0,80)',
       'điều kiện vận hành: đặt cách nhau ≥ 60 mm trên bàn, ≥ 80 mm trên băng'),
      ('Ảnh nền gắn với vị trí camera và ánh sáng', 'camera xê dịch 8,7 px làm hỏng mặt nạ',
       'đã có cảnh báo tự động; chụp lại ảnh nền khi cần'),
      ('Camera đơn cần biết trước mặt đỡ', 'không đo được chiều cao vật',
       'đo chiều cao bằng bài toán ngược của phép khớp mép trên'),
      ('Bộ giải va chạm lún vào vật động', 'bàn máy lún 5–8 mm nếu ép quá đỉnh vật',
       'đã tránh bằng ràng buộc điều khiển; nguyên nhân chưa kiểm chứng'),
      ('Tốc độ băng tải đã hết khả năng động cơ', '16 mm/s, không tăng được nữa',
       'đổi puly, hộp số hoặc nâng điện áp nguồn'),
  ],
  widths=[4.0, 5.0, 7.0])

H3('4.4.3. Hướng phát triển')

N([
    '**Đo chiều cao vật bằng camera đơn** — bài toán ngược của phép khớp mép trên: đáy vật trên '
    'mặt phẳng đã biết cho tọa độ ngang, mép trên cho chiều cao. Mở ra khả năng phân biệt vật cùng '
    'màu nhưng khác kích thước, tức gỡ được giới hạn đầu tiên trong Bảng 4.10.',
    '**Gắp khi vật đang chạy** — cơ chế bám theo vật đã có sẵn (mục 3.3.4); chỉ cần bỏ bước dừng '
    'băng và bù trễ của chuỗi nhận thức.',
    '**Nhiều vật cùng màu** — thay giả định "mỗi màu một vật" bằng danh sách thực thể động. Đây là '
    'thay đổi lớn nhất còn lại, ảnh hưởng tới cả khâu nhận dạng, lập kế hoạch và cơ cấu hút.',
    '**Hiệu chuẩn lại điểm mốc** — đo lại tọa độ thật của sáu điểm mốc để xóa phần lệch hệ thống '
    '+9,6 mm, đưa sai số camera thật về gần mức 2,35 mm đã đo được.',
    '**Bù trễ** — đo độ trễ đầu-cuối của chuỗi nhận thức rồi dự đoán vị trí vật tại thời điểm robot '
    'tới nơi, thay vì tại thời điểm chụp ảnh.',
])

H3('4.4.4. Kết luận')

P('Đề tài đã xây dựng hoàn chỉnh một hệ thống trong đó **tín hiệu từ camera thật điều khiển robot '
  'delta trong môi trường mô phỏng**, với đầy đủ các khâu: mô hình động học, môi trường mô phỏng '
  'có tương tác vật lý, hệ thống thị giác máy tính, bản sao số và vòng điều khiển khép kín có '
  'thiết bị thật.')

P('Về mặt kỹ thuật, kết quả đáng kể nhất không phải con số sai số mà là **cơ chế tự đánh giá độ '
  'tin cậy**. Hệ thống không chỉ đưa ra vị trí mà còn đưa ra mức độ chắc chắn của nó, và lớp điều '
  'khiển từ chối hành động trên thông tin không đáng tin. Bốn lớp phòng vệ được xây dựng lần lượt, '
  'mỗi lớp ra đời từ một lỗi thật đã quan sát được, và chúng bắt những loại lỗi khác hẳn nhau — '
  'trong đó việc nhận ra rằng **tỉ lệ diện tích về nguyên tắc không thể phát hiện vị trí sai** là '
  'bước ngoặt của toàn bộ phần thị giác.')

P('Về mặt phương pháp, đề tài cho thấy giá trị của việc **đo trước khi thiết kế** và **đo lại sau '
  'khi sửa**. Nhiều giả định ban đầu đã bị chính số liệu bác bỏ: pha giảm tốc cho băng tải hóa ra '
  'không cần, mép đáy *trông* chính xác hơn mép trên chỉ vì hai sai số triệt tiêu nhau, và một giả '
  'thuyết về nguồn gốc sai số bị bác bỏ bằng **dấu của xu hướng** chứ không phải bằng độ lớn. Nếu '
  'chỉ dựa vào suy luận mà không đo, phần lớn những điều đó sẽ đi vào hệ thống dưới dạng lỗi khó '
  'tìm.')

S.save()
