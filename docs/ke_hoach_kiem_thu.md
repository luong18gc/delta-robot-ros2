# Kế hoạch kiểm thử đồ án

Tài liệu này liệt kê các trường hợp kiểm thử (test case) của hệ thống, dùng cho hai mục đích:
viết vào khóa luận, và chọn ra kịch bản trình diễn trước hội đồng phản biện.

Mỗi mục ghi rõ **đã đo hay chưa**. Những mục ghi *chưa đo* là khoảng trống thật — liệt kê ra để
còn bổ sung, chứ không phải để làm đẹp danh sách.

**Nguyên tắc chung:** một phép kiểm thử chỉ có giá trị khi nó **có thể thất bại**. Vì vậy phần lớn
các mục dưới đây được chấm bằng **đo đạc độc lập** (vị trí thật từ mô phỏng, thước đo trên bàn
thật) chứ không phải bằng chính thứ đang được kiểm tra.

---

## A. Kiểm thử tự động — 164 trường hợp, không cần phần cứng

```bash
colcon test --packages-select delta_controller && colcon test-result --verbose
```

Chạy trong khoảng 3 giây, không cần mở mô phỏng, không cần camera, không cần robot. Đây là lớp
bảo vệ chạy lại sau **mỗi** lần sửa mã.

| Khối | Số test | Bảo đảm điều gì |
|---|---|---|
| `test_task_planner` | 40 | lập kế hoạch tác vụ, chọn thứ tự, kiểm tra tầm với, các trường hợp bị từ chối |
| `test_conveyor_cycle` | 32 | máy trạng thái băng tải, bàn giao quyền, nhiều vật cùng lúc |
| `test_trajectory` | 14 | biên dạng bậc năm, quỹ đạo an toàn, kiểm tra toàn tuyến |
| `test_color_detector` | 12 | phân ngưỡng màu, gộp mảnh, ảnh thật có đáp án biết trước |
| `test_task_executor` | 11 | chế độ camera, trí nhớ quan sát, kiểm chứng sau thao tác |
| `test_camera_model` | 10 | phép chiếu, hiệu chuẩn PnP trên ảnh thật |
| `test_delta_kinematics` | 9 | động học thuận/ngược, chọn nhánh, điểm ngoài tầm với |
| `test_gripper_logic` | 9 | cửa sổ dung sai hút |
| `test_object_detector` | 7 | tách nền, tách vùng dính liền |
| `test_real_camera` | 7 | tư thế camera giải lại mỗi khung |
| `test_vision_estimation` | 6 | khớp hình bóng, cờ tin cậy |
| `test_vision_eval` | 4 | tái hiện đúng khâu nhận dạng khi đánh giá ngoại tuyến |
| lint + tài liệu | 3 | phong cách mã, docstring, bản quyền |

**Điểm đáng nói với hội đồng:** phần lớn mã nghiệp vụ (động học, quỹ đạo, lập kế hoạch, máy trạng
thái, ước lượng thị giác) **không phụ thuộc ROS**, nên kiểm thử được bằng `pytest` thuần. Đó là
một quyết định kiến trúc, không phải tình cờ.

---

## B. Động học — nền của mọi thứ phía trên

| Mã | Nội dung | Tiêu chí đạt | Kết quả |
|---|---|---|---|
| B1 | Vòng lặp động học ngược → thuận trên lưới **5 424 điểm** phủ vùng làm việc | sai lệch < 1 µm | **~1e-13 m** (cỡ sai số làm tròn của máy) ✅ |
| B2 | Thay tư thế gốc vào công thức: θ = 0 ⟺ bàn máy tại (0; 0; −140,5) | khớp đúng mô hình URDF | khớp ✅ |
| B3 | Ràng buộc chiều dài thanh chống không đổi ở mọi tư thế | sai lệch < 1 µm | đạt ✅ |
| B4 | Chọn nhánh khuỷu: điểm có **cả hai nghiệm** trong giới hạn khớp | chọn đúng nhánh liên tục với tư thế gốc | đạt ✅ |
| B5 | Điểm ngoài tầm với | phải **báo lỗi**, không trả nghiệm bừa | đạt ✅ |
| B6 | Đo vị trí **thật** trong mô phỏng tại 9 điểm (tư thế gốc, trục Z, lệch X/Y, điểm xa) | lệch < 1 mm | **< 1 mm** ✅ |

> **B1 là phép thử mạnh nhất của chương động học** và nên nêu đầu tiên khi phản biện: nó không
> kiểm tra một vài điểm chọn sẵn mà quét toàn vùng làm việc, và sai số ở mức làm tròn của máy
> tính chứng tỏ hai công thức là nghịch đảo đúng của nhau chứ không phải "gần đúng".

---

