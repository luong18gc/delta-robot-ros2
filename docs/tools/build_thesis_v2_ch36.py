#!/usr/bin/env python3
"""
Dựng khóa luận (bản 2) — Chương 3 đến Chương 6, thành một tệp riêng.

    python3 docs/tools/build_thesis_v2_ch36.py

Nối tiếp Chương 1–2 (`build_thesis_v2.py`), dùng chung khung định dạng `thesis_style.py`.

Hai yêu cầu riêng của người làm đồ án, định hình cách viết:

1. **Chương 4 (thị giác) phải chi tiết nhất** — đây là trọng tâm đề tài. Chương này dài gần gấp
   đôi các chương khác và đi tới từng quyết định kỹ thuật, kể cả những quyết định đã bị bác bỏ.
2. **Mỗi phép khắc phục sai số phải nêu rõ TRƯỚC là bao nhiêu, SAU còn bao nhiêu.** Một con số
   cuối cùng không cho thấy công sức bỏ ra; cặp số trước–sau thì có, và nó cũng là bằng chứng
   rằng phép khắc phục thật sự có tác dụng chứ không phải đổi chỗ sai số đi nơi khác.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import omml as m                                                   # noqa: E402
import thesis_style as S                                           # noqa: E402
from thesis_style import B, EQ, H1, H2, H3, IMG, N, P, T           # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Khoa_luan_v2_ch3_6.docx')

FIGURES = [
    ('3.1', 'Mô hình URDF chỉ mô tả được cấu trúc cây; mạch kín được đóng lúc chạy bằng các khớp '
            'tháo rời được', 'kl34_mach_kin.png', 15.5),
    ('3.2', 'Bố trí cảnh mô phỏng nhìn từ trên xuống', 'kl34_bo_tri_canh.png', 13.5),
    ('3.3', 'Cửa sổ dung sai cho phép hút thành công', 'kl34_cua_so_hut.png', 13.5),
    ('3.4', 'Ba khay phân loại có nhãn tên loại, nhìn từ camera mô phỏng', 'bin_labels.png', 14.0),
    ('3.5', 'Đồ thị các nút và chủ đề ROS 2 của hệ thống', 'ros_graph.png', 15.5),
    ('4.1', 'Từ điểm ảnh về tọa độ ba chiều bằng phép giao tia với mặt phẳng đã biết cao độ',
     'kl34_mo_hinh_camera.png', 15.0),
    ('4.2', 'Sáu điểm mốc ArUco dùng cho hiệu chuẩn ngoại tham số',
     'calibration_markers.png', 14.0),
    ('4.3', 'So sánh mặt nạ thu được bằng ngưỡng màu cố định và bằng phép trừ ảnh nền',
     'foreground_comparison.png', 15.0),
    ('4.4', 'Vì sao phải khớp mép trên khi mặt bàn phản chiếu', 'kl34_khop_mep.png', 15.0),
    ('4.5', 'Bốn lớp phòng vệ và loại lỗi mà mỗi lớp phát hiện được',
     'kl34_lop_phong_ve.png', 15.0),
    ('4.6', 'Bảy phép khắc phục sai số, đo trước và sau khi áp dụng',
     'kl456_giam_sai_so.png', 15.5),
    ('4.7', 'Phân bố sai số định vị trên mặt bàn trong mô phỏng', 'vision_error_map.png', 15.0),
    ('4.8', 'Độ bền của khâu nhận dạng với nhiễu cảm biến và với mức sáng',
     'vision_robustness.png', 15.0),
    ('4.9', 'Kết quả nhận dạng trên camera thật', 'real_camera_detections.png', 15.0),
    ('5.1', 'Luồng thông tin của vòng khép kín hai chiều', 'kl456_vong_kin.png', 15.5),
    ('5.2', 'Đối chiếu vị trí vật thật và vật ảo', 'twin_coordinates.png', 14.5),
    ('5.3', 'Máy trạng thái của vòng băng tải và chỗ bàn giao quyền quyết định vị trí',
     'kl456_may_trang_thai.png', 16.0),
    ('6.1', 'Kiến trúc tổng thể của hệ thống', 'system_architecture.png', 15.5),
]
TABLES = [
    ('3.1', 'Cấu trúc động học của một chân trong mô hình mô phỏng'),
    ('3.2', 'Hai nguyên nhân quá tải tính toán và cách khắc phục'),
    ('3.3', 'Hệ số thời gian thực của mô phỏng theo cấu hình'),
    ('3.4', 'Quy đổi kích thước giữa thế giới thật và mô hình số với hệ số tỉ lệ k = 3'),
    ('3.5', 'Dung sai của cơ cấu hút'),
    ('3.6', 'Kết quả kiểm chứng chức năng gắp–thả trên mô phỏng'),
    ('4.1', 'Kết quả hiệu chuẩn camera'),
    ('4.2', 'Ngưỡng phân lớp màu trong không gian HSV'),
    ('4.3', 'Hai kiểu hỏng ngược nhau của ngưỡng cố định'),
    ('4.4', 'So sánh hai phương pháp tách vật trên cùng một khung hình camera thật'),
    ('4.5', 'Đặc trưng hình học dùng để khớp hình bóng theo từng tình huống'),
    ('4.6', 'Bốn lớp phát hiện kết quả không đáng tin'),
    ('4.7', 'Ngưỡng kiểm tra hình dáng, đo trên ảnh thật'),
    ('4.8', 'Bảy phép khắc phục sai số chính, đo trước và sau'),
    ('4.9', 'Quá trình hiệu chỉnh cờ tin cậy'),
    ('4.10', 'Những hướng đã thử và bị bác bỏ'),
    ('4.11', 'Sai số định vị của hệ thống thị giác'),
    ('4.12', 'Độ bền của khâu nhận dạng'),
    ('5.1', 'Ba mức tích hợp giữa đối tượng thật và mô hình số'),
    ('5.2', 'Kiểm chứng đồng bộ vị trí của bản sao số'),
    ('5.3', 'Kiểm chứng hai lớp phòng vệ bằng gây nhiễu có chủ ý'),
    ('5.4', 'Thông số đo được của băng tải'),
    ('6.1', 'Đối chiếu mục tiêu đề ra và kết quả đạt được'),
    ('6.2', 'Giới hạn đã biết của hệ thống'),
]
S.configure(OUT, FIGURES, TABLES)

v, nn, fnc, o, sq = m.v, m.n, m.fn, m.op, m.seq
sb, sp, fr, dl, mx, sqr, txt = m.sub, m.sup, m.frac, m.delim, m.matrix, m.sqrt, m.txt


# ================================================================== CHƯƠNG 3
H1('CHƯƠNG 3. XÂY DỰNG MÔI TRƯỜNG MÔ PHỎNG VÀ TƯƠNG TÁC VẬT THỂ', page_break=False)

P('Chương 2 đã thiết lập mô hình toán của cơ cấu. Chương này dựng môi trường để mô hình đó vận '
  'hành: mô phỏng vật lý của robot, cảnh làm việc có vật thể, cơ cấu gắp–thả, và lớp điều khiển '
  'cấp cao nhận lệnh bằng ngôn ngữ tác vụ thay vì tọa độ khớp.')

P('Môi trường mô phỏng ở đây không phải công cụ phụ trợ mà là **một nửa của hệ thống cuối cùng**: '
  'theo kịch bản của đề tài, robot chỉ tồn tại trong mô phỏng, còn vật thể thì có thật. Mọi sai '
  'lệch giữa hành vi mô phỏng và hành vi cơ cấu thật sẽ xuất hiện nguyên vẹn trong kết quả.')

H2('3.1. Yêu cầu đối với môi trường mô phỏng')

P('Bốn yêu cầu được đặt ra, lần lượt dẫn tới các lựa chọn kỹ thuật trong chương:')

N([
    '**Mô phỏng động lực học có va chạm**, để thao tác gắp–thả bị ràng buộc bởi vật lý chứ không '
    'phải chỉ là phép gán tọa độ. Nếu vật thể được đặt bằng cách ghi thẳng vị trí thì mọi phép '
    'kiểm chứng đều trở nên vô nghĩa — hệ thống sẽ luôn "thành công".',
    '**Giao diện trạng thái giống cảm biến thật**: chỉ các đại lượng đo được trên robot thật mới '
    'được công bố cho lớp điều khiển.',
    '**Cảnh làm việc tương ứng với bố trí thật** về mặt hình học, để kết quả thị giác chuyển sang '
    'mô phỏng được mà không phải sửa công thức.',
    '**Tốc độ đủ gần thời gian thực**, vì khâu thị giác chạy theo đồng hồ thật của camera.',
])

H2('3.2. Mô hình hóa cơ cấu mạch kín')

P('Khó khăn đầu tiên nằm ở định dạng mô tả robot. URDF — định dạng chuẩn của ROS — chỉ biểu diễn '
  'được **cấu trúc cây**: mỗi khâu có đúng một khâu cha. Robot delta lại là cơ cấu **mạch kín**, '
  'trong đó bàn máy được ba chân cùng nối tới. Cấu trúc đó không tồn tại trong một cây.')

IMG('3.1')

P('Giải pháp là mô tả cơ cấu dưới dạng ba nhánh rời nhau trong URDF, rồi **đóng mạch lúc chạy** '
  'bằng cơ cấu hàn hai khâu lại của trình mô phỏng. Khi mô phỏng khởi động, ba mối hàn được tạo '
  'và cơ cấu trở thành mạch kín thật sự: lực truyền qua cả ba chân, bàn máy bị ràng buộc đúng như '
  'cơ cấu vật lý.')

P('Điều kiện bắt buộc là **hai khâu được hàn phải trùng khung tọa độ tại tư thế gốc**. Hệ quả '
  'thực tiễn rất quan trọng cho phần sau của đề tài: không thể tùy tiện đổi kích thước hình học '
  'của robot trong mô hình, vì làm vậy sẽ phá các mối hàn. Đây chính là lý do ở Chương 4 bài toán '
  'kích thước vật thể phải giải bằng **hệ số tỉ lệ** chứ không bằng cách phóng to robot.')

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

P('Chuỗi ba khớp trượt bị động giữ cho bàn máy **luôn song song với đế** — đúng tính chất đặc '
  'trưng của robot delta đã nêu ở Chương 1, và ở đây nó được tái tạo bằng ràng buộc cơ học chứ '
  'không phải bằng giả thiết.')

H2('3.3. Giao diện điều khiển và phản hồi trạng thái')

P('Mỗi khớp chủ động được điều khiển bằng bộ điều khiển vị trí kiểu PID, nhận lệnh góc qua một '
  'chủ đề riêng. Ở chiều ngược lại, trạng thái khớp được công bố để lớp điều khiển tính động học '
  'thuận.')

P('Một quyết định thiết kế quan trọng: **chỉ công bố các khớp chủ động**. Robot thật chỉ có bộ mã '
  'hóa vòng quay trên ba động cơ; các khớp bị động — khớp cầu, khớp trượt treo bàn máy — không có '
  'cảm biến. Nếu mô phỏng công bố cả vị trí bàn máy thì lớp điều khiển sẽ vô tình dùng một thông '
  'tin mà robot thật không có, và toàn bộ phần động học thuận trở nên thừa. Việc **cố ý giấu bớt '
  'thông tin** là điều kiện để kết quả có ý nghĩa.')

IMG('3.5')

H3('3.3.1. Hai nguyên nhân quá tải tính toán')

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

P('Hai lỗi này đáng ghi lại vì chúng tiêu biểu cho một lớp vấn đề của hệ thống phân tán: **chi '
  'phí nằm ở chỗ truyền tin, không nằm ở chỗ tính toán**. Không có thuật toán nào được cải tiến; '
  'chỉ giảm số thông điệp phải xử lý.')

T('3.3', ['Cấu hình', 'Hệ số thời gian thực'],
  [
      ('Đồ họa tích hợp, có cửa sổ hiển thị', '≈ 0,35'),
      ('Đồ họa tích hợp, không cửa sổ', '≈ 0,94'),
      ('Card đồ họa rời, trước khi khắc phục quá tải', '0,56'),
      ('Card đồ họa rời, sau khi khắc phục', '0,77 – 0,99'),
  ],
  widths=[10.0, 6.0])

P('Hệ số thời gian thực nhỏ hơn 1 có một hệ quả tinh tế mà về sau gây ra một lỗi thực sự: vòng '
  'phát điểm quỹ đạo chạy theo **đồng hồ thật**, nên khi mô phỏng chạy chậm hơn, lệnh "đi tới '
  'điểm P" trả về trong lúc robot vẫn đang trên đường. Lỗi này được mô tả ở mục 3.6.')

H2('3.4. Cảnh làm việc và hệ số tỉ lệ')

P('Cảnh gồm mặt bàn, băng tải, ba khay phân loại và ba vật thể. Toàn bộ tọa độ và kích thước được '
  'khai báo tại **một vị trí duy nhất** trong mã nguồn; mọi thành phần khác — tệp mô tả cảnh, nút '
  'gắp–thả, bộ lập kế hoạch, khối thị giác — đều đọc từ đó.')

IMG('3.2')

IMG('3.4')

P('Ba khay được dán nhãn tên loại ở mặt quay về phía camera. Chi tiết nhỏ này có vai trò trình '
  'bày: nếu ba khay giống hệt nhau thì người xem không phân biệt được robot đang **phân loại** '
  'hay chỉ đang thả vật vào một ô trống bất kỳ. Nhãn dùng chữ trắng trên nền xám — không dùng '
  'màu của vật — vì khay có màu bão hòa sẽ bị chính khâu nhận dạng hiểu nhầm là vật.')

P('Nguyên tắc một nguồn dữ liệu này tỏ ra có giá trị trong thực nghiệm. Khi băng tải thật được '
  'lắp xong và phát hiện chạy ngược chiều dự kiến, dây động cơ đã hàn cố định nên không đảo cực '
  'được. Việc xử lý chỉ là **đổi một con số** — đầu nào là đầu nạp, đầu nào là điểm gắp — và toàn '
  'hệ thống đi theo. Nếu hằng số đó nằm rải rác trong các nút thì đã phải sửa nhiều chỗ và gần '
  'như chắc chắn bỏ sót.')

H3('3.4.1. Vì sao phải dùng hệ số tỉ lệ')

P('Vật thể thật dùng trong đề tài là lon nước ngọt, đường kính 57,5 mm và cao 147 mm. Vùng làm '
  'việc của robot chỉ cao khoảng 120 mm tính từ mặt bàn. Đặt một lon thật vào đó thì **đỉnh lon '
  'chạm trần vùng làm việc**: robot với tới được nhưng không nhấc lên được, và khay cũng không '
  'chứa nổi.')

P('Phóng to robot không phải lựa chọn, vì đổi hình học trong mô hình sẽ phá các mối hàn mạch kín '
  '(mục 3.2) và mọi kiểm chứng động học phải làm lại. Giải pháp là **thu nhỏ thế giới**: vật thể '
  'ảo giữ đúng tỉ lệ hình dạng của vật thật nhưng kích thước chia cho hệ số ' +
  'k = 3, và mọi tọa độ cũng vậy.')

T('3.4', ['Đại lượng', 'Thế giới thật', 'Mô hình số (chia cho k = 3)'],
  [
      ('Đường kính vật', '57,5 mm', '19,2 mm'),
      ('Chiều cao vật', '147 mm', '49,0 mm'),
      ('Chiều dài băng tải', '230 mm', '76,7 mm'),
      ('Chiều cao mặt băng so với bàn', '50 mm', '16,7 mm'),
      ('Dung sai cho phép của cơ cấu hút', '36 mm', '12 mm'),
  ],
  widths=[6.4, 4.8, 4.8])

P('Hệ số k = 3 không phải chọn tùy ý. Với k = 2,5, vật ảo cao 58,8 mm, và khi robot mang một vật '
  'đi **qua phía trên** một vật khác đang đứng thì đầu công tác phải ở cao độ −99,4 mm — vượt '
  'trần vùng làm việc. Trong thực nghiệm, điều này biểu hiện thành việc vật đang mang **đè vào** '
  'vật đang đứng và làm đổ nó. Với k = 3 chỉ cần −119 mm, nằm an toàn trong vùng làm việc.')

P('Một tính chất quan trọng của phép tỉ lệ: **nó không làm sai số thị giác xấu đi**. Camera phủ '
  'vùng rộng gấp k lần nên số milimét ứng với một điểm ảnh tăng k lần, nhưng khi quy kết quả về '
  'không gian ảo thì sai số lại chia cho k. Hai tác động triệt tiêu nhau.')

H2('3.5. Cơ cấu gắp–thả')

P('Cơ cấu hút chân không được mô phỏng bằng cùng cơ chế hàn hai khâu đã dùng để đóng mạch kín: '
  'khi hút, bàn máy và vật được hàn lại; khi nhả, mối hàn bị hủy. Mối hàn **giữ nguyên vị trí '
  'tương đối tại thời điểm tạo**, nên vật đi theo robot đúng từng milimét mà không bị giật về tâm '
  'đầu hút — đúng hành vi của giác hút thật.')

P('Hai chi tiết kỹ thuật đã phải xử lý:')

B([
    '**Trùng tên chủ đề điều khiển.** Các mối hàn đóng mạch kín dùng chung một chủ đề mặc định; '
    'nếu cơ cấu hút cũng dùng chủ đề đó thì một lệnh nhả sẽ **phá luôn mạch kín** của robot. Mỗi '
    'vật vì vậy được cấp một chủ đề riêng.',
    '**Trạng thái khởi động.** Cơ cấu hàn tự động dính ngay khi mô phỏng khởi động và không có '
    'tùy chọn tắt, nên lúc mới chạy robot bị cả ba vật giữ cứng. Nút điều khiển phải chủ động gửi '
    'lệnh nhả cho tới khi nhận được xác nhận.',
])

H3('3.5.1. Điều kiện hút và dung sai')

P('Việc hút chỉ được chấp nhận khi đầu hút nằm trong một cửa sổ dung sai quanh đỉnh vật. Cửa sổ '
  'này mô phỏng giới hạn vật lý của giác hút thật: lệch tâm quá nhiều thì không kín khí, còn cách '
  'xa quá thì không tạo được chân không.')

IMG('3.3')

T('3.5', ['Điều kiện', 'Giá trị cho phép (hệ ảo)', 'Tương đương thật'],
  [
      ('Lệch ngang giữa tâm đầu hút và tâm vật', '≤ 12 mm', '≤ 36 mm'),
      ('Khe giữa mặt dưới đầu hút và đỉnh vật', 'từ −4 mm đến +6 mm', 'từ −12 mm đến +18 mm'),
  ],
  widths=[7.6, 4.4, 4.0])

P('Giá trị **12 mm** trở thành chỉ tiêu thiết kế cho toàn bộ Chương 4: hệ thống thị giác chỉ có '
  'ích nếu sai số định vị của nó nhỏ hơn con số này.')

H3('3.5.2. Một hiện tượng của bộ giải va chạm')

P('Trong quá trình kiểm chứng va chạm, phát hiện một hiện tượng cần lưu ý. Khi đầu công tác được '
  'ra lệnh ép **xuống thấp hơn đỉnh một vật đang nằm trên bàn**, đầu công tác lún dần vào vật '
  'khoảng 5–8 mm thay vì dừng lại. Hiện tượng xảy ra với mọi hình dạng vật đã thử; nghi do vật '
  'nhẹ bị kẹp giữa lực của bộ điều khiển và mặt bàn, khiến bộ giải tiếp xúc không hội tụ. Nguyên '
  'nhân **chưa được kiểm chứng**.')

P('Cách xử lý là một ràng buộc đặt lên lớp điều khiển: **hạ đầu công tác tới đúng cao độ đỉnh vật '
  'rồi hút, không bao giờ ra lệnh thấp hơn**. Ràng buộc này về sau trở thành có ích ngoài dự '
  'kiến, vì nó cũng chính là hành vi đúng của một giác hút thật.')

H2('3.6. Lớp điều khiển tác vụ')

P('Trên nền động học và cơ cấu gắp–thả, một lớp điều khiển cấp cao được xây dựng để nhận lệnh '
  'dạng tác vụ. Lớp này tách thành hai phần có trách nhiệm khác hẳn nhau:')

B([
    '**Bộ lập kế hoạch** — thuần toán, không phụ thuộc trình mô phỏng: đổi một lệnh cấp cao thành '
    'chuỗi thao tác di chuyển, hút, nhả; tính điểm chạm và điểm thả; kiểm tra **toàn bộ** các '
    'đích bằng động học ngược **trước khi** robot chuyển động.',
    '**Bộ thực thi** — chạy kế hoạch và **kiểm chứng bằng đo đạc**: sau khi hút, vật phải được '
    'nhấc lên ít nhất 10 mm; sau khi thả, vật phải thật sự nằm trong khay.',
])

P('Việc kiểm tra toàn tuyến trước khi chuyển động quan trọng hơn vẻ ngoài của nó. Một điểm nằm '
  'ngoài vùng làm việc ở **giữa** đường đi sẽ không bị phát hiện nếu chỉ kiểm tra điểm đầu và '
  'điểm cuối; khi đó robot dừng giữa chừng ở tư thế bất kỳ, có thể đang mang vật.')

P('Nguyên tắc **kiểm chứng bằng đo đạc** là điểm khác biệt so với một hệ thống chỉ thực thi lệnh. '
  'Thao tác được coi là thành công khi quan sát xác nhận, không phải khi lệnh đã gửi đi.')

H3('3.6.1. Lỗi do quỹ đạo chạy theo đồng hồ thật')

P('Mục 3.3 đã nêu rằng mô phỏng chạy chậm hơn thời gian thực. Vòng phát điểm quỹ đạo lại đếm theo '
  'đồng hồ thật, nên khi phát xong điểm cuối cùng thì robot **vẫn còn đang di chuyển**. Lệnh "đi '
  'tới điểm P" trả về, lớp trên tưởng đã tới nơi và ra lệnh hút.')

P('Sai lệch đo được tại thời điểm hút lên tới **46–48 mm**, trong khi ước lượng của camera chỉ '
  'lệch 1,8 mm. Đây là ví dụ rõ nét về một loại lỗi khó truy: **khâu bị nghi ngờ (thị giác) hoàn '
  'toàn vô can**, còn khâu gây lỗi lại là một giả định ngầm trong lớp chuyển động đã viết từ '
  'trước. Cách khắc phục là chờ cho tới khi vị trí **đo được** nằm trong 2 mm quanh đích.')

P('Lỗi này đã tồn tại từ khi lớp chuyển động được viết, nhưng chỉ lộ ra khi vật thể đổi từ khối '
  'vuông thấp sang lon cao — vì với vật thấp, sai lệch còn nằm trong dung sai.')

H2('3.7. Kiểm chứng môi trường mô phỏng')

T('3.6', ['Nội dung kiểm chứng', 'Kết quả'],
  [
      ('Phân loại 3 vật vào đúng khay của từng loại',
       '3/3 vật đúng khay, lệch tâm khay 0,3 / 0,5 / 1,8 mm'),
      ('Trả 3 vật từ khay về vị trí ban đầu', '3/3 vật đúng chỗ, lệch 4,9 / 7,0 / 7,4 mm'),
      ('5 bố trí ngẫu nhiên, phân loại', '15/15 vật đúng khay, 5/5 lượt hoàn thành'),
      ('5 bố trí ngẫu nhiên, trả về chỗ cũ',
       '15/15 vật đúng chỗ, trung bình 5,5 mm, lớn nhất 7,1 mm'),
      ('Thời gian mỗi lượt', '106 s (phân loại) + 111 s (trả về)'),
  ],
  widths=[7.2, 8.8])

P('Không lượt nào thất bại. Các sai lệch đều nhỏ hơn dung sai 12 mm của cơ cấu hút, và phần lớn '
  'bắt nguồn từ sai số bám của bộ điều khiển khớp cùng độ võng của cơ cấu dưới trọng lực — tức là '
  'sai số của **cơ cấu**, không phải của mô hình toán hay của khâu nhận thức.')

H2('3.8. Kết luận chương')

P('Chương 3 đã dựng xong môi trường mô phỏng và lớp tương tác với vật thể:')

B([
    'Cơ cấu mạch kín được mô hình hóa bằng cách đóng mạch lúc chạy, kèm ràng buộc không được đổi '
    'hình học — ràng buộc này dẫn thẳng tới lựa chọn dùng hệ số tỉ lệ.',
    'Giao diện trạng thái cố ý **chỉ công bố đại lượng đo được trên robot thật**, để phần động '
    'học thuận có vai trò thực sự.',
    'Cảnh làm việc khai báo tại một nguồn duy nhất, với hệ số tỉ lệ k = 3 được chọn từ ràng buộc '
    'chiều cao vùng làm việc chứ không phải tùy ý.',
    'Cơ cấu hút có cửa sổ dung sai **12 mm**, trở thành chỉ tiêu thiết kế cho hệ thống thị giác.',
    'Lớp điều khiển tác vụ kiểm tra toàn tuyến trước khi chuyển động và **kiểm chứng bằng đo '
    'đạc** sau mỗi thao tác.',
])

P('Chương tiếp theo xây dựng hệ thống thị giác máy tính — khâu cung cấp thông tin vị trí vật thể '
  'cho môi trường vừa dựng, và là trọng tâm của đề tài.')




# ================================================================== CHƯƠNG 4
H1('CHƯƠNG 4. HỆ THỐNG THỊ GIÁC MÁY TÍNH')

P('Chương này là trọng tâm của đề tài. Nhiệm vụ đặt ra: từ ảnh của **một camera đơn**, xác định '
  'chủng loại và vị trí ba chiều của vật thể trong hệ tọa độ robot, kèm theo đánh giá **mức độ '
  'đáng tin** của từng kết quả.')

P('Yêu cầu định lượng đã xác định ở Chương 3: sai số định vị phải nhỏ hơn **12 mm** trong hệ ảo — '
  'dung sai của cơ cấu hút. Nhưng trong quá trình thực hiện, một yêu cầu thứ hai nổi lên và hóa '
  'ra khó hơn: hệ thống phải **tự biết khi nào mình không chắc**. Lý do thực tiễn: một ước lượng '
  'sai mà được tin tưởng khiến robot hút trượt hoặc đâm vào vật, trong khi một ước lượng bị từ '
  'chối chỉ làm hệ thống chờ thêm một khung hình.')

P('Chương được tổ chức theo đúng thứ tự của đường ống xử lý — mô hình camera, hiệu chuẩn, tách '
  'vật, ước lượng vị trí, đánh giá độ tin cậy — rồi dành riêng **mục 4.7** để trình bày quá trình '
  'giảm sai số, trong đó mỗi phép khắc phục đều nêu rõ sai số **trước** và **sau**.')

H2('4.1. Mô hình camera và bài toán định vị')

P('Camera được mô hình hóa theo mô hình lỗ kim. Một điểm trong không gian, biểu diễn trong hệ tọa '
  'độ robot, trước hết được đưa về hệ tọa độ camera bằng phép biến đổi cứng:')

EQ(sq(sb(v('X'), v('c')), o('='), v('R'), sb(v('X'), v('r')), o('+'), v('t')), '4.1')

P('rồi chiếu lên mặt phẳng ảnh bằng ma trận nội tham số:')

EQ(sq(v('s'), mx([[v('u')], [v('v')], [nn(1)]]), o('='), v('K'), sb(v('X'), v('c')),
      o(','), txt('   '), v('K'), o('='),
      mx([[sb(v('f'), v('x')), nn(0), sb(v('c'), v('x'))],
          [nn(0), sb(v('f'), v('y')), sb(v('c'), v('y'))],
          [nn(0), nn(0), nn(1)]])), '4.2')

P('Trong đó **R**, **t** là ngoại tham số — tư thế camera so với robot; **K** là nội tham số — '
  'tiêu cự và tâm ảnh của riêng thiết bị. Hệ số **s** là độ sâu, và chính nó là nguồn gốc của khó '
  'khăn: phép chiếu **làm mất một chiều**, mọi điểm trên cùng một tia cho cùng một điểm ảnh.')

IMG('4.1')

P('Camera đơn vì vậy không đủ để xác định vị trí ba chiều nếu không có thêm ràng buộc. Ràng buộc '
  'dùng ở đây đến từ hình học của cảnh: **vật đứng trên một mặt phẳng đã biết cao độ**. Khi đó '
  'tâm vật nằm ở cao độ bằng cao độ mặt đỡ cộng nửa chiều cao vật, và tọa độ ngang tìm được bằng '
  'cách giao tia nhìn với mặt phẳng đó:')

EQ(sq(sb(v('X'), v('r')), o('='), sp(v('R'), txt('T')),
      dl(sq(v('λ'), sp(v('K'), txt('−1')), mx([[v('u')], [v('v')], [nn(1)]]), o('−'), v('t'))),
      o(','), txt('   '), v('λ'), txt(' sao cho '), sb(v('z'), v('r')), o('='),
      sb(v('z'), txt('đỡ')), o('+'), fr(v('h'), nn(2))), '4.3')

H3('4.1.1. Khi cảnh có nhiều mặt đỡ')

P('Giả thiết "vật đứng trên mặt phẳng đã biết" là giả thiết tiêu chuẩn của các hệ gắp–thả dùng '
  'camera đơn. Nhưng khi băng tải được thêm vào, cảnh có **hai** mặt đỡ ở hai cao độ khác nhau: '
  'mặt bàn và mặt băng, chênh nhau 50 mm thật.')

P('Cách xử lý là xét cả hai giả thiết rồi chọn giả thiết **tự nhất quán**: giả thiết "vật đứng '
  'trên băng" chỉ được chấp nhận nếu vị trí suy ra từ chính nó rơi đúng vào phạm vi mặt băng. Đây '
  'là một dạng kiểm tra tính nhất quán nội tại — một giả thiết chỉ được nhận khi kết luận của nó '
  'không mâu thuẫn với tiền đề của nó.')

P('Mức độ quan trọng của việc chọn đúng mặt đỡ lớn hơn vẻ ngoài rất nhiều. Đo trên **cùng một '
  'khung hình, cùng một vật**: giả thiết mặt bàn cho (+167; +13) mm, giả thiết mặt băng cho '
  '(+91; +14) mm. Chênh lệch **76 mm** chỉ vì sai 50 mm cao độ — vì camera nhìn chúc 46°, sai số '
  'theo chiều cao bị khuếch đại khi chiếu xuống mặt phẳng ngang.')

H2('4.2. Hiệu chuẩn camera')

P('Hiệu chuẩn chia thành hai bài toán độc lập. Việc tách rời chúng không chỉ là thói quen: hai '
  'bài toán có **chu kỳ thực hiện khác nhau**, và gộp lại sẽ buộc phải làm lại cả hai mỗi khi chỉ '
  'một trong hai thay đổi.')

H3('4.2.1. Nội tham số')

P('Nội tham số gắn với **thiết bị cụ thể** — hai camera cùng kiểu vẫn khác nhau — nhưng không đổi '
  'khi di chuyển camera, nên chỉ cần đo **một lần cho mỗi máy**. Phương pháp dùng bàn cờ phẳng '
  'chụp ở nhiều tư thế khác nhau; bài toán quy về cực tiểu hóa sai số chiếu lại.')

P('Camera dùng trong đề tài là loại lấy nét cố định. Đây là **ưu điểm chứ không phải hạn chế**: '
  'tiêu cự không thể trôi sau khi hiệu chuẩn, nên kết quả hiệu chuẩn có giá trị lâu dài. Kết quả: '
  'tiêu cự 1417,4 điểm ảnh, sai số chiếu lại **0,222 điểm ảnh**.')

H3('4.2.2. Ngoại tham số và bài toán PnP')

P('Ngoại tham số là tư thế camera so với robot. Phương pháp dùng sáu điểm mốc ArUco dán trên mặt '
  'bàn tại các tọa độ đã biết; xác định tư thế từ các cặp điểm–ảnh là bài toán PnP '
  '(*Perspective-n-Point*).')

IMG('4.2')

P('Hai chi tiết kỹ thuật đã phải xử lý, và điều đáng nói là **cả hai chỉ lộ ra trên ảnh thật**, '
  'trong khi với dữ liệu tổng hợp thì mọi cách làm đều cho kết quả đúng:')

N([
    '**Cách lấy tâm điểm mốc.** Lấy trung bình bốn góc cho kết quả lệch khi nhìn xiên, vì phép '
    'chiếu phối cảnh **không bảo toàn trung điểm**. Phải lấy **giao điểm hai đường chéo** — đại '
    'lượng mà phép chiếu phối cảnh có bảo toàn.',
    '**Thuật toán giải PnP.** Một thuật toán chuyên dùng cho điểm mốc đồng phẳng cho nghiệm sai '
    'hẳn trên ảnh thật — sai số chiếu lại **434 điểm ảnh** — dù vẫn đúng với điểm tổng hợp. Phải '
    'thay bằng thuật toán tổng quát kèm bước tinh chỉnh phi tuyến.',
])

T('4.1', ['Đại lượng', 'Camera mô phỏng', 'Camera thật'],
  [
      ('Sai số chiếu lại khi hiệu chuẩn', '0,14 điểm ảnh', '0,222 điểm ảnh'),
      ('Sai lệch vị trí camera', '0,35 mm', '—'),
      ('Sai lệch hướng nhìn', '0,017°', '—'),
      ('Sai số ngoại tham số quy ra hệ ảo', '—', '0,93 mm'),
      ('Góc chúc', '32°', '46,1°'),
      ('Độ phân giải', '640 × 480', '1280 × 720'),
      ('Nhiễu cảm biến (độ lệch chuẩn)', 'khai báo nhưng không có tác dụng', '2,2 mức xám'),
  ],
  widths=[6.0, 5.0, 5.0])

P('Góc chúc thật khác hẳn mô phỏng vì bàn không đủ dài để lùi camera xa hơn. Khối thị giác **tự '
  'thích nghi** vì nó dùng mô hình camera đo được chứ không giả định góc nào; góc dốc hơn thậm chí '
  'có lợi cho việc chống che khuất giữa các vật.')

H3('4.2.3. Quy ước tỉ lệ trong hiệu chuẩn')

P('Chương 3 đã đặt ra hệ số tỉ lệ k = 3 giữa thế giới thật và mô hình số. Câu hỏi thiết kế là: áp '
  'dụng phép chia này ở đâu trong đường ống?')

P('Lựa chọn của đề tài là đưa **tọa độ ảo** vào bài toán PnP **ngay từ khâu hiệu chuẩn**, thay vì '
  'hiệu chuẩn theo milimét thật rồi chia kết quả về sau. Cơ sở toán học: thu nhỏ toàn bộ thế giới '
  'k lần chỉ làm **vectơ tịnh tiến của camera chia cho k**; ma trận nội tham số, hệ số méo và bản '
  'thân phép chiếu phối cảnh đều **không đổi**.')

P('Hệ quả thực tiễn rất lớn: toàn bộ khối thị giác phía sau — phép giao tia, hình bóng dự đoán, '
  'mặt bàn, khay, băng tải — chạy nguyên trong hệ ảo mà **không phải sửa một dòng nào** khi '
  'chuyển từ camera mô phỏng sang camera thật. Đây cũng là lý do mối nối giữa hai thế giới ở '
  'Chương 5 mỏng tới mức chỉ còn một phép cộng cao độ đế robot.')

P('Cái giá duy nhất: vị trí camera in ra nhỏ hơn thật k lần, chỉ ảnh hưởng lúc báo cáo. Một lỗi '
  'đã mắc phải ở đây và đáng ghi lại: hàm quy đổi ngược về milimét thật **quên cộng cao độ mặt '
  'bàn**, nên báo camera nằm ở −45 mm, tức dưới mặt bàn. Kiểm thử cũ không bắt được vì nó so kết '
  'quả với chính hàm đang sai; sửa lại bằng cách so với **hình học giá đỡ đo bằng thước**.')

H2('4.3. Tách vật thể khỏi nền')

P('Khâu đầu tiên của đường ống là xác định những vùng ảnh nào thuộc về vật. Đề tài đã dùng **hai '
  'phương pháp khác nhau cho hai thế giới** — và đây là một kết luận về bản chất bài toán, không '
  'phải một giải pháp chắp vá.')

H3('4.3.1. Phân ngưỡng theo màu trong không gian HSV')

P('Phương pháp thứ nhất: chuyển ảnh từ không gian RGB sang HSV rồi phân ngưỡng theo lớp màu. '
  'Không gian HSV tách riêng **sắc màu** (H) khỏi **độ sáng** (V), nên bền với bóng đổ hơn hẳn '
  'RGB — một điểm ảnh trong bóng vẫn giữ nguyên sắc màu, chỉ giảm độ sáng.')

T('4.2', ['Lớp màu', 'Sắc màu H', 'Độ bão hòa S', 'Độ sáng V'],
  [
      ('Đỏ', '[0; 8] ∪ [172; 180]', '≥ 90', '≥ 40'),
      ('Lục', '[45; 85]', '≥ 90', '≥ 40'),
      ('Lam', '[95; 125]', '≥ 90', '≥ 40'),
  ],
  widths=[3.6, 5.6, 3.4, 3.4])

P('Lớp đỏ phải khai báo thành **hai khoảng** vì sắc màu là đại lượng tuần hoàn và màu đỏ nằm vắt '
  'qua điểm 0°. Ngưỡng độ bão hòa loại được mặt bàn và thành khay.')

P('Ngưỡng độ sáng V ≥ 40 thoạt nhìn có vẻ thừa, nhưng khi mặt bàn chuyển sang màu tối nó trở '
  'thành ngưỡng **quan trọng nhất**. Lý do nằm ở chính định nghĩa độ bão hòa:')

EQ(sq(v('S'), o('='), fr(sq(fnc('max'), dl(sq(v('R'), o(','), v('G'), o(','), v('B'))), o('−'),
                           fnc('min'), dl(sq(v('R'), o(','), v('G'), o(','), v('B')))),
                        sq(fnc('max'), dl(sq(v('R'), o(','), v('G'), o(','), v('B')))))), '4.4')

P('Mẫu số tiến về 0 ở vùng tối, nên **một chênh lệch vài mức xám do nhiễu cũng cho độ bão hòa '
  'rất cao**. Đo trên ảnh thật: trong vùng có V < 40, tới **85 % điểm ảnh** vượt ngưỡng bão hòa '
  '90. Với nền tối, thứ thật sự loại được mặt bàn là ngưỡng độ sáng — và vì vậy **không được hạ '
  'ngưỡng V** để cố nhận vật trong bóng; phần tối của vật phải xử lý bằng cách thêm ánh sáng.')

H3('4.3.2. Vì sao ngưỡng cố định không bền với ánh sáng')

P('Trên camera thật, bộ ngưỡng cố định thất bại theo **hai kiểu ngược nhau về cơ chế**, tùy điều '
  'kiện chiếu sáng:')

T('4.3', ['Điều kiện', 'Cơ chế hỏng', 'Hậu quả'],
  [
      ('Ban ngày, rèm mở', 'mặt bàn sáng lên và ám màu', 'mặt bàn lọt vào mặt nạ'),
      ('Thắp một đèn', 'mặt bàn quá tối, độ bão hòa hóa nhiễu (công thức 4.4)',
       'gần như **cả mặt bàn** lọt vào'),
  ],
  widths=[4.0, 7.0, 5.0])

P('Điểm then chốt: hai kiểu hỏng này **ngược chiều nhau**, nên không tồn tại bộ ngưỡng nào xử lý '
  'được cả hai. Đã quét toàn dải phơi sáng (80–2600) và độ khuếch đại (0–100) của camera, không '
  'cấu hình nào cứu được. Vấn đề không nằm ở việc chọn ngưỡng nào cho khéo, mà ở **chính ý tưởng '
  'dùng ngưỡng cố định cho một đại lượng phụ thuộc ánh sáng**.')

H3('4.3.3. Trừ ảnh nền')

P('Giải pháp là so ảnh hiện tại với **ảnh mặt bàn trống** chụp trước đó; điểm ảnh nào khác ảnh nền '
  'quá một ngưỡng thì thuộc về vật. Đại lượng được so là **sự thay đổi**, không phải giá trị tuyệt '
  'đối, nên nó độc lập với mức sáng chung của cảnh.')

IMG('4.3')

P('Hiệu quả đo được rất rõ. Trên cảnh **không có vật nào**:')

B([
    'cách lấy ngưỡng báo **12,06 %** diện tích ảnh là "vật";',
    'phép trừ nền báo **0,00 %**;',
    'trong khi nhiễu cảm biến chỉ cỡ **1 mức xám** so với ngưỡng 30 — tức biên an toàn rất rộng.',
])

P('Cái giá phải trả là ảnh nền **gắn cứng với vị trí camera và điều kiện chiếu sáng**. Đo được: '
  'camera xê dịch chỉ **8,7 điểm ảnh** đã làm mọi đường biên trong cảnh lọt vào mặt nạ, tỉ lệ nền '
  'trước vọt từ gần 0 lên **17 %**, sinh ra những vùng giả lớn hơn cả vật thật.')

P('Điều nguy hiểm là kiểu hỏng này **không báo lỗi**. Tư thế camera được giải lại mỗi khung nên nó '
  '**tự lành** sau khi camera xê dịch; ảnh nền thì không có cơ chế tương tự. Cách xử lý: hệ thống '
  'tự đối chiếu vị trí các điểm mốc hiện tại với vị trí của chúng **trong chính ảnh nền**, và '
  'cảnh báo khi lệch quá 3 điểm ảnh. Nguyên tắc rút ra: **thứ gì chụp lại một trạng thái rồi giữ '
  'nguyên thì phải có cách tự biết trạng thái đó đã cũ.**')

H3('4.3.4. Vì sao hai thế giới cần hai phương pháp')

P('Phép trừ nền **không dùng được cho cảnh mô phỏng**: ở đó ba khay màu xám cũng "không phải mặt '
  'bàn", nên vật nằm trong khay dính liền với khay thành một vùng và bị loại.')

P('Ngược lại, phân ngưỡng theo màu **không dùng được cho vật thật**, vì một lý do sâu hơn. Toàn bộ '
  'khâu ước lượng phía sau ngầm giả định **mặt nạ thu được chính là hình bóng của vật**. Giả định '
  'đó đúng với vật mô phỏng có thân một màu đặc, nhưng sai hẳn với lon thật: màu nằm thành vành, '
  'xen mảng trắng và logo lớn.')

T('4.4', ['Đại lượng đo trên cùng một khung hình', 'Theo màu', 'Trừ nền'],
  [
      ('Tỉ lệ cao/rộng của ba vật (vật thật: 2,56)', '2,28 / 1,88 / **0,93**',
       '2,45 / 2,26 / 2,65'),
      ('Diện tích ba vật (điểm ảnh)', '14 645 / 5 603 / 2 003', '28 449 / 22 261 / 22 240'),
      ('Nhiễu vị trí theo x (mm thật)', '3,4 / 5,9 / 13,8', '3,0 / 7,1 / 4,4'),
      ('Bước nhảy lớn nhất giữa hai khung', '11,6 / 19,3 / 48,1 mm', '8,9 / 22,6 / 16,0 mm'),
      ('Tỉ lệ nhìn thấy', 'phải đoán bằng hằng số', '**0,99 ± 0,01**'),
      ('Cờ tin cậy', 'hai vật bị coi là bị che ở **mọi** khung', '**60/60 khung tin cậy**'),
  ],
  widths=[7.0, 4.6, 4.4])

P('Ba vật **cùng kích thước** mà nhận theo màu cho diện tích chênh nhau **bảy lần**, và một vật '
  'có tỉ lệ cao/rộng 0,93 trong khi vật thật là 2,56 — nghĩa là phép đo đang đo **thiết kế nhãn** '
  'chứ không đo vật.')

P('Còn tỉ lệ nhìn thấy 0,99 ± 0,01 có ý nghĩa đặc biệt: nó nói rằng hình bóng đo được **khớp** '
  'hình bóng dự đoán. Nhờ đó cơ chế phát hiện che khuất (mục 4.6) lấy lại **đúng định nghĩa ban '
  'đầu** của nó, thay vì phải chia cho một hằng số đoán được.')

P('**Kết luận rút ra:** bản sao số cần giống nhau về **hình học**, còn khâu nhận dạng là bài toán '
  'riêng của từng thế giới. Đây cũng là câu trả lời cho băn khoăn "vật ảo trông không giống vật '
  'thật": nó không cần giống về bề ngoài, chỉ cần giống về hình học.')


H2('4.4. Ước lượng vị trí từ hình bóng')

P('Có mặt nạ rồi, bước tiếp theo là suy ra vị trí. Cách đơn giản nhất — lấy tâm khối của vùng ảnh '
  'rồi giao tia — có một sai sót **hệ thống**: tâm khối là tâm của **phần nhìn thấy**, không phải '
  'hình chiếu của tâm vật. Với vật bị che một phần, hai điểm này lệch nhau theo đúng hướng nhìn, '
  'và sai lệch càng lớn khi phần bị che càng nhiều.')

P('Phương pháp dùng trong đề tài là **khớp hình bóng**. Từ mô hình hình học của vật (hộp, trụ, '
  'cầu, kèm kích thước) và mô hình camera, dựng **hình bóng dự đoán** — bao lồi của ảnh các điểm '
  'trên bề mặt vật — rồi tìm vị trí (x, y) sao cho một **đặc trưng hình học** của hình bóng dự '
  'đoán trùng với đặc trưng tương ứng đo được trên ảnh.')

EQ(sq(fnc('F'), dl(sq(v('x'), o(','), v('y'))), o('='),
      mx([[sq(sb(v('v'), txt('đo')), o('−'), sb(v('v'), txt('dự đoán')),
              dl(sq(v('x'), o(','), v('y'))))],
          [sq(sb(v('u'), txt('đo')), o('−'), sb(v('u'), txt('dự đoán')),
              dl(sq(v('x'), o(','), v('y'))))]]), o('='), nn(0)), '4.5')

P('Hệ hai phương trình hai ẩn này giải bằng phương pháp Newton. Cao độ z không phải ẩn vì nó đã '
  'bị ràng buộc bởi giả thiết mặt đỡ (mục 4.1).')

H3('4.4.1. Chọn đặc trưng nào, và vì sao')

P('Đặc trưng được chọn khác nhau tùy tình huống. Việc chọn sai không làm thuật toán hỏng — nó vẫn '
  'hội tụ — mà làm kết quả **sai một cách có hệ thống**, kiểu sai khó phát hiện nhất.')

IMG('4.4')

T('4.5', ['Tình huống', 'Đặc trưng dùng', 'Vì sao', 'Sai số trước → sau'],
  [
      ('Vật trong khay (mô phỏng)', 'mép trên',
       'thành khay che nửa dưới nên mép đáy vô nghĩa', '**13,4 → 1,0 mm**'),
      ('Vật trên bàn, mặt nạ theo màu', 'mép đáy',
       'thân vật có màu xuống tận đáy, đáy tì trên bàn', '**28 → 1,8 mm**'),
      ('Vật trên bàn thật, mặt bàn phản chiếu', 'mép trên',
       'ảnh phản chiếu dính liền chân vật', '**11,4 → 4,5 mm**'),
  ],
  widths=[4.4, 2.8, 5.2, 3.6])

P('Trường hợp thứ ba đáng phân tích kỹ. Mặt bàn thật phản chiếu hình ảnh của vật, và ảnh phản '
  'chiếu **dính liền** chân vật nên mép đáy của mặt nạ không còn là chỗ vật chạm bàn. Sai lệch đo '
  'được **đều khoảng −33 mm ở cả ba vật** — và chính sự *đồng đều* đó là manh mối: một sai số '
  'ngẫu nhiên không thể giống nhau ở ba vật khác nhau, nên nó phải có nguyên nhân hình học chung. '
  'Con số −33 mm đúng bằng chiều cao ảnh phản chiếu.')

P('Phép trừ nền **không xóa được** ảnh phản chiếu, vì ảnh phản chiếu chỉ xuất hiện khi có vật — '
  'nó không nằm trong ảnh nền. Nhưng ảnh phản chiếu luôn nằm **phía dưới** vật, nên mép trên miễn '
  'nhiễm. Đổi sang khớp mép trên là đủ, không cần xử lý ảnh phức tạp.')

P('⚠️ Cần phân biệt với một kết luận ngược chiều đã nêu ở trên: với **mặt nạ theo màu**, mép trên '
  'lại *không* dùng được (đo 5–12 mm so với 0,1–0,7 mm của mép đáy), vì khi đó mép trên là mép '
  'của vùng **màu** — bị nắp và vành nhãn làm nhòe — chứ không phải mép hình học của vật. Cùng '
  'một đặc trưng, hai kết luận trái ngược, vì **mặt nạ mang ý nghĩa khác nhau** trong hai trường '
  'hợp.')

H3('4.4.2. Hai sai sót phương pháp luận đã mắc phải')

P('Hai lần suýt rút ra kết luận sai trong quá trình này. Cả hai đều **không phải lỗi lập trình** '
  'mà là lỗi suy luận, nên đáng ghi lại hơn cả lỗi mã nguồn:')

N([
    '**Hai sai số triệt tiêu nhau tạo ra con số đẹp giả tạo.** Trước khi áp dụng phép trừ nền, '
    'cách khớp mép đáy *trông* chính xác hơn — 9,08 mm so với 18,31 mm — nên suýt được chọn. Thực '
    'ra mặt nạ khi đó còn lốm đốm làm phồng **đỉnh**, bù trừ một phần cho ảnh phản chiếu làm phồng '
    '**đáy**. Dọn sạch một sai số mới thấy sai số kia, và thứ tự đúng bị đảo ngược hoàn toàn. '
    '**Bài học: không chọn phương pháp theo con số tổng khi dữ liệu đầu vào còn bẩn.**',
    '**Bộ giải phân kỳ bị nhầm là sai số đo.** Khi xuất phát từ tâm khối — vốn bị ảnh phản chiếu '
    'kéo xuống — mọi vật đặt tại cùng một chỗ đều cho **cùng một đáp án sai** (+88,7; −28,7) bất '
    'kể đó là vật nào. Sự *giống hệt nhau* này là dấu hiệu rơi vào nghiệm lạ, chứ sai số đo thì '
    'phải tản mạn. Đổi điểm xuất phát sang ước lượng thô từ mép đáy là hết hẳn.',
])

H2('4.5. Tách vùng ảnh khi hai vật chạm nhau')

P('Hai vật chạm nhau trong ảnh — chưa cần che nhau — bị gộp thành một vùng liên thông, nên chỉ '
  'được gán **một danh tính** và trượt mọi phép kiểm tra hình dáng. Hậu quả nặng hơn vẻ ngoài: '
  'vùng gộp **giành mất lớp màu**, nên vật thứ ba đứng riêng cũng biến mất theo.')

P('Cách xử lý gồm ba phần:')

N([
    '**Giữ mọi vùng của mỗi màu rồi mới chọn**, thay vì chốt ngay vùng lớn nhất. Chọn theo kích '
    'cỡ là quyết định **trước khi** biết vùng nào hợp lệ về hình dáng.',
    '**Tách vùng đã trượt** bằng cách lấy điểm ảnh của từng lớp màu làm hạt giống, rồi gán phần '
    'không mang màu về hạt giống **gần nhất theo khoảng cách**. Chỉ gọi khi đã trượt: gọi vô điều '
    'kiện thì vành logo màu khác sẽ xé một vật lành lặn làm đôi.',
    '**Chỉ đếm phần phía trên chân vật dự đoán** khi tính diện tích và kích thước, để ảnh phản '
    'chiếu không được tính vào.',
])

P('Ba cạm bẫy đã gặp khi cài phép tách, đều đáng nêu vì chúng là lỗi của **công cụ được chọn** '
  'chứ không phải của ý tưởng:')

B([
    '**Thuật toán phân vùng theo gradient độ sáng là công cụ sai.** Vệt lóa trên vỏ vật làm biên '
    'chạy sang vật bên cạnh, lấy mất khoảng 30 % điểm ảnh của vật kề. Gán theo khoảng cách cho '
    'biên **thẳng đứng**, đúng với hình học hai hình trụ đứng cạnh nhau.',
    '**Phép biến đổi khoảng cách có đánh nhãn theo thành phần liên thông cũng sai**: hai vật chạm '
    'nhau thì hạt giống hai màu cũng chạm, thành một thành phần, nên cả vùng về màu đông điểm ảnh '
    'hơn. Phải tính khoảng cách **riêng cho từng màu**.',
    '**Logo mang màu khác** làm hạt giống nhiễu, nên chỉ lấy **mảng lớn nhất** của mỗi màu.',
])

P('Kết quả: vật đứng riêng lấy lại được (tỉ lệ nhìn thấy 1,02, tin cậy). Nhưng **hai vật chạm '
  'nhau vẫn bị từ chối** (tỉ lệ nhìn thấy 0,71–0,80 so với ngưỡng 0,90). Đã thử hạ ngưỡng và '
  '**bác bỏ**: ngưỡng đó bảo đảm tính chất "hễ báo tin cậy thì sai số trong dung sai gắp", hạ '
  'xuống thì mọi vật bị che một phần đều lọt và robot sẽ hút lệch tâm. Trường hợp này vì vậy được '
  'ghi nhận thành **điều kiện vận hành**: đặt các vật cách nhau ít nhất một bề rộng vật.')

H2('4.6. Phát hiện kết quả không đáng tin')

P('Mục này trả lời yêu cầu định tính nêu ở đầu chương. Hệ thống không chỉ đưa ra vị trí mà còn đưa '
  'ra **một cờ tin cậy**; lớp điều khiển từ chối thao tác trên kết quả không tin cậy.')

IMG('4.5')

T('4.6', ['Lớp', 'Kiểm tra gì', 'Bắt được loại lỗi nào'],
  [
      ('Hình học', 'vị trí suy ra có nằm trong vùng đặt vật không',
       'dây điện, mép bàn, sàn nhà lọt vào khung hình'),
      ('Hình dáng', 'bề rộng và chiều cao khung bao so với hình bóng dự đoán',
       'bàn tay, mảnh logo bị tách rời, hai vật dính liền'),
      ('Tỉ lệ nhìn thấy', 'diện tích đo / diện tích hình bóng dự đoán, ngoài [0,90; 1,30]',
       'vật bị che một phần'),
      ('Xác nhận nhiều khung', 'vị trí nhảy xa phải trụ lại 5 khung liên tiếp',
       'nhiễu thoáng qua, bàn tay lướt ngang'),
  ],
  widths=[3.4, 6.6, 6.0])

P('Bốn lớp này **không chồng lấn**: mỗi lớp bắt một loại lỗi mà lớp khác bỏ sót. Điều đó quan '
  'trọng hơn việc siết chặt một lớp duy nhất, và đoạn dưới đây giải thích vì sao.')

H3('4.6.1. Vì sao tỉ lệ diện tích không thể phát hiện vị trí sai')

P('Đây là một giới hạn **mang tính cấu trúc**, không phải chuyện đặt ngưỡng chưa khéo. Việc nhận '
  'ra nó là bước ngoặt dẫn tới ba lớp còn lại.')

P('Quy trình ước lượng xác định vị trí **trước**, rồi mới dựng hình bóng dự đoán **tại chính vị '
  'trí vừa tìm được**. Nếu một vùng ảnh lớn hơn vật thật, phép khớp sẽ đẩy vật về **gần camera '
  'hơn**; mà hình bóng dự đoán tại vị trí gần hơn đó **cũng lớn hơn**. Tỉ lệ hai diện tích vì vậy '
  '**tự chuẩn hóa** về gần 1 dù vị trí sai hàng trăm milimét.')

P('Thử nghiệm xác nhận: đưa tay vào khung hình làm vật ảo nhảy **284 mm** trong khi cờ tin cậy '
  'vẫn báo **1,00**. Không ngưỡng nào đặt trên tỉ lệ diện tích bắt được trường hợp này.')

H3('4.6.2. Kiểm tra hình dáng — thông tin độc lập')

P('Lớp kiểm tra hình dáng khắc phục được vì nó dùng **thông tin mà phép khớp không chạm tới**. '
  'Phép khớp (công thức 4.5) chỉ ràng buộc **mép trên** và **tâm ngang**; **bề rộng** và **chiều '
  'cao** của khung bao là hai đại lượng độc lập, phép khớp không tự điều chỉnh cho chúng khớp.')

T('4.7', ['Trường hợp đo trên ảnh thật', 'Lệch bề rộng', 'Kết luận'],
  [
      ('Ba vật lành lặn', '+5 % / +13 % / +8 %', 'đạt'),
      ('Vùng rộng gấp 2,3 lần (bàn tay)', '+133 %', 'loại'),
      ('Mảnh vụn (vành logo bị tách)', '−59 %', 'loại'),
  ],
  widths=[7.0, 4.0, 5.0])

P('Ngưỡng **chiều cao** phải **không đối xứng** — từ 0,65 đến 1,60 — vì ảnh phản chiếu nằm trong '
  'khung bao làm vật lành lặn cao hơn dự đoán 16–28 %. Giới hạn dưới chặt hơn vì "thấp hơn hẳn" '
  'chính là dấu vân tay của một vành logo bị tách rời.')

H3('4.6.3. Ràng buộc không tự chuẩn hóa: vật lý')

P('Lớp cuối cùng dựa vào một ràng buộc mà **không phép khớp nào lách được**: vật không dịch '
  'chuyển 284 mm trong một phần mười giây. Một vị trí mới cách xa vị trí cũ phải được **năm khung '
  'liên tiếp xác nhận** mới được chấp nhận.')

P('Điểm tinh tế: bộ lọc này phải chặn nhiễu mà **không chặn nhầm** chuyển động thật. Nhấc vật đặt '
  'sang chỗ khác thì chỗ mới **trụ lại** nên vẫn được ghi nhận, chỉ trễ nửa giây; còn nhiễu thoáng '
  'qua thì không trụ được. Kết quả kiểm chứng ở Chương 5 xác nhận cả hai vế.')


H2('4.7. Quá trình giảm sai số')

P('Mục này trình bày riêng quá trình giảm sai số, vì bản thân quá trình đó là một phần kết quả. '
  'Một con số cuối cùng — 1,13 mm hay 4,50 mm — không cho thấy nó đã được đạt tới bằng cách nào, '
  'và cũng không chứng minh được rằng mỗi phép khắc phục thật sự có tác dụng chứ không phải chỉ '
  'đẩy sai số sang chỗ khác.')

P('Nguyên tắc áp dụng xuyên suốt: **đo trước, sửa, đo lại trên cùng dữ liệu**. Nhờ giữ lại bộ dữ '
  'liệu đánh giá 172 ảnh có đáp án biết trước, mọi phép khắc phục đều so được với chính nó trước '
  'khi sửa, thay vì so với một lần chạy khác trong điều kiện khác.')

IMG('4.6')

H3('4.7.1. Bảy phép khắc phục chính')

T('4.8', ['Vấn đề', 'Nguyên nhân', 'Cách khắc phục', 'Trước', 'Sau'],
  [
      ('Vật trong khay bị ước lượng xa hơn thật',
       'thành khay che nửa dưới, tâm khối lệch lên',
       'khớp mép trên thay vì tâm khối', '13,4 mm', '**1,0 mm**'),
      ('Vật trên bàn bị ước lượng thấp hơn thật',
       'tâm khối vùng màu lệch xuống 32 px so với tâm hình bóng',
       'khớp mép đáy', '28 mm', '**1,8 mm**'),
      ('Vật trên bàn THẬT lệch đều −33 mm',
       'mặt bàn phản chiếu, ảnh phản chiếu dính chân vật',
       'khớp mép trên (miễn nhiễm với phản chiếu)', '11,4 mm', '**4,5 mm**'),
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
       'nâng lên tư thế quan sát trước khi đo', '17 mm (cờ = 0)', '**0,3 mm**'),
  ],
  widths=[3.6, 4.4, 4.0, 2.0, 2.0], size=11)

P('Đáng chú ý là **không phép khắc phục nào trong bảng trên là cải tiến thuật toán nhận dạng**. '
  'Tất cả đều là sửa một **giả định sai về hình học hoặc về thời gian**: vật đứng ở đâu, mặt nạ '
  'có ý nghĩa gì, robot đã tới nơi chưa. Đây là đặc điểm đáng nêu của các hệ thống thị giác ứng '
  'dụng — phần lớn sai số không đến từ khâu "nhìn" mà từ khâu "diễn giải cái nhìn thấy".')

H3('4.7.2. Giảm sai số của cờ tin cậy')

P('Bản thân cờ tin cậy cũng trải qua quá trình tương tự. Chỉ tiêu ở đây không phải sai số trung '
  'bình mà là **sai số lớn nhất trong số những ước lượng được gắn cờ tin cậy** — vì đó mới là '
  'đại lượng quyết định robot có hút trượt hay không.')

T('4.9', ['Thay đổi', 'Bỏ sót', 'Báo nhầm', 'Sai số lớn nhất khi báo TIN CẬY'],
  [
      ('Ngưỡng tỉ lệ nhìn thấy 0,85', '1/29', '10/143', '5,65 mm'),
      ('Nâng lên 0,90', '**0/29**', '12/143', '**3,42 mm**'),
      ('Thêm chặn trên 1,30 (bắt vùng to bất thường)', '0/29', '—', 'chặn được hai vật dính liền'),
      ('Thêm kiểm tra hình dáng', '0/29', '—', 'chặn được bàn tay và mảnh logo'),
  ],
  widths=[6.6, 2.4, 2.6, 4.4])

P('Việc nâng ngưỡng từ 0,85 lên 0,90 làm **tăng** số lần báo nhầm (10 → 12) nhưng **xóa hẳn** số '
  'lần bỏ sót (1 → 0) và giảm sai số lớn nhất từ 5,65 xuống 3,42 mm. Đây là một đánh đổi **có chủ '
  'ý và không đối xứng**: một lần bỏ sót khiến robot hút lệch tâm và làm đổ vật, còn một lần báo '
  'nhầm chỉ khiến hệ thống chờ thêm một khung hình.')

P('Tính chất thu được sau toàn bộ quá trình, và là mệnh đề đáng giá nhất của cả chương: **hễ hệ '
  'thống báo tin cậy thì sai số nằm trong dung sai gắp.** Đó là thứ biến một phép ước lượng thành '
  'một phép ước lượng **dùng được**.')

H3('4.7.3. Những phép khắc phục đã thử và bị bác bỏ')

P('Phần này ghi lại các hướng đã thử nhưng không giữ. Chúng có giá trị vì mỗi hướng bị bác bỏ đều '
  'thu hẹp không gian giải pháp và giải thích vì sao cách đang dùng là cách còn lại.')

T('4.10', ['Đã thử', 'Vì sao bác bỏ'],
  [
      ('Khớp mép trên cho vật trên bàn (mặt nạ màu)',
       'cho 5–12 mm so với 0,1–0,7 mm của mép đáy; mép trên của vùng MÀU bị nắp và vành nhãn làm '
       'nhòe khác nhau tùy khoảng cách'),
      ('Hạ ngưỡng tỉ lệ nhìn thấy để nhận được hai vật chạm nhau',
       'phá vỡ tính chất "hễ tin cậy thì trong dung sai"; mọi vật bị che một phần sẽ lọt'),
      ('Đo bề rộng bằng trung vị theo hàng, để né hàng dị thường do phản chiếu',
       'mặt nạ trừ nền có mép lởm chởm nên trung vị kéo vật LÀNH LẶN xuống −25 %; phá trường hợp '
       'thường gặp để cứu trường hợp hiếm'),
      ('Thuật toán PnP chuyên cho điểm mốc đồng phẳng',
       'sai số chiếu lại 434 điểm ảnh trên ảnh thật, dù đúng với dữ liệu tổng hợp'),
      ('Quét toàn dải phơi sáng và độ khuếch đại để cứu ngưỡng cố định',
       'hai kiểu hỏng ngược chiều nhau, không cấu hình nào thỏa mãn cả hai'),
      ('Dời tư thế quan sát để tránh che vật ở giữa',
       'phép đo cho thấy lỗi đi theo VẬT chứ không theo tư thế; nguyên nhân thật là ngưỡng tỉ lệ '
       'nhìn thấy đặt cho camera thật không hợp với mặt nạ màu'),
  ],
  widths=[6.6, 9.4])

H2('4.8. Đánh giá độ chính xác')

P('Bộ dữ liệu đánh giá trong mô phỏng gồm **172 ảnh** có vị trí thật biết trước, thu bằng cách '
  'dời vật qua lưới 61 điểm × 3 vật bằng dịch vụ đặt tư thế của trình mô phỏng, kèm các tình '
  'huống khó: robot lơ lửng sát vật ở bốn khe hở khác nhau, vật nằm trong khay, vật bị cắt mép '
  'ảnh. Phân tích chạy **ngoại tuyến** trên bộ dữ liệu đó, tái hiện đúng khâu nhận dạng của hệ '
  'thống chạy thật.')

IMG('4.7')

T('4.11', ['Điều kiện đánh giá', 'Trung bình', 'Phân vị 95', 'Lớn nhất'],
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

H3('4.8.1. Truy nguyên phần lệch hệ thống của camera thật')

P('Sai số 4,50 mm của camera thật gồm hai phần: **2,35 mm** tản mạn và khoảng **+9,6 mm** lệch hệ '
  'thống theo một hướng. Việc phần tản mạn nhỏ hơn hẳn phần lệch cho biết phép đo rất ổn định và '
  'phần dư là **lỗi mô hình**, không phải nhiễu — tức là có thể truy ra nguyên nhân.')

P('Giả thuyết đầu tiên là sai chiều cao vật. Giả thuyết này bị **bác bỏ bằng dấu của xu hướng**: '
  'sai chiều cao sinh ra lệch **tăng** theo khoảng cách (tính được: −13 → −19,8 mm), trong khi số '
  'liệu đo cho thấy lệch **giảm** (+12,5 / +12,4 / +3,9 mm tại ba khoảng cách). Hai xu hướng '
  'ngược chiều nhau nên giả thuyết sai, bất kể độ lớn có vẻ hợp lý.')

P('Đo riêng từng điểm mốc — bằng cách khớp tư thế từ các điểm mốc còn lại rồi giao tia với mặt '
  'bàn — cho thấy **hai điểm mốc lệch 26 mm và 29 mm** so với tọa độ thiết kế, làm sai số ngoại '
  'tham số tăng từ 0,93 lên 1,96 mm ảo. Cách khắc phục không cần bóc dán lại: chỉ cần **đo lại '
  'tọa độ thật của các điểm mốc và khai báo đúng** — điểm mốc không cần nằm đúng chỗ thiết kế, '
  'chỉ cần **biết đúng** chỗ nó nằm.')

H3('4.8.2. Ba cạm bẫy đo đạc')

P('Quá trình dựng và đánh giá hệ thống thật gặp ba cạm bẫy, đều là **lỗi của công cụ đo** chứ '
  'không phải của người đo, và cả ba đều suýt dẫn tới những can thiệp không cần thiết:')

N([
    '**Quy đổi chiều cao camera quên mặt bàn**, nên báo camera nằm dưới mặt bàn. Kiểm thử không '
    'bắt được vì nó so kết quả với chính hàm đang sai — hai vế cùng sai một kiểu thì vẫn khớp.',
    '**Hàm ước lượng tư thế từ một điểm mốc đơn lẻ cho kết quả sai** trên điểm mốc nhỏ nhìn xiên: '
    'báo hai điểm mốc lệch +65 mm, hai lần liên tiếp. Cách đo đúng là khớp tư thế bằng một nhóm '
    'điểm mốc đáng tin rồi giao tia với mặt bàn; làm vậy thì cả sáu điểm mốc nằm trong 8 mm.',
    '**Chấm điểm bằng đơn vị pixel là sai đơn vị.** Công cụ báo "sai số 3,25 px quá lớn" trong '
    'khi quy ra chỉ **0,93 mm ảo**, ngang mô phỏng. Cùng một sai số pixel ứng với số milimét khác '
    'hẳn tùy camera gần hay xa, nên ngưỡng phải đặt theo **milimét** và so với dung sai 12 mm.',
])

H2('4.9. Độ bền')

IMG('4.8')

T('4.12', ['Yếu tố', 'Mức chịu được', 'Mức bắt đầu hỏng'],
  [
      ('Nhiễu cảm biến (độ lệch chuẩn, mức xám)', '≤ 10: không ảnh hưởng',
       '20: còn 99,2 %; 40: còn 83 %'),
      ('Mức sáng (hệ số nhân)', '0,5 – 1,6: ổn định', '0,3: mất 16,5 % số lần nhận dạng'),
      ('Khoảng cách giữa hai vật cạnh nhau', '≥ 60 mm thật trên bàn, ≥ 80 mm trên băng tải',
       'chạm nhau: bị từ chối'),
      ('Camera xê dịch sau khi chụp ảnh nền', 'dưới 3 điểm ảnh',
       '8,7 điểm ảnh: nền trước vọt lên 17 %'),
  ],
  widths=[5.4, 5.6, 5.0])

P('Camera dùng trong đề tài đo được nhiễu cỡ **2,2 mức xám** — nằm sâu trong vùng an toàn. Con số '
  'này có ý nghĩa thực tiễn: nó cho biết phần đánh giá độ bền với nhiễu, vốn thực hiện bằng nhiễu '
  'nhân tạo thêm vào ảnh mô phỏng, **có mốc thực tế để đối chiếu**.')

P('Khoảng cách tối thiểu trên băng tải (80 mm) lớn hơn trên mặt bàn (60 mm), và lý do thuần túy '
  'hình học: hai vật cách nhau theo phương dọc băng thì cũng **cách camera xa gần khác nhau**, '
  'nên phối cảnh **nén** khoảng cách giữa chúng trong ảnh. Con số này được xác định bằng cách '
  'chiếu hình bóng dự đoán của hai vật qua mô hình camera đã hiệu chuẩn rồi đo khe giữa hai khung '
  'bao, chứ không ước lượng bằng mắt.')

IMG('4.9')

H2('4.10. Kết luận chương')

P('Chương 4 đã xây dựng hoàn chỉnh hệ thống thị giác:')

B([
    '**Mô hình camera và ràng buộc mặt phẳng** thay cho chiều đã mất khi chiếu, kèm cơ chế chọn '
    'giả thuyết tự nhất quán khi cảnh có nhiều mặt đỡ.',
    '**Hiệu chuẩn hai tầng** với quy ước đưa tọa độ ảo vào ngay từ khâu hiệu chuẩn — nhờ đó toàn '
    'bộ khối phía sau chạy nguyên trong hệ ảo khi chuyển từ mô phỏng sang thật.',
    '**Hai phương pháp tách vật cho hai thế giới**, và lý do khác nhau là một kết luận về bản '
    'chất bài toán: mặt nạ theo màu đo thiết kế nhãn, mặt nạ trừ nền đo vật.',
    '**Ước lượng bằng khớp hình bóng** với việc chọn đặc trưng theo tình huống, kèm phép tách '
    'vùng khi hai vật chạm nhau.',
    '**Bốn lớp phát hiện kết quả không đáng tin**, trong đó việc nhận ra tỉ lệ diện tích *về '
    'nguyên tắc* không bắt được vị trí sai là bước ngoặt dẫn tới ba lớp còn lại.',
    '**Quá trình giảm sai số** với bảy phép khắc phục chính, mỗi phép đều đo trước và sau trên '
    'cùng dữ liệu.',
    '**Sai số 1,13 mm trong mô phỏng và 4,50 mm trên camera thật**, đều nằm trong dung sai 12 mm '
    'của cơ cấu hút; và tính chất quan trọng hơn: hễ hệ thống báo tin cậy thì sai số ≤ 3,42 mm.',
])

P('Chương tiếp theo tích hợp hai nửa đã xây dựng — môi trường mô phỏng của Chương 3 và hệ thống '
  'thị giác của Chương 4 — thành một vòng kín, trong đó vật thể thật điều khiển robot mô phỏng và '
  'mô phỏng ra lệnh ngược lại cho thiết bị thật.')


# ================================================================== CHƯƠNG 5
H1('CHƯƠNG 5. TÍCH HỢP: BẢN SAO SỐ VÀ VÒNG ĐIỀU KHIỂN KHÉP KÍN')

P('Chương này ghép hai nửa đã xây dựng thành một hệ thống hoạt động: vật thể **thật** nằm trên '
  'bàn thật, robot **ảo** nằm trong mô phỏng, và camera là cầu nối duy nhất giữa chúng.')

IMG('5.1')

H2('5.1. Phân loại mức độ tích hợp')

P('Theo cách phân loại của Kritzinger đã trình bày ở Chương 1, quan hệ giữa một đối tượng thật và '
  'mô hình số của nó có ba mức, phân biệt bởi **chiều của luồng thông tin**:')

T('5.1', ['Mức', 'Luồng thông tin', 'Trong đề tài này'],
  [
      ('Mô hình số', 'không tự động, cập nhật thủ công',
       'giai đoạn đầu: vật ảo đặt cố định trong tệp mô tả cảnh'),
      ('Bóng số', 'tự động, **một chiều** thật → ảo',
       'camera đưa vị trí vật thật vào mô phỏng (mục 5.2)'),
      ('Bản sao số', 'tự động, **hai chiều**',
       'mô phỏng ra lệnh dừng băng tải thật (mục 5.4)'),
  ],
  widths=[3.0, 5.4, 7.6])

P('Việc nêu rõ phân loại này không phải hình thức: nó xác định **điều gì còn thiếu** để hệ thống '
  'đạt mức cao nhất, và trong đề tài này điều còn thiếu chính là chiều ngược — mô phỏng phải điều '
  'khiển được một thiết bị thật. Băng tải được thêm vào chính để đóng chiều đó.')

H2('5.2. Đồng bộ vị trí vật thể')

P('Mối nối giữa hai thế giới mỏng hơn nhiều so với dự kiến ban đầu, và đó là kết quả của quyết '
  'định ở mục 4.2.3: khối thị giác **đã phát tọa độ trong hệ ảo sẵn**, vì tọa độ ảo được đưa vào '
  'bài toán PnP ngay từ khâu hiệu chuẩn. Ở tầng tích hợp này chỉ còn một phép cộng cao độ đế '
  'robot — **không có phép đổi tỉ lệ nào**.')

IMG('5.2')

P('Nút đồng bộ **từ chối làm bốn việc**, và mỗi điều từ chối đều xuất phát từ một lỗi đã gặp:')

N([
    '**Bỏ qua vật có cờ tin cậy bằng 0.** Không có điều này thì mọi ước lượng xấu đều được ghi '
    'thẳng vào mô phỏng.',
    '**Chỉ ghi khi vật thật dịch quá 6 mm thật.** Dưới mức đó để bộ giải vật lý tự lo, thay vì '
    'ghi đè vị trí mười lần mỗi giây — ghi đè liên tục làm vật ảo không bao giờ được phép rơi, va '
    'chạm hay nằm yên theo quy luật vật lý.',
    '**Không đụng tới vật mà cơ cấu hút đang giữ.** Vật đang lơ lửng thì camera không đo được '
    '(nó giả định vật đứng trên mặt phẳng), nên mọi ước lượng lúc đó đều vô nghĩa.',
    '**Không ghi một bước nhảy xa nếu chưa được xác nhận.** Chi tiết ở mục 5.3.',
])

T('5.2', ['Nội dung kiểm chứng', 'Kết quả'],
  [
      ('Vật ảo so với vị trí camera báo', '**0,0 – 0,4 mm ảo**'),
      ('Cao độ vật ảo', 'đúng độ cao vật đứng trên bàn, không rơi, không lún'),
      ('Dời vật thật hơn 100 mm', 'vật ảo bám theo trong **1 mm thật = 0,3 mm ảo**'),
      ('Khởi động lại hệ thống', 'vật ảo tự đồng bộ từ vị trí khai báo về vị trí thật'),
  ],
  widths=[7.0, 9.0])

H2('5.3. Hai lớp phòng vệ chống dịch chuyển giả')

P('Khi chạy thật, hiện tượng đầu tiên gặp phải là vật ảo **nhảy 294 mm rồi quay về**. Truy nguyên '
  'cho thấy nguyên nhân không phải thứ nghi ngờ ban đầu, và quá trình truy nguyên đó đáng ghi lại.')

P('Nghi ngờ đầu tiên là **bàn tay người** vào dời vật: tay có sắc màu ngả đỏ cam nên rơi vào lớp '
  'màu của một trong ba vật. Thêm chặn trên cho tỉ lệ nhìn thấy đã bắt được một phần, nhưng thử '
  'lại bằng cách giơ tay vào khung thì vật ảo **vẫn nhảy 284 mm trong khi cờ tin cậy báo 1,00** — '
  'đúng như phân tích ở mục 4.6.1 đã dự đoán.')

P('Nguyên nhân thật là **vành logo đỏ của một vật khác**: khi vùng ảnh của vật đó bị cắt thành '
  'nhiều mảnh, mảnh vành logo thành vùng riêng, được phân loại là đỏ, và khâu chọn lấy **vùng đỏ '
  'lớn nhất** nên vật đỏ bị "dịch chuyển tức thời" sang chỗ vật kia, lặp đi lặp lại.')

P('Hai lớp phòng vệ được thêm, và chúng có **phân công rõ ràng**:')

B([
    '**Lớp hình dáng** (mục 4.6.2) nói *"không biết vật ở đâu"* — thà không báo gì còn hơn báo sai '
    'chỗ.',
    '**Lớp xác nhận nhiều khung** nói *"chỗ mới phải trụ lại đã"* — dựa vào ràng buộc vật lý mà '
    'không phép khớp nào lách được.',
])

P('Kiểm chứng bằng cách **gây nhiễu có chủ ý**: đưa tay vào khung hình và dời vật nhiều lần.')

T('5.3', ['Quan sát trong cùng một lượt chạy', 'Kết quả'],
  [
      ('Số lần vật ảo dịch chuyển giả', '**0**'),
      ('Số khung bị lớp hình dáng loại bỏ', '25 (vật bị tay che)'),
      ('Số khung bị giữ lại chờ xác nhận', '12'),
      ('Chuyển động THẬT trong cùng khoảng thời gian', '177 mm và 170 mm — **cả hai đều tới nơi**'),
  ],
  widths=[9.0, 7.0])

P('Dòng cuối của bảng quan trọng ngang ba dòng trên. Một lớp phòng vệ chỉ đáng tin khi nó **vừa '
  'chặn được cái sai vừa không chặn nhầm cái đúng** — nếu chỉ chứng minh vế đầu thì việc tắt hẳn '
  'hệ thống cũng cho kết quả y hệt.')

H2('5.4. Băng tải: đóng chiều ngược của vòng điều khiển')

P('Băng tải được thêm vào theo gợi ý của giảng viên hướng dẫn, với hai lý do. Thứ nhất, nó làm '
  'kịch bản giống dây chuyền sản xuất thật hơn là dùng tay dời vật. Thứ hai — và quan trọng hơn '
  'về mặt học thuật — nó cho **mô phỏng ra lệnh cho một thiết bị thật**, đưa hệ thống từ mức '
  '*bóng số* lên mức *bản sao số* đầy đủ.')

T('5.4', ['Thông số băng tải', 'Giá trị đo được'],
  [
      ('Tốc độ (đã chạy hết khả năng động cơ)', '16 mm/s thật'),
      ('Quãng trôi sau khi ra lệnh dừng', '**3 mm**'),
      ('Điểm gắp, đo khi vật TỰ CHẠY tới', '+90,2 mm (so với +82,1 mm khi đặt bằng tay)'),
      ('Khoảng cách tối thiểu giữa hai vật', '80 mm thật (vừa 3 vật trên băng)'),
      ('Thời gian hết hạn lệnh chạy', '3 s'),
  ],
  widths=[8.0, 8.0])

P('Hai con số trong bảng cần giải thích vì chúng dẫn tới quyết định thiết kế:')

B([
    '**Quãng trôi chỉ 3 mm** đã bác bỏ một giả định ban đầu của chính tác giả, rằng cần một pha '
    'giảm tốc trước khi dừng để vật không đổ vì quán tính. Ở tốc độ 16 mm/s, quán tính không đáng '
    'kể và phép dừng thẳng là đủ. Đây là ví dụ cho việc **đo trước khi thiết kế**.',
    '**Điểm gắp lệch 8 mm** giữa cách đo đặt tay và cách đo để vật tự chạy tới. Số đo đặt tay mô '
    'tả một vị trí mà **vật đang chạy không bao giờ ở đó**, vì nó không tính quãng trôi.',
])

H3('5.4.1. Lưới an toàn của lệnh chạy')

P('Lệnh cho băng chạy được thiết kế **không phải là một công tắc bật-và-quên**, mà là một **lời '
  'khẳng định có hạn dùng**: máy tính phải nhắc lại lệnh ít nhất mỗi 3 giây, nếu không băng tự '
  'dừng.')

P('Lý do là an toàn chức năng. Nếu máy tính treo, cáp tuột, hay phần mềm điều khiển chết, sẽ không '
  'ai gửi lệnh nữa và băng **tự dừng**. Một băng tải tiếp tục chạy vì phần mềm điều khiển đã chết '
  'là trạng thái không được phép tồn tại, và đây là cách rẻ nhất để loại bỏ nó — không cần nút '
  'dừng khẩn cấp, không cần cảm biến.')

H2('5.5. Máy trạng thái của vòng làm việc')

P('Vòng làm việc hoàn chỉnh được mô tả bằng một máy trạng thái sáu trạng thái.')

IMG('5.3')

P('Năm trạng thái đầu là trình tự hiển nhiên. Trạng thái thứ sáu — **nhả quyền** — mới là chỗ khó '
  'duy nhất của cả vòng, và nó không hiện ra cho tới khi hệ thống chạy thật.')

H3('5.5.1. Bài toán bàn giao quyền quyết định vị trí')

P('Khi robot ảo đã gắp vật và bỏ vào khay, **vật thật vẫn còn nằm trên băng tải**. Bản sao số thì '
  'bám camera. Nếu không làm gì, nó sẽ kéo vật ảo từ trong khay về lại mặt băng — **mười lần mỗi '
  'giây** — tức là xóa sạch việc robot vừa làm, nhanh đúng bằng tốc độ robot làm.')

P('Cách giải: quyền quyết định vị trí vật phải **tạm chuyển sang mô phỏng** đúng lúc bắt đầu gắp, '
  'và chỉ **nhận lại khi thế giới thật đã đồng bộ** — tức khi tay người đã nhấc vật thật ra khỏi '
  'băng.')

P('Giảng viên hướng dẫn diễn đạt yêu cầu này là *"tắt camera thực tế"*. Khi thực hiện thì chính '
  'xác hơn một chút, và sự khác biệt có ý nghĩa: **không tắt camera** — còn phải tiếp tục nhìn, '
  'vì **nhìn chính là cách biết được vật thật đã được nhấc đi hay chưa**. Thứ bị tạm ngừng là '
  'quyền *ghi* vị trí, không phải việc *quan sát*.')

P('Hai bất biến mà máy trạng thái này bảo đảm:')

N([
    '**Không bao giờ có hai nguồn cùng ghi vị trí một vật.** Vật đang gắp thì chỉ mô phỏng ghi; '
    'vật trên băng thì chỉ camera ghi.',
    '**Không nhận vật mới khi vật vừa gắp chưa được dọn khỏi băng.** Ràng buộc này chỉ áp cho '
    'đúng vật đó, không áp cho cả mặt băng — nên đặt nhiều vật cùng lúc vẫn hợp lệ.',
])

H3('5.5.2. Robot bám theo vật trong suốt hành trình')

P('Một cải tiến so với thiết kế ban đầu: thay vì đứng chờ ở cuối băng, robot **đưa đầu hút lên '
  'trên nắp vật trước**, và băng chỉ chạy khi đầu hút đã vào vị trí; sau đó đầu hút **bám theo '
  'vật suốt hành trình**. Khi băng dừng thì hút được ngay, không mất thêm quãng đi.')

P('Việc bám đuổi đòi hỏi một cơ chế điều khiển khác với việc đi tới một điểm: lập trọn quỹ đạo '
  'rồi chạy là đúng cho *"đi tới đó"* nhưng sai cho *bám đuổi*, vì đích đổi ngay trong lúc đang '
  'đi. Mỗi nhịp chỉ kéo vị trí lệnh về phía đích một đoạn có giới hạn, và chính giới hạn tốc độ '
  'đó tạo ra chuyển động mượt.')

P('Một lỗi đã gặp ở đây, thuần túy số học nhưng hậu quả rõ rệt: nhịp bám ban đầu được gọi theo '
  'nhịp của máy trạng thái (0,3 s), trong khi mỗi lần gọi chỉ nhích 1 mm — tức **3,3 mm/s ảo, '
  'chậm hơn cả tốc độ vật trên băng**, nên robot không bao giờ đuổi kịp và chuyển động giật từng '
  'nấc. Tách hai nhịp ra (bám 50 Hz, quyết định 0,3 s) đưa tốc độ bám lên 50 mm/s ảo. Hai nhịp '
  'này **không liên quan gì nhau**: một bên hỏi *"giờ phải làm gì"*, bên kia chỉ kéo robot về '
  'phía đích.')

H2('5.6. Kết luận chương')

P('Chương 5 đã ghép hệ thống thành một vòng hoàn chỉnh:')

B([
    '**Đồng bộ vị trí** với mối nối chỉ gồm một phép cộng cao độ, nhờ quy ước tỉ lệ đặt từ khâu '
    'hiệu chuẩn.',
    '**Hai lớp phòng vệ** chống dịch chuyển giả, kiểm chứng bằng gây nhiễu có chủ ý: 0 lần dịch '
    'chuyển giả, trong khi hai chuyển động thật 177 và 170 mm đều được ghi nhận.',
    '**Băng tải** đưa hệ thống từ mức bóng số lên mức bản sao số đầy đủ, kèm lưới an toàn dạng '
    'lời khẳng định có hạn dùng.',
    '**Máy trạng thái sáu trạng thái** với cơ chế bàn giao quyền quyết định vị trí — ý tưởng kỹ '
    'thuật cốt lõi của chương.',
    '**Robot bám theo vật** suốt hành trình băng, chuẩn bị sẵn cơ chế cho bài toán gắp khi đang '
    'chạy.',
])


# ================================================================== CHƯƠNG 6
H1('CHƯƠNG 6. KẾT QUẢ, ĐÁNH GIÁ VÀ KẾT LUẬN')

IMG('6.1')

H2('6.1. Đối chiếu mục tiêu và kết quả')

T('6.1', ['Mục tiêu đề ra', 'Kết quả đạt được', 'Đánh giá'],
  [
      ('Xây dựng mô hình động học robot delta',
       'công thức dạng đóng cho cả hai chiều; vòng lặp ngược–thuận trên 5 424 điểm sai lệch '
       '~1e−13 m', 'đạt'),
      ('Mô phỏng robot tương tác được với vật thể',
       'va chạm vật lý, cơ cấu hút, kiểm chứng bằng đo đạc sau mỗi thao tác', 'đạt'),
      ('Nhận dạng và định vị vật bằng thị giác',
       '1,13 mm (mô phỏng) · 4,50 mm (camera thật), so với dung sai 12 mm', 'đạt'),
      ('Dùng tín hiệu camera THẬT điều khiển robot mô phỏng',
       'bản sao số: vật ảo bám vật thật trong 0,3 mm ảo', 'đạt'),
      ('Gắp–thả tự động dựa trên thị giác',
       '15/15 vật vào đúng khay trên 5 bố trí ngẫu nhiên', 'đạt'),
      ('Tăng tính ứng dụng (yêu cầu bổ sung)',
       'băng tải thật do mô phỏng điều khiển; vòng làm việc khép kín', 'đạt'),
  ],
  widths=[4.6, 7.4, 2.4])

H2('6.2. Các kết quả chính')

H3('6.2.1. Về độ chính xác')

P('Sai số định vị **1,13 mm** trong mô phỏng và **4,50 mm** trên camera thật, so với dung sai '
  '**12 mm** của cơ cấu hút. Quan trọng hơn con số trung bình là tính chất: **hễ hệ thống báo tin '
  'cậy thì sai số không vượt 3,42 mm** — nghĩa là một kết quả được chấp nhận thì chắc chắn gắp '
  'được, còn kết quả không chắc thì bị từ chối chứ không được dùng bừa.')

P('Chênh lệch giữa hai môi trường (1,13 so với 4,50 mm) đã được truy nguyên: phần tản mạn chỉ '
  '**2,35 mm**, phần còn lại là lệch hệ thống do sai số vị trí điểm mốc hiệu chuẩn — tức là một '
  'nguyên nhân **đã xác định và khắc phục được**, không phải giới hạn của phương pháp.')

H3('6.2.2. Về độ tin cậy')

P('Trên 5 bố trí ngẫu nhiên: **15/15 vật** vào đúng khay, **15/15 vật** trả về đúng chỗ cũ, '
  'không lượt nào thất bại. So sánh then chốt: chế độ dùng camera cho kết quả **bằng đúng** chế '
  'độ dùng vị trí thật từ mô phỏng (30/30 ở cả hai), chỉ chậm hơn khoảng 35 % do phải dừng lại '
  'quan sát. Nói cách khác, **thay nguồn vị trí lý tưởng bằng camera không làm mất tỉ lệ thành '
  'công nào**.')

H3('6.2.3. Về quá trình giảm sai số')

P('Bảy phép khắc phục chính đã giảm sai số từ mức 13–76 mm xuống mức 0,3–4,5 mm (Bảng 4.8). Đặc '
  'điểm chung đáng nêu: **không phép nào là cải tiến thuật toán nhận dạng**; tất cả đều là sửa '
  'một giả định sai về hình học hoặc về thời gian. Đây là nhận xét có giá trị thực tiễn cho các '
  'hệ thống thị giác ứng dụng.')

H3('6.2.4. Về chất lượng phần mềm')

P('201 trường hợp kiểm thử tự động chạy trong khoảng 3 giây, **không cần mô phỏng, camera hay '
  'robot**. Điều này có được nhờ một quyết định kiến trúc: phần lớn mã nghiệp vụ — động học, quỹ '
  'đạo, lập kế hoạch tác vụ, máy trạng thái, ước lượng thị giác — **không phụ thuộc ROS**, nên '
  'kiểm thử được độc lập. Mọi hằng số của cảnh khai báo tại một nơi duy nhất, nhờ đó việc băng '
  'tải thật chạy ngược chiều dự kiến được xử lý bằng cách sửa **một con số**.')

H2('6.3. Giới hạn của hệ thống')

P('Phần này nêu các giới hạn đã biết. Việc nêu rõ chúng quan trọng không kém việc nêu kết quả: '
  'một giới hạn được xác định và đo đạc là thông tin kỹ thuật, còn một giới hạn bị giấu đi sẽ trở '
  'thành lỗi bất ngờ khi vận hành.')

T('6.2', ['Giới hạn', 'Biểu hiện', 'Hướng khắc phục'],
  [
      ('Giả định "mỗi màu một vật"',
       'không phân biệt được hai vật cùng màu',
       'chuyển từ danh sách vật cố định sang "N thực thể phát hiện được"; cần sửa cả chuỗi xử lý'),
      ('Hai vật chạm nhau trong ảnh',
       'bị từ chối (tỉ lệ nhìn thấy 0,71–0,80)',
       'điều kiện vận hành: đặt cách nhau ≥ 60 mm trên bàn, ≥ 80 mm trên băng'),
      ('Ảnh nền gắn với vị trí camera và ánh sáng',
       'camera xê dịch 8,7 px làm hỏng mặt nạ',
       'đã có cảnh báo tự động; chụp lại ảnh nền khi cần'),
      ('Camera đơn cần biết trước mặt đỡ',
       'không đo được chiều cao vật',
       'đo chiều cao bằng bài toán ngược của phép khớp mép trên (chưa làm)'),
      ('Bộ giải va chạm lún vào vật động',
       'bàn máy lún 5–8 mm nếu ép xuống quá đỉnh vật',
       'đã tránh bằng ràng buộc điều khiển; nguyên nhân chưa kiểm chứng'),
      ('Tốc độ băng tải đã hết khả năng động cơ',
       '16 mm/s, không tăng được nữa',
       'đổi puly/hộp số hoặc nâng điện áp nguồn'),
  ],
  widths=[4.0, 5.0, 7.0])

H2('6.4. Hướng phát triển')

N([
    '**Đo chiều cao vật bằng camera đơn** — bài toán ngược của phép khớp mép trên: đáy vật trên '
    'mặt phẳng đã biết cho tọa độ ngang, mép trên cho chiều cao. Mở ra khả năng phân biệt vật '
    'cùng màu nhưng khác kích thước.',
    '**Gắp khi vật đang chạy** — cơ chế bám theo vật đã có sẵn (mục 5.5.2); chỉ cần bỏ bước dừng '
    'băng và bù trễ của chuỗi nhận thức.',
    '**Nhiều vật cùng màu** — thay giả định "mỗi màu một vật" bằng danh sách thực thể động. Đây '
    'là thay đổi lớn nhất còn lại, ảnh hưởng tới cả khâu nhận dạng, lập kế hoạch và cơ cấu hút.',
    '**Hiệu chuẩn lại điểm mốc** — đo lại tọa độ thật của sáu điểm mốc để xóa phần lệch hệ thống '
    '+9,6 mm, đưa sai số camera thật về gần mức 2,35 mm đã đo được.',
    '**Bù trễ** — đo độ trễ đầu-cuối của chuỗi nhận thức rồi dự đoán vị trí vật tại thời điểm '
    'robot tới nơi, thay vì tại thời điểm chụp ảnh.',
])

H2('6.5. Kết luận')

P('Đề tài đã xây dựng hoàn chỉnh một hệ thống trong đó **tín hiệu từ camera thật điều khiển robot '
  'delta trong môi trường mô phỏng**, với đầy đủ các khâu: mô hình động học, môi trường mô phỏng '
  'có tương tác vật lý, hệ thống thị giác máy tính, bản sao số và vòng điều khiển khép kín có '
  'thiết bị thật.')

P('Về mặt kỹ thuật, kết quả đáng kể nhất không phải con số sai số mà là **cơ chế tự đánh giá độ '
  'tin cậy**. Hệ thống không chỉ đưa ra vị trí mà còn đưa ra mức độ chắc chắn của nó, và lớp điều '
  'khiển từ chối hành động trên thông tin không đáng tin. Bốn lớp phòng vệ được xây dựng lần '
  'lượt, mỗi lớp ra đời từ một lỗi thật đã quan sát được, và chúng bắt những loại lỗi khác hẳn '
  'nhau — trong đó việc nhận ra rằng **tỉ lệ diện tích về nguyên tắc không thể phát hiện vị trí '
  'sai** là bước ngoặt của toàn bộ phần thị giác.')

P('Về mặt phương pháp, đề tài cho thấy giá trị của việc **đo trước khi thiết kế** và **đo lại sau '
  'khi sửa**. Nhiều giả định ban đầu đã bị chính số liệu bác bỏ: pha giảm tốc cho băng tải hóa ra '
  'không cần, mép đáy *trông* chính xác hơn mép trên chỉ vì hai sai số triệt tiêu nhau, và một '
  'giả thuyết về che khuất bị bác bỏ bằng **dấu của xu hướng** chứ không phải bằng độ lớn. Nếu '
  'chỉ dựa vào suy luận mà không đo, phần lớn những điều đó sẽ đi vào hệ thống dưới dạng lỗi khó '
  'tìm.')

S.save()
