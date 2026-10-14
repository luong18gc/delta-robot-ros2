#!/usr/bin/env python3
"""
Dựng khóa luận (bản 2) — Chương 3 và Chương 4, thành một tệp riêng.

    python3 docs/tools/build_thesis_v2_ch34.py

Định dạng dùng chung với Chương 1–2 qua `thesis_style.py`. Hình sinh bằng
`make_thesis_figures_ch34.py` từ hằng số thật trong mã nguồn.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import omml as m                                                   # noqa: E402
import thesis_style as S                                           # noqa: E402
from thesis_style import B, EQ, H1, H2, H3, IMG, N, P, T           # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Khoa_luan_v2_ch34.docx')

FIGURES = [
    ('3.1', 'Mô hình URDF chỉ mô tả được cấu trúc cây; mạch kín được đóng lúc chạy bằng các khớp '
            'tháo rời được', 'kl34_mach_kin.png', 15.5),
    ('3.2', 'Bố trí cảnh mô phỏng nhìn từ trên xuống, với tầm với của robot, băng tải, ba khay '
            'phân loại và hướng nhìn của camera', 'kl34_bo_tri_canh.png', 13.5),
    ('3.3', 'Cửa sổ dung sai cho phép hút thành công', 'kl34_cua_so_hut.png', 13.5),
    ('3.4', 'Đồ thị các nút và chủ đề ROS 2 của hệ thống', 'ros_graph.png', 15.5),
    ('4.1', 'Từ điểm ảnh về tọa độ ba chiều bằng phép giao tia với mặt phẳng đã biết cao độ',
     'kl34_mo_hinh_camera.png', 15.0),
    ('4.2', 'Sáu điểm mốc ArUco dùng cho hiệu chuẩn ngoại tham số',
     'calibration_markers.png', 14.0),
    ('4.3', 'So sánh mặt nạ thu được bằng ngưỡng màu cố định và bằng phép trừ ảnh nền',
     'foreground_comparison.png', 15.0),
    ('4.4', 'Vì sao phải khớp mép trên khi mặt bàn phản chiếu', 'kl34_khop_mep.png', 15.0),
    ('4.5', 'Bốn lớp phòng vệ và loại lỗi mà mỗi lớp phát hiện được',
     'kl34_lop_phong_ve.png', 15.0),
    ('4.6', 'Phân bố sai số định vị trên mặt bàn trong mô phỏng',
     'vision_error_map.png', 15.0),
    ('4.7', 'Độ bền của khâu nhận dạng với nhiễu cảm biến và với mức sáng',
     'vision_robustness.png', 15.0),
    ('4.8', 'Kết quả nhận dạng trên camera thật: vùng xét giới hạn theo hình học và ba vật đã '
            'được định vị', 'real_camera_detections.png', 15.0),
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
    ('4.3', 'So sánh hai phương pháp tách vật trên cùng một khung hình camera thật'),
    ('4.4', 'Đặc trưng hình học dùng để khớp hình bóng theo từng tình huống'),
    ('4.5', 'Bốn lớp phát hiện kết quả không đáng tin'),
    ('4.6', 'Sai số định vị của hệ thống thị giác'),
    ('4.7', 'Độ bền của khâu nhận dạng'),
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

IMG('3.4')

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

P('Chương này trình bày khâu thị giác: từ ảnh của một camera đơn, xác định chủng loại và vị trí '
  'ba chiều của vật thể trong hệ tọa độ của robot, kèm theo một đánh giá về **mức độ đáng tin** '
  'của từng kết quả.')

P('Yêu cầu định lượng đã được xác định ở Chương 3: sai số định vị phải nhỏ hơn **12 mm** trong hệ '
  'ảo. Nhưng một yêu cầu thứ hai, định tính, hóa ra khó hơn và quan trọng hơn: hệ thống phải **tự '
  'biết khi nào mình không chắc**. Một ước lượng sai mà được tin tưởng thì nguy hiểm hơn hẳn một '
  'ước lượng bị từ chối.')

H2('4.1. Mô hình camera và bài toán định vị')

P('Camera được mô hình hóa theo mô hình lỗ kim. Một điểm trong không gian, biểu diễn trong hệ tọa '
  'độ của robot, trước hết được đưa về hệ tọa độ camera:')

EQ(sq(sb(v('X'), v('c')), o('='), v('R'), sb(v('X'), v('r')), o('+'), v('t')), '4.1')

P('rồi chiếu lên mặt phẳng ảnh bằng ma trận nội tham số:')

EQ(sq(v('s'), mx([[v('u')], [v('v')], [nn(1)]]), o('='), v('K'), sb(v('X'), v('c')),
      o(','), txt('   '), v('K'), o('='),
      mx([[sb(v('f'), v('x')), nn(0), sb(v('c'), v('x'))],
          [nn(0), sb(v('f'), v('y')), sb(v('c'), v('y'))],
          [nn(0), nn(0), nn(1)]])), '4.2')

P('Trong đó **R** và **t** là ngoại tham số — vị trí và hướng của camera so với robot; **K** là '
  'nội tham số — tiêu cự và tâm ảnh của chính thiết bị.')

P('Phép chiếu này làm **mất một chiều**: mọi điểm nằm trên cùng một tia đều cho cùng một điểm '
  'ảnh. Camera đơn vì vậy không đủ để xác định vị trí ba chiều, trừ khi có thêm một ràng buộc.')

IMG('4.1')

P('Ràng buộc ở đây đến từ hình học của cảnh: **vật đứng trên một mặt phẳng đã biết cao độ**. Khi '
  'đó tâm vật nằm ở cao độ bằng cao độ mặt đỡ cộng nửa chiều cao vật, và giao tia nhìn với mặt '
  'phẳng đó cho ra tọa độ ngang:')

EQ(sq(sb(v('X'), v('r')), o('='), sp(v('R'), txt('T')),
      dl(sq(v('λ'), sp(v('K'), txt('−1')), mx([[v('u')], [v('v')], [nn(1)]]), o('−'), v('t'))),
      o(','), txt('   '), v('λ'), txt(' sao cho '), sb(v('z'), v('r')), o('='),
      sb(v('z'), txt('đỡ')), o('+'), fr(v('h'), nn(2))), '4.3')

P('Giả thiết "vật đứng trên mặt phẳng đã biết" là hợp lệ trong bài toán này và cũng là giả thiết '
  'được dùng rộng rãi trong các hệ thống gắp–thả công nghiệp dùng camera đơn. Khi cảnh có **hai** '
  'mặt đỡ ở hai cao độ khác nhau — mặt bàn và mặt băng tải — hệ thống xét cả hai giả thiết và '
  'chọn giả thiết **tự nhất quán**: giả thiết "vật đứng trên băng" chỉ được chấp nhận nếu vị trí '
  'suy ra từ nó thật sự rơi vào phạm vi mặt băng.')

P('Tầm quan trọng của việc chọn đúng mặt đỡ lớn hơn vẻ ngoài. Đo trên cùng một khung hình: giả '
  'thiết mặt bàn cho (+167; +13) mm, giả thiết mặt băng cho (+91; +14) mm. Chênh **76 mm** chỉ vì '
  'sai 50 mm cao độ — vì camera nhìn chúc, sai số theo chiều cao bị khuếch đại khi chiếu xuống '
  'mặt phẳng.')

H2('4.2. Hiệu chuẩn')

P('Hiệu chuẩn chia làm hai bài toán độc lập, và việc tách rời chúng là có chủ ý.')

H3('4.2.1. Nội tham số')

P('Nội tham số gắn với **thiết bị cụ thể**, kể cả hai máy cùng kiểu, nên phải đo riêng và chỉ cần '
  'đo một lần. Phương pháp dùng bàn cờ phẳng chụp ở nhiều tư thế. Kết quả cho camera dùng trong '
  'đề tài: tiêu cự 1417,4 điểm ảnh, sai số chiếu lại **0,222 điểm ảnh**.')

H3('4.2.2. Ngoại tham số')

P('Ngoại tham số là tư thế camera so với robot. Phương pháp dùng sáu điểm mốc ArUco dán trên mặt '
  'bàn tại các tọa độ đã biết; bài toán xác định tư thế từ các cặp điểm–ảnh là bài toán PnP.')

IMG('4.2')

P('Hai chi tiết kỹ thuật đã phải xử lý, và cả hai đều chỉ lộ ra trên ảnh thật:')

B([
    '**Cách lấy tâm điểm mốc.** Lấy trung bình bốn góc cho kết quả lệch khi nhìn xiên, vì phép '
    'chiếu phối cảnh không bảo toàn trung điểm. Phải lấy **giao điểm hai đường chéo** — đại lượng '
    'mà phép chiếu phối cảnh bảo toàn.',
    '**Thuật toán giải PnP.** Một thuật toán thường dùng cho điểm mốc phẳng cho nghiệm sai hẳn '
    'trên ảnh thật (sai số chiếu lại 434 điểm ảnh) dù vẫn đúng với dữ liệu tổng hợp. Phải thay '
    'bằng thuật toán tổng quát kèm bước tinh chỉnh phi tuyến.',
])

T('4.1', ['Đại lượng', 'Camera mô phỏng', 'Camera thật'],
  [
      ('Sai số chiếu lại khi hiệu chuẩn', '0,14 điểm ảnh', '0,222 điểm ảnh (nội tham số)'),
      ('Sai lệch vị trí camera', '0,35 mm', '—'),
      ('Sai lệch hướng nhìn', '0,017°', '—'),
      ('Sai số ngoại tham số quy ra hệ ảo', '—', '0,93 mm'),
      ('Góc chúc', '32°', '46,1°'),
  ],
  widths=[6.4, 4.8, 5.6])

P('Góc chúc thật khác hẳn mô phỏng vì bàn không đủ dài để đặt camera lùi xa hơn. Khối thị giác '
  '**tự thích nghi** vì nó dùng mô hình camera đo được chứ không giả định góc; góc dốc hơn thậm '
  'chí có lợi cho việc chống che khuất.')

H3('4.2.3. Quy ước tỉ lệ trong hiệu chuẩn')

P('Chương 3 đã đặt ra hệ số tỉ lệ k = 3. Câu hỏi là áp dụng nó ở đâu. Lựa chọn trong đề tài là '
  'đưa **tọa độ ảo** vào bài toán PnP ngay từ khâu hiệu chuẩn, thay vì hiệu chuẩn theo milimét '
  'thật rồi chia kết quả về sau.')

P('Cơ sở: thu nhỏ toàn bộ thế giới k lần chỉ làm **vectơ tịnh tiến của camera chia cho k**; ma '
  'trận nội tham số, hệ số méo và bản thân phép chiếu đều không đổi. Nhờ vậy toàn bộ khối thị '
  'giác phía sau — phép giao tia, hình bóng dự đoán, mặt bàn, khay — chạy nguyên trong hệ ảo mà '
  '**không phải sửa một dòng nào**. Đây là lý do mối nối giữa thế giới thật và mô phỏng ở Chương '
  '5 mỏng tới mức chỉ còn một phép cộng cao độ đế robot.')

H2('4.3. Tách vật thể khỏi nền')

P('Khâu đầu tiên của đường ống xử lý là xác định những vùng ảnh nào thuộc về vật thể. Đề tài đã '
  'dùng **hai phương pháp khác nhau cho hai thế giới**, và đó là một kết luận chứ không phải một '
  'chắp vá.')

H3('4.3.1. Phân ngưỡng theo màu')

P('Phương pháp đầu tiên: chuyển ảnh sang không gian HSV rồi phân ngưỡng theo lớp màu. Không gian '
  'HSV tách riêng sắc màu khỏi độ sáng nên bền với bóng đổ hơn không gian RGB.')

T('4.2', ['Lớp màu', 'Sắc màu H', 'Độ bão hòa S', 'Độ sáng V'],
  [
      ('Đỏ', '[0; 8] ∪ [172; 180]', '≥ 90', '≥ 40'),
      ('Lục', '[45; 85]', '≥ 90', '≥ 40'),
      ('Lam', '[95; 125]', '≥ 90', '≥ 40'),
  ],
  widths=[3.6, 5.6, 3.4, 3.4])

P('Ngưỡng độ bão hòa loại được mặt bàn và thành khay. Ngưỡng độ sáng tưởng như thừa nhưng lại là '
  'ngưỡng quan trọng nhất khi mặt bàn màu tối: do cách định nghĩa ' +
  'S = (max − min)/max, **điểm ảnh tối có độ bão hòa cao giả tạo**. Đo trên ảnh thật, trong vùng '
  'tối có tới 85 % điểm ảnh vượt ngưỡng bão hòa. Với nền tối, thứ loại được mặt bàn chính là '
  'ngưỡng độ sáng.')

H3('4.3.2. Vì sao ngưỡng cố định không bền')

P('Trên camera thật, bộ ngưỡng cố định thất bại theo **hai kiểu ngược nhau** tùy ánh sáng:')

N([
    '**Ban ngày**: mặt bàn sáng lên và ám màu, nên lọt vào mặt nạ.',
    '**Thắp một đèn**: mặt bàn quá tối, độ bão hòa hóa nhiễu, và gần như **cả mặt bàn** lọt vào.',
])

P('Quét toàn dải phơi sáng và độ khuếch đại của camera đều không cứu được cả hai trường hợp cùng '
  'lúc. Vấn đề không nằm ở việc chọn ngưỡng nào, mà ở **bản thân ý tưởng dùng ngưỡng cố định cho '
  'một đại lượng phụ thuộc ánh sáng**.')

H3('4.3.3. Trừ ảnh nền')

P('Giải pháp là so ảnh hiện tại với **ảnh mặt bàn trống** chụp trước đó: điểm ảnh nào khác ảnh '
  'nền quá một ngưỡng thì thuộc về vật. Đại lượng được so là **sự thay đổi**, không phải giá trị '
  'tuyệt đối, nên nó không phụ thuộc vào mức sáng chung.')

IMG('4.3')

P('Hiệu quả rất rõ: trên cảnh không có vật, cách lấy ngưỡng báo 12,06 % diện tích ảnh là "vật", '
  'còn phép trừ nền báo **0,00 %**; trong khi nhiễu cảm biến chỉ cỡ 1 mức xám so với ngưỡng 30.')

P('Cái giá phải trả là ảnh nền **gắn cứng với vị trí camera và với điều kiện chiếu sáng**. Camera '
  'xê dịch chỉ 8,7 điểm ảnh đã làm mọi đường biên trong cảnh lọt vào mặt nạ, tỉ lệ nền trước vọt '
  'từ gần 0 lên 17 %, và sinh ra những vùng giả lớn hơn cả vật thật. Vì tư thế camera được giải '
  'lại mỗi khung nên nó **tự lành**, còn ảnh nền thì không — nên hệ thống phải tự đối chiếu vị '
  'trí các điểm mốc với lúc chụp ảnh nền và cảnh báo khi lệch quá 3 điểm ảnh.')

H3('4.3.4. Vì sao hai thế giới dùng hai phương pháp')

P('Phép trừ nền **không dùng được cho cảnh mô phỏng**: ở đó ba khay màu xám cũng "không phải mặt '
  'bàn", nên vật nằm trong khay dính liền với khay thành một vùng. Ngược lại, phân ngưỡng theo '
  'màu **không dùng được cho vật thật**, vì lý do sâu hơn, trình bày ngay dưới đây.')

P('Toàn bộ khâu ước lượng ngầm giả định **mặt nạ thu được chính là hình bóng của vật**. Giả định '
  'này đúng với vật ảo có thân một màu, nhưng sai hẳn với lon thật: màu nằm thành vành, xen mảng '
  'trắng và logo lớn.')

T('4.3', ['Đại lượng đo trên cùng một khung hình', 'Theo màu', 'Trừ nền'],
  [
      ('Tỉ lệ cao/rộng của ba lon (lon thật: 2,56)', '2,28 / 1,88 / 0,93', '2,45 / 2,26 / 2,65'),
      ('Diện tích ba lon (điểm ảnh)', '14 645 / 5 603 / 2 003', '28 449 / 22 261 / 22 240'),
      ('Nhiễu vị trí theo x (mm thật)', '3,4 / 5,9 / 13,8', '3,0 / 7,1 / 4,4'),
      ('Tỉ lệ nhìn thấy', 'phải đoán bằng hằng số', '0,99 ± 0,01'),
  ],
  widths=[7.0, 4.6, 4.4])

P('Ba lon cùng kích thước mà nhận theo màu cho diện tích chênh nhau **bảy lần** — vì phép đo đang '
  'đo **thiết kế nhãn** chứ không đo vật. Còn tỉ lệ nhìn thấy 0,99 nghĩa là hình bóng đo được '
  'khớp hình bóng dự đoán, tức cơ chế phát hiện che khuất (mục 4.5) lấy lại đúng định nghĩa ban '
  'đầu thay vì phải chia cho một hằng số đoán được.')

P('Kết luận rút ra: **bản sao số cần giống nhau về hình học, còn khâu nhận dạng là bài toán riêng '
  'của từng thế giới.** Đây cũng là câu trả lời cho băn khoăn "vật ảo trông không giống vật thật": '
  'nó không cần giống về bề ngoài, chỉ cần giống về hình học.')

H2('4.4. Ước lượng vị trí từ hình bóng')

P('Có mặt nạ rồi, bước tiếp là suy ra vị trí. Cách đơn giản nhất — lấy tâm khối của vùng ảnh rồi '
  'giao tia — có một sai sót hệ thống: **tâm khối là tâm của phần nhìn thấy**, không phải hình '
  'chiếu của tâm vật. Với vật bị che một phần, hai điểm này lệch nhau đáng kể.')

P('Phương pháp dùng trong đề tài là **khớp hình bóng**. Từ mô hình hình học của vật và mô hình '
  'camera, dựng **hình bóng dự đoán** — bao lồi của ảnh các điểm trên bề mặt vật — rồi tìm vị trí '
  '(x, y) sao cho một đặc trưng hình học của hình bóng dự đoán trùng với đặc trưng tương ứng đo '
  'được trên ảnh. Bài toán hai ẩn này giải bằng phương pháp Newton.')

EQ(sq(fnc('F'), dl(sq(v('x'), o(','), v('y'))), o('='),
      mx([[sq(sb(v('v'), txt('đo')), o('−'), sb(v('v'), txt('dự đoán')),
              dl(sq(v('x'), o(','), v('y'))))],
          [sq(sb(v('u'), txt('đo')), o('−'), sb(v('u'), txt('dự đoán')),
              dl(sq(v('x'), o(','), v('y'))))]]), o('='), nn(0)), '4.4')

H3('4.4.1. Chọn đặc trưng nào')

P('Đặc trưng được chọn khác nhau tùy tình huống, và việc chọn sai gây sai số lớn:')

IMG('4.4')

T('4.4', ['Tình huống', 'Đặc trưng dùng', 'Sai số'],
  [
      ('Vật trong khay (mô phỏng)', 'mép trên + tâm ngang', '13,4 mm → 1,0 mm'),
      ('Vật trên bàn, mặt nạ theo màu', 'mép đáy', '→ 1,8 mm'),
      ('Vật trên bàn thật, mặt bàn phản chiếu', 'mép trên', '11,4 mm → 4,5 mm'),
  ],
  widths=[6.4, 5.0, 4.6])

P('Trường hợp thứ ba đáng nói nhất. Mặt bàn thật phản chiếu hình ảnh của lon, và ảnh phản chiếu '
  '**dính liền** chân lon nên mép đáy của mặt nạ không còn là chỗ lon chạm bàn. Sai lệch **đều '
  'khoảng −33 mm ở cả ba lon**, đúng bằng chiều cao ảnh phản chiếu. Phép trừ nền không xóa được, '
  'vì ảnh phản chiếu chỉ xuất hiện khi có lon.')

P('Ảnh phản chiếu luôn nằm **phía dưới**, nên mép trên miễn nhiễm. Đổi sang khớp mép trên là đủ.')

H3('4.4.2. Hai sai sót phương pháp luận đã mắc phải')

P('Hai lần suýt kết luận sai trong quá trình này, đều đáng ghi lại vì chúng không phải lỗi lập '
  'trình:')

N([
    '**Hai sai số triệt tiêu nhau tạo ra con số đẹp giả tạo.** Trước khi áp dụng phép trừ nền, '
    'cách khớp mép đáy *trông* chính xác hơn (9,08 mm so với 18,31 mm) — vì mặt nạ còn lốm đốm '
    'làm phồng **đỉnh**, bù trừ một phần cho ảnh phản chiếu làm phồng **đáy**. Dọn sạch một sai '
    'số mới thấy sai số kia. Bài học: **không chọn phương pháp theo con số tổng khi dữ liệu đầu '
    'vào còn bẩn.**',
    '**Bộ giải phân kỳ bị nhầm là sai số đo.** Khi xuất phát từ tâm khối (bị ảnh phản chiếu kéo '
    'xuống), mọi lon đặt tại cùng một chỗ đều cho **cùng một đáp án sai** bất kể là lon nào — dấu '
    'hiệu rơi vào nghiệm lạ chứ không phải sai số ngẫu nhiên. Đổi điểm xuất phát sang ước lượng '
    'thô là hết.',
])

H2('4.5. Phát hiện kết quả không đáng tin')

P('Phần này trả lời yêu cầu định tính nêu ở đầu chương. Hệ thống không chỉ đưa ra vị trí mà còn '
  'đưa ra **một cờ tin cậy**, và lớp điều khiển từ chối thao tác trên kết quả không tin cậy.')

IMG('4.5')

T('4.5', ['Lớp', 'Kiểm tra gì', 'Bắt được loại lỗi nào'],
  [
      ('Hình học', 'vị trí nằm ngoài vùng đặt vật',
       'dây điện, mép bàn, sàn nhà lọt vào khung hình'),
      ('Hình dáng', 'bề rộng và chiều cao khung bao so với hình bóng dự đoán',
       'bàn tay, mảnh logo bị tách rời, hai vật dính liền'),
      ('Tỉ lệ nhìn thấy', 'diện tích đo được / diện tích hình bóng dự đoán, ngoài [0,90; 1,30]',
       'vật bị che một phần'),
      ('Xác nhận nhiều khung', 'vị trí nhảy xa phải trụ lại 5 khung liên tiếp',
       'nhiễu thoáng qua'),
  ],
  widths=[3.4, 6.6, 6.0])

P('Bốn lớp này không chồng lấn: mỗi lớp bắt một loại lỗi mà lớp khác bỏ sót. Điều đó quan trọng '
  'hơn việc siết chặt một lớp duy nhất.')

H3('4.5.1. Vì sao tỉ lệ diện tích không phát hiện được vị trí sai')

P('Đây là một giới hạn **mang tính cấu trúc**, không phải chuyện đặt ngưỡng chưa khéo, và việc '
  'nhận ra nó đã dẫn tới lớp kiểm tra hình dáng.')

P('Quy trình ước lượng xác định vị trí **trước**, rồi mới dựng hình bóng dự đoán **tại chính vị '
  'trí vừa tìm được**. Nếu một vùng ảnh lớn hơn vật thật, phép khớp sẽ đẩy vật về **gần camera '
  'hơn**, và hình bóng dự đoán tại vị trí mới đó **cũng lớn hơn**. Tỉ lệ hai diện tích vì vậy '
  '**tự chuẩn hóa** về gần 1. Thử nghiệm xác nhận: đưa tay vào khung hình làm vật ảo nhảy 284 mm '
  'trong khi cờ tin cậy vẫn báo 1,00.')

P('Lớp kiểm tra hình dáng khắc phục được vì nó dùng **thông tin độc lập**: phép khớp chỉ ràng '
  'buộc mép trên và tâm ngang, nên **bề rộng và chiều cao** là hai đại lượng mà phép khớp không '
  'tự điều chỉnh cho khớp. Đo trên ảnh thật: ba lon lành lặn lệch +5 / +13 / +8 % bề rộng — đạt; '
  'một vùng rộng gấp 2,3 lần — loại; một mảnh vụn hẹp hơn 59 % — loại.')

P('Ngưỡng chiều cao phải **không đối xứng** (từ 0,65 đến 1,60) vì ảnh phản chiếu nằm trong khung '
  'bao làm lon lành lặn cao hơn dự đoán 16–28 %. Giới hạn dưới chặt hơn vì "thấp hơn hẳn" chính '
  'là dấu hiệu của một vành logo bị tách rời.')

H3('4.5.2. Ràng buộc không tự chuẩn hóa: vật lý')

P('Lớp cuối cùng dựa vào một ràng buộc mà không phép khớp nào lách được: **vật không dịch chuyển '
  '284 mm trong một phần mười giây**. Một vị trí mới cách xa vị trí cũ phải được **năm khung liên '
  'tiếp xác nhận** mới được chấp nhận. Nhấc vật đặt sang chỗ khác thì chỗ mới trụ lại nên vẫn '
  'được ghi nhận, chỉ trễ nửa giây; nhiễu thoáng qua thì không.')

P('Kiểm chứng bằng cách cố ý gây nhiễu — đưa tay vào khung hình và dời vật nhiều lần: **không một '
  'trường hợp dịch chuyển giả nào** được ghi nhận. Trong cùng khoảng thời gian, hai lần dời vật '
  'thật 177 mm và 170 mm đều được ghi nhận đầy đủ. Bộ lọc chặn được nhiễu mà không chặn nhầm '
  'chuyển động thật.')

H2('4.6. Đánh giá độ chính xác')

P('Bộ dữ liệu đánh giá trong mô phỏng gồm 172 ảnh với vị trí thật đã biết, thu bằng cách dời vật '
  'qua một lưới điểm phủ vùng làm việc, kèm các tình huống khó: robot lơ lửng sát vật, vật nằm '
  'trong khay, vật bị cắt mép ảnh.')

IMG('4.6')

T('4.6', ['Điều kiện đánh giá', 'Trung bình', 'Phân vị 95', 'Lớn nhất'],
  [
      ('Mô phỏng, vùng robot gắp được (58 mẫu)', '1,13 mm', '3,7 mm', '6,2 mm'),
      ('Mô phỏng, toàn bộ điểm trong ảnh', '2,0 mm', '—', '20,6 mm'),
      ('Mô phỏng, vật trong khay (trước khi khớp mép trên)', '13,4 mm', '—', '19,7 mm'),
      ('Mô phỏng, vật trong khay (sau khi khớp mép trên)', '1,0 mm', '—', '1,9 mm'),
      ('Camera thật, 18 phép đo', '4,50 mm', '—', '6,31 mm'),
      ('Camera thật, bỏ phần lệch hệ thống', '2,35 mm', '—', '—'),
  ],
  widths=[7.8, 2.9, 2.6, 2.7])

P('So với dung sai **12 mm** của cơ cấu hút: mô phỏng đạt với biên an toàn gấp mười lần, camera '
  'thật đạt kể cả ở trường hợp xấu nhất.')

P('Phần lệch hệ thống +9,6 mm trên camera thật đã được truy nguyên. Giả thuyết "sai chiều cao '
  'vật" bị **bác bỏ bằng dấu của xu hướng**: sai chiều cao sinh ra lệch **tăng** theo khoảng '
  'cách, trong khi số liệu cho thấy lệch **giảm** (+12,5 / +12,4 / +3,9 mm). Đo riêng từng điểm '
  'mốc cho thấy hai điểm mốc lệch 26 mm và 29 mm so với tọa độ thiết kế. Khắc phục không cần dán '
  'lại: chỉ cần **đo lại tọa độ thật của các điểm mốc và khai báo đúng** — điểm mốc không cần nằm '
  'đúng chỗ thiết kế, chỉ cần biết đúng chỗ nó nằm.')

H3('4.6.1. Độ bền')

IMG('4.7')

T('4.7', ['Yếu tố', 'Mức chịu được', 'Mức bắt đầu hỏng'],
  [
      ('Nhiễu cảm biến (độ lệch chuẩn, mức xám)', '≤ 10: không ảnh hưởng',
       '20: còn 99,2 %; 40: còn 83 %'),
      ('Mức sáng (hệ số nhân)', '0,5 – 1,6: ổn định', '0,3: mất 16,5 %'),
      ('Khoảng cách giữa hai vật đứng cạnh nhau', '≥ 60 mm thật: nhận đủ',
       'chạm nhau: bị từ chối (tỉ lệ nhìn thấy 0,71–0,80)'),
  ],
  widths=[5.4, 5.0, 5.6])

P('Camera thật dùng trong đề tài đo được nhiễu cỡ 2,2 mức xám — nằm sâu trong vùng an toàn.')

P('Trường hợp hai vật chạm nhau vẫn bị từ chối. Đã thử hạ ngưỡng tỉ lệ nhìn thấy và **bác bỏ**: '
  'ngưỡng đó bảo đảm tính chất "hễ báo tin cậy thì sai số nằm trong dung sai gắp", hạ xuống thì '
  'mọi vật bị che một phần đều lọt và robot sẽ hút lệch tâm. Thay vào đó, đây được ghi nhận thành '
  '**điều kiện vận hành**: đặt các vật cách nhau ít nhất một bề rộng vật.')

IMG('4.8')

H2('4.7. Kết luận chương')

P('Chương 4 đã xây dựng hoàn chỉnh hệ thống thị giác:')

B([
    '**Mô hình camera và hiệu chuẩn** hai tầng, với quy ước đưa tọa độ ảo vào ngay từ khâu hiệu '
    'chuẩn — nhờ đó toàn bộ khối phía sau chạy nguyên trong hệ ảo.',
    '**Hai phương pháp tách vật cho hai thế giới**, và lý do của sự khác nhau đó là một kết luận '
    'về bản chất bài toán chứ không phải một chắp vá.',
    '**Ước lượng bằng khớp hình bóng**, với việc chọn đặc trưng theo tình huống — mép trên khi '
    'mặt bàn phản chiếu, mép đáy khi mặt nạ chỉ có phần mang màu.',
    '**Bốn lớp phát hiện kết quả không đáng tin**, trong đó việc nhận ra rằng tỉ lệ diện tích '
    '*về nguyên tắc* không phát hiện được vị trí sai đã dẫn tới hai lớp còn lại.',
    '**Sai số 1,13 mm trong mô phỏng và 4,50 mm trên camera thật**, đều nằm trong dung sai 12 mm '
    'của cơ cấu hút.',
])

P('Chương tiếp theo tích hợp hai nửa đã xây dựng — môi trường mô phỏng của Chương 3 và hệ thống '
  'thị giác của Chương 4 — thành một vòng kín, trong đó vật thể thật điều khiển robot mô phỏng.')

S.save()