## C. Cơ cấu gắp–thả

| Mã | Nội dung | Tiêu chí đạt | Kết quả |
|---|---|---|---|
| C1 | Cửa sổ dung sai hút: lệch ngang ≤ 12 mm, khe ∈ [−4; +6] mm | trong cửa sổ thì hút được, ngoài thì từ chối | đạt ✅ |
| C2 | Ra lệnh hút khi **chưa chạm vật** | bị từ chối, **kèm gợi ý tọa độ đúng** | đạt ✅ |
| C3 | Thả khi **không giữ vật nào** | bị từ chối | đạt ✅ |
| C4 | Thả vào khay **đã có vật khác** | bị từ chối **trước khi nhặt** (không cầm vật mà không có chỗ thả) | đạt ✅ |
| C5 | Đẩy lệch vật bằng bàn máy rồi gắp lại | gắp đúng **vị trí mới**, không theo vị trí cũ | đạt ✅ |
| C6 | Va chạm: ép bàn máy xuống mặt bàn tĩnh | bị chặn đúng cao độ, không rung | đạt ✅ |
| C7 | Va chạm: ép xuống **vật động** | — | ⚠️ **lún 5–8 mm**, nguyên nhân chưa kiểm chứng; đã xử lý bằng ràng buộc không ra lệnh thấp hơn đỉnh vật |

---

## D. Thị giác trên mô phỏng

Bộ dữ liệu: **172 ảnh** có vị trí thật biết trước (`datasets/vision_eval/`), thu bằng cách dời vật
qua lưới 61 điểm × 3 vật, kèm các tình huống khó.

| Mã | Nội dung | Tiêu chí đạt | Kết quả |
|---|---|---|---|
| D1 | Sai số định vị trong **vùng robot gắp được** (58 mẫu) | < 12 mm (dung sai hút) | **TB 1,13 mm · P95 3,7 · max 6,2** ✅ |
| D2 | Toàn bộ điểm trong ảnh | — | TB 2,0 mm · max 20,6 (đều ngoài tầm với) |
| D3 | Vật **trong khay** (thành khay che nửa dưới) | < 12 mm | **13,4 → 1,0 mm** sau khi khớp mép trên ✅ |
| D4 | Vật bị **bàn máy che** | phải bị **từ chối**, không được đoán bừa | score = 0 ✅ |
| D5 | Độ bền với **nhiễu cảm biến** | giữ được tới σ = 10 mức xám | σ ≤ 10 vô hại; σ 20 → 99,2 %; σ 40 → 83 % ✅ |
| D6 | Độ bền với **mức sáng** | — | ổn định 0,5×–1,6×; 0,3× mất 16,5 % |
| D7 | **Chất lượng cờ tin cậy** | bắt được phần lớn ước lượng sai | bắt **97 %** ước lượng sai > 5 mm; báo nhầm 8 % |
| D8 | Ước lượng **được gắn cờ tin cậy** thì sai bao nhiêu | < 12 mm | TB 0,90 mm · **max 3,42 mm** ✅ |

> **D8 là mệnh đề đáng giá nhất của cả khối thị giác**: *hễ hệ thống nói nó tin, thì sai số nằm
> trong dung sai gắp.* Đó là thứ biến một phép ước lượng thành một phép ước lượng **dùng được**.

---

## E. Thị giác trên camera thật

| Mã | Nội dung | Tiêu chí đạt | Kết quả |
|---|---|---|---|
| E1 | Hiệu chuẩn **nội tham số** (bàn cờ) | RMS < 0,5 px | **0,222 px** ✅ |
| E2 | Hiệu chuẩn **ngoại tham số** (6 điểm mốc) | sai số quy ra hệ ảo < 3 mm | **0,93 mm** ✅ |
| E3 | Sai số định vị, **18 phép đo** (3 vật × 6 vị trí, đặt theo dấu bút chì) | < 12 mm | **TB 4,50 mm · tệ nhất 6,31 mm** ✅ |
| E4 | Bỏ phần lệch hệ thống | — | **2,35 mm** → phép đo rất ổn định, phần dư là lỗi mô hình |
| E5 | Truy nguyên phần lệch hệ thống +9,6 mm | phải xác định được nguồn | **bác bỏ** giả thuyết sai chiều cao *bằng dấu của xu hướng*; truy ra **2 điểm mốc lệch 26 và 29 mm** ✅ |
| E6 | So **ngưỡng cố định** với **trừ ảnh nền**, cảnh không có vật | mặt nạ phải trống | ngưỡng: **12,06 %** · trừ nền: **0,00 %** ✅ |
| E7 | Nhiễu vị trí khi vật đứng yên | — | **0,5–0,9 mm** (trước khi trừ nền: 3,0–13,8 mm) ✅ |
| E8 | Cảnh báo **ảnh nền hết hiệu lực** khi camera xê dịch | phải báo, không hỏng âm thầm | 8,7 px → cảnh báo; so với chính nó → 0,00 px, im lặng ✅ |
| E9 | Tường và sàn nhà lọt vào khung (18 % diện tích) | không gây nhận nhầm | 0 điểm ảnh vượt ngưỡng ✅ |
| E10 | Hai vật **chạm nhau** trong ảnh | phải **từ chối**, không gắp lệch tâm | bị từ chối (tỉ lệ nhìn thấy 0,71–0,80) ✅ |
| E11 | Khoảng cách tối thiểu giữa hai vật trên băng | hình bóng không chồng nhau | **≥ 80 mm** (60 mm thì chồng) ✅ |

---

## F. Bản sao số

| Mã | Nội dung | Tiêu chí đạt | Kết quả |
|---|---|---|---|
| F1 | Vật ảo bám vật thật khi đứng yên | < 12 mm ảo | **0,0–0,4 mm ảo** ✅ |
| F2 | Vật ảo bám khi **dời vật thật > 100 mm** | theo kịp | **1 mm thật = 0,3 mm ảo** ✅ |
| F3 | Khởi động lại hệ | vật ảo tự đồng bộ về vị trí thật | đạt ✅ |
| F4 | **Đưa tay vào khung hình** (gây nhiễu cố ý) | **không** được sinh dịch chuyển giả | **0 lần dịch chuyển giả**; 25 khung bị lớp hình dáng loại ✅ |
| F5 | Nhiễu thoáng qua so với **chuyển động thật** | chặn nhiễu, **không chặn nhầm** chuyển động thật | 12 khung bị giữ lại; 2 lần dời thật 177 và 170 mm **đều tới nơi** ✅ |
| F6 | Vành logo đỏ của vật khác bị nhận nhầm | phải bị loại | lớp **hình dáng** loại được ✅ |

> **F4–F5 là cặp đôi nên diễn trước hội đồng**: một lớp bảo vệ chỉ đáng tin khi nó vừa chặn được
> cái sai **vừa không chặn nhầm cái đúng**. Chỉ chứng minh vế đầu thì chưa đủ — tắt hẳn hệ thống
> cũng "chặn được mọi cái sai".

---

## G. Vòng băng tải

| Mã | Nội dung | Tiêu chí đạt | Kết quả |
|---|---|---|---|
| G1 | Tốc độ băng và **quãng trôi** sau khi dừng | đo được, dùng đặt hạn chờ | **16 mm/s**, trôi **3 mm** ✅ |
| G2 | Điểm gắp khi vật **tự chạy tới** | khác điểm đặt tay | **+90,2 mm** so với +82,1 mm đặt tay ✅ |
| G3 | Vòng đầy đủ: bám → chạy → dừng → hút → thả | hoàn thành | đạt ✅ |
| G4 | **Bàn giao quyền vị trí** — vật thật còn trên băng sau khi robot đã thả vật ảo vào khay | vật ảo **không** bị kéo về băng | đạt (32 test tự động + chạy thật) ✅ |
| G5 | **Nhiều vật cùng lúc** trên băng | xử lý lần lượt từ vật gần điểm gắp nhất | đạt (7 test tự động) ✅ |
| G6 | Hạn chờ khi vật **không tới nơi** (kẹt, trượt dây) | dừng băng và báo | đạt ✅ |
| G7 | Lưới an toàn: **mất kết nối máy tính** | băng **tự dừng** sau 3 s | đạt ✅ |
| G8 | Robot che vật kế tiếp sau khi thả | tự lùi về tư thế quan sát | đạt ✅ |

> **G7 nên diễn trực tiếp**: rút cáp USB giữa lúc băng đang chạy, băng tự dừng sau 3 giây. Đây là
> an toàn chức năng chứ không phải tính năng phụ — một băng tải chạy mãi vì phần mềm điều khiển
> đã chết là thứ không được phép tồn tại.

---

## H. Kiểm thử đầu-cuối, có thống kê

| Mã | Nội dung | Số lượt | Kết quả |
|---|---|---|---|
| H1 | Phân loại 3 vật vào đúng khay, **5 bố trí ngẫu nhiên** (seed cố định) | 5 | **15/15 vật · 5/5 lượt** ✅ |
| H2 | Trả mọi vật về chỗ cũ | 5 | **15/15 vật** (TB 5,5 mm · max 7,1 mm) ✅ |
| H3 | Thời gian mỗi lượt | — | 106 s + 111 s |
| H4 | So chế độ **camera** với chế độ **vị trí thật** (cảnh cũ, 10 bố trí) | 10 | **bằng nhau: 30/30 cả hai chế độ**; camera chậm hơn ~35 % ✅ |

> **H4 là phép so sánh then chốt của đề tài**: nó trả lời câu hỏi *"thay vị trí thật bằng camera
> thì mất gì?"* — và câu trả lời là **không mất tỉ lệ thành công nào**, chỉ chậm hơn vì phải dừng
> lại quan sát.

---

## I. Kịch bản trình diễn trước hội đồng

Chọn theo tiêu chí: **ngắn, nhìn thấy được, và mỗi kịch bản chứng minh một năng lực khác nhau.**

| # | Kịch bản | Thời lượng | Chứng minh điều gì |
|---|---|---|---|
| 1 | Dời vật thật trên bàn bằng tay, vật ảo bám theo trong Gazebo | 1 phút | toàn chuỗi camera → mô phỏng chạy thật |
| 2 | Bấm **Phân loại tất cả** trên giao diện, robot tự gắp 3 vật vào 3 khay | 2 phút | hệ thống hoàn chỉnh, tự chủ |
| 3 | Đặt vật lên băng, chạy vòng băng tải trọn vẹn | 2 phút | tính ứng dụng công nghiệp |
| 4 | **Đưa tay vào khung hình** trong lúc đang chạy | 30 giây | hệ thống **từ chối** thay vì làm sai |
| 5 | Đặt hai vật **chạm nhau**, rồi tách ra | 1 phút | biết khi nào mình không chắc, và tự phục hồi |
| 6 | Yêu cầu gắp vật **ngoài tầm với** | 15 giây | kiểm tra toàn tuyến **trước khi** chuyển động |
| 7 | **Rút cáp USB** của băng tải lúc đang chạy | 15 giây | an toàn chức năng |
| 8 | Che một vật rồi hỏi hệ thống | 30 giây | cờ tin cậy, và trí nhớ quan sát |

**Khuyến nghị quan trọng:** kịch bản 4, 5, 6, 7 — tức **các kịch bản hệ thống TỪ CHỐI làm** — nên
chiếm ít nhất một nửa thời lượng. Một hệ thống chạy đúng khi mọi thứ thuận lợi là điều hội đồng
mặc định phải có; thứ phân biệt là hệ thống **biết khi nào nó không nên hành động**.

**Nên chuẩn bị sẵn:** `docs/results/*.md` mở sẵn trên màn hình để dẫn số khi được hỏi, và lệnh
`colcon test` chạy tại chỗ (3 giây) để chứng minh 164 test không phải con số trên giấy.

---

## J. Khoảng trống chưa kiểm thử

Liệt kê trung thực, kèm mức độ ưu tiên. Hội đồng thường hỏi đúng những chỗ này.

| Mã | Chưa có | Vì sao đáng làm | Ưu tiên |
|---|---|---|---|
| J1 | **Độ lặp lại**: đặt cùng một vật vào cùng một chỗ N lần, đo độ tản mạn | Sai số TB đã có, nhưng *độ lặp lại* mới trả lời "hệ thống có ổn định không". Dễ làm: ~20 phút | **Cao** |
| J2 | **Độ trễ đầu-cuối**: từ lúc vật thật dịch tới lúc robot bắt đầu đi | Số liệu bắt buộc cho một hệ thống điều khiển theo thời gian thực; hiện chỉ có tần số khung (10 Hz) và thời gian xử lý (42 ms) | **Cao** |
| J3 | **Tỉ lệ thành công của vòng băng tải** qua N lượt liên tiếp | H1–H4 đo cảnh trên bàn; vòng băng tải mới chỉ chạy định tính | **Cao** |
| J4 | **Chạy dài**: 30–60 phút liên tục | Phát hiện rò rỉ bộ nhớ, trôi hiệu chuẩn, tích lũy sai số | Trung bình |
| J5 | **Phục hồi sau khi hút hụt** | Hiện tại báo lỗi và dừng; chưa thử tự nhặt lại | Trung bình |
| J6 | Hai vật **cùng màu** | Giới hạn đã biết của giả định "một màu một vật"; nên **nêu ra như giới hạn** thay vì giấu | Thấp (là giới hạn, không phải lỗi) |
| J7 | Kiểm thử **giao diện** | Hiện kiểm bằng tay | Thấp |
| J8 | **Người dùng không nhấc vật thật** khỏi băng sau khi gắp | Hệ thống sẽ chờ mãi — đúng thiết kế, nhưng chưa thử xem thông báo có đủ rõ không | Trung bình |

**Đề xuất:** làm **J1, J2, J3** trước buổi phản biện. Cả ba đều đo được trong một buổi, và cả ba
đều tạo ra **bảng số liệu mới** cho khóa luận — thứ mà hội đồng đánh giá cao hơn hẳn một mô tả
định tính.
