# Danh mục chức năng và kịch bản trình diễn

Liệt kê **những gì hệ thống làm được** và cách cho hội đồng thấy từng thứ. Sắp theo mạch tăng
dần: cơ cấu → tương tác → thị giác → bản sao số → vòng khép kín → các tình huống từ chối.

Tổng thời lượng nếu diễn hết: **khoảng 25 phút**. Phần đánh dấu ⭐ là phần nên giữ nếu bị rút gọn.

**Chuẩn bị:** mở sẵn 3 cửa sổ — Gazebo (mô phỏng), giao diện điều khiển, và ảnh gỡ lỗi của camera
(`rqt_image_view /vision/debug_image`). Ảnh gỡ lỗi là thứ thuyết phục nhất vì hội đồng **nhìn thấy
hệ thống đang nhìn thấy gì**.

```bash
# Terminal 1 — cả hệ thống
ros2 launch delta_controller conveyor_cycle.launch.py
# Terminal 2 — giao diện
ros2 run delta_controller gui
# Terminal 3 — ảnh gỡ lỗi
ros2 run rqt_image_view rqt_image_view /vision/debug_image
```

---

## Phần 1 — Nền tảng: động học và chuyển động (3 phút)

| # | Chức năng | Cách diễn | Hội đồng thấy gì |
|---|---|---|---|
| 1.1 | **Điều khiển theo tọa độ Descartes** | gõ `0 0 -0.15` trong `cartesian_control` | nhập tọa độ không gian, robot tự tính 3 góc khớp — đây là bài toán động học ngược |
| 1.2 | **Đọc ngược vị trí từ góc khớp** | gõ `where` | động học thuận: từ 3 góc đo được suy ra vị trí bàn máy |
| 1.3 | ⭐ **Quỹ đạo an toàn ba đoạn** | gõ `safe -0.08 0 -0.16` | robot **nâng lên, đi ngang, hạ xuống** thay vì đi thẳng xuyên qua vật |
| 1.4 | **Đổi tốc độ** | gõ `speed 0.02` rồi lặp lại lệnh | cùng quỹ đạo, chạy chậm lại |

> **Câu nên nói:** ba góc khớp được giải bằng công thức dạng đóng, không phải bằng phép lặp số —
> nên thời gian tính là hằng số và không có chuyện không hội tụ.

---

## Phần 2 — Tương tác với vật thể (4 phút)

| # | Chức năng | Cách diễn | Hội đồng thấy gì |
|---|---|---|---|
| 2.1 | **Gắp một vật theo tên** | giao diện: chọn vật → **Nhặt lên** | robot tự tính điểm chạm, hạ xuống, hút |
| 2.2 | ⭐ **Thả vào đúng khay theo chủng loại** | **Thả vào khay** | mỗi loại có khay riêng — hệ thống tự biết khay nào |
| 2.3 | **Lấy vật từ khay ra bàn** | **Lấy ra bàn** | thao tác ngược lại |
| 2.4 | ⭐⭐ **Phân loại tự động toàn bộ** | **Phân loại tất cả** | robot tự lần lượt gắp 3 vật vào 3 khay, **không cần lệnh nào thêm** |
| 2.5 | **Trả mọi vật về chỗ cũ** | **Trả về chỗ cũ** | dựng lại cảnh ban đầu, sẵn sàng diễn lại |
| 2.6 | ⭐ **Kiểm chứng bằng đo đạc** | xem nhật ký khi gắp | hệ thống **tự kiểm tra** vật đã được nhấc lên ≥ 10 mm và đã nằm trong khay — không chỉ gửi lệnh rồi coi là xong |

> **Điểm nhấn của phần này là 2.6.** Một thao tác chỉ được coi là thành công khi **quan sát xác
> nhận**, không phải khi lệnh đã gửi đi. Đây là khác biệt giữa "chạy được" và "biết mình đã làm
> được".

---

## Phần 3 — Thị giác máy tính (6 phút) — trọng tâm đề tài

| # | Chức năng | Cách diễn | Hội đồng thấy gì |
|---|---|---|---|
| 3.1 | ⭐⭐ **Nhận dạng và định vị bằng camera đơn** | nhìn cửa sổ ảnh gỡ lỗi | khung bao quanh từng vật, kèm **tên, tọa độ mm, tỉ lệ nhìn thấy** |
| 3.2 | ⭐ **Hiển thị cả hai hệ tọa độ** | đọc nhãn trên ảnh | `thật +X,+Y \| ảo +X,+Y` — thể hiện phép ánh xạ tỉ lệ k = 3 |
| 3.3 | **Hiệu chuẩn tự động mỗi khung** | che một điểm mốc rồi bỏ ra | tư thế camera được **giải lại từng khung**, nên xê dịch camera là tự thích nghi |
| 3.4 | ⭐ **Giới hạn vùng xét theo hình học** | nhìn vùng tối ở rìa ảnh | chỉ xét phần mặt bàn — tường, sàn, dây điện bị loại **trước khi** phân tích |
| 3.5 | **Tách vật bằng trừ ảnh nền** | bật/tắt đèn trong phòng | nhận dạng **không đổi** khi ánh sáng đổi — vì so với ảnh nền chứ không dùng ngưỡng cố định |
| 3.6 | ⭐⭐ **Cờ tin cậy** | lấy tay che một phần vật | nhãn chuyển sang **`BỊ CHE?`**, hệ thống **ngừng tin** vật đó |
| 3.7 | **Ước lượng vật trong khay** | đặt một vật vào khay | thành khay che nửa dưới, hệ thống vẫn định vị đúng nhờ **khớp mép trên** |

> **Hai số nên nhớ để trả lời:** sai số **1,13 mm** trong mô phỏng và **4,50 mm** trên camera
> thật, so với dung sai của cơ cấu hút là **12 mm**.

---

## Phần 4 — Bản sao số (3 phút)

| # | Chức năng | Cách diễn | Hội đồng thấy gì |
|---|---|---|---|
| 4.1 | ⭐⭐ **Vật thật dịch → vật ảo dịch theo** | dùng tay đẩy một lon trên bàn thật | lon trong Gazebo **đi theo ngay**, lệch dưới 1 mm |
| 4.2 | ⭐ **Chỉ ghi khi dịch thật sự** | chạm nhẹ vào lon | dưới 6 mm thì hệ thống **để yên** cho bộ giải vật lý, không ghi đè 10 lần/giây |
| 4.3 | **Khởi động lại là tự đồng bộ** | tắt rồi mở lại mô phỏng | lon ảo tự nhảy từ vị trí khai báo về đúng vị trí thật |
| 4.4 | ⭐ **Robot bám theo vật đang di chuyển** | `ros2 run delta_controller follow`, rồi đẩy lon | đầu hút **giữ khoảng cách cố định** phía trên nắp lon trong suốt quá trình |

> **Thuật ngữ nên dùng:** đây là **digital shadow** (bóng số) khi thông tin chỉ đi một chiều
> thật → ảo, và trở thành **digital twin** đầy đủ khi mô phỏng ra lệnh ngược lại cho băng tải ở
> Phần 5.

---

## Phần 5 — Vòng khép kín với băng tải (4 phút) ⭐⭐

| # | Chức năng | Cách diễn | Hội đồng thấy gì |
|---|---|---|---|
| 5.1 | **Mô phỏng điều khiển thiết bị thật** | bấm **Bắt đầu vòng** | mô phỏng **ra lệnh cho băng tải thật** chạy — thông tin đi cả hai chiều |
| 5.2 | ⭐ **Đầu hút vào vị trí trước khi băng chạy** | quan sát thứ tự | robot lên trên nắp lon **rồi** băng mới chạy |
| 5.3 | ⭐⭐ **Bám theo lon suốt hành trình** | quan sát | đầu hút đi theo lon trên cả quãng băng, nên khi băng dừng là hút được **ngay** |
| 5.4 | **Dừng đúng điểm gắp** | quan sát | camera báo lon tới nơi → mô phỏng ra lệnh dừng băng |
| 5.5 | ⭐⭐ **Bàn giao quyền quyết định** | sau khi robot thả lon vào khay | lon thật **vẫn trên băng** mà lon ảo **nằm yên trong khay** — quyền vị trí đã chuyển sang mô phỏng |
| 5.6 | **Nhận lại quyền khi thế giới thật đồng bộ** | nhấc lon thật ra | hệ thống nhận ra, báo sẵn sàng, chờ lon kế tiếp |
| 5.7 | ⭐ **Nhiều lon cùng lúc trên băng** | đặt 2–3 lon cách nhau ≥ 80 mm | xử lý lần lượt từ lon gần điểm gắp nhất |

> **5.5 là ý tưởng kỹ thuật sâu nhất của cả đồ án** và nên dành thời gian giải thích: nếu không
> bàn giao quyền, bản sao số sẽ kéo lon ảo từ trong khay về lại băng **10 lần mỗi giây**, xóa sạch
> việc robot vừa làm nhanh đúng bằng tốc độ robot làm.

---

## Phần 6 — Các tình huống hệ thống TỪ CHỐI (4 phút) ⭐⭐

Phần quan trọng nhất. Nếu bị rút ngắn thời gian, **cắt phần khác chứ đừng cắt phần này**.

| # | Tình huống | Cách diễn | Hệ thống phản ứng thế nào |
|---|---|---|---|
| 6.1 | ⭐⭐ **Bàn tay lọt vào khung hình** | đưa tay vào giữa lúc đang chạy | **không** sinh dịch chuyển giả; nhật ký ghi "Thay 1/2 vat" |
| 6.2 | ⭐ **Hai vật chạm nhau** | đẩy hai lon sát nhau rồi tách ra | lúc chạm: **từ chối** cả hai; tách ra: nhận lại ngay |
| 6.3 | ⭐ **Yêu cầu gắp ngoài tầm với** | gõ `0.2 0 -0.19` | báo lỗi **trước khi** robot nhúc nhích — kiểm tra toàn tuyến chứ không phải chỉ điểm cuối |
| 6.4 | **Thả khi không giữ vật** | bấm **Thả vào khay** lúc tay trống | bị từ chối kèm lý do |
| 6.5 | **Thả vào khay đã có vật** | thử chuyển hai vật vào cùng khay | từ chối **trước khi nhặt** — không cầm vật rồi mới phát hiện không có chỗ thả |
| 6.6 | ⭐⭐ **Rút cáp USB băng tải** | rút giữa lúc băng chạy | băng **tự dừng sau 3 giây** |
| 6.7 | **Xê dịch camera** | chạm nhẹ vào giá camera | hệ thống **cảnh báo ảnh nền hết hiệu lực** kèm lệnh cần gõ |
| 6.8 | **Che hoàn toàn một vật** | đặt vật bị bàn máy che | cờ tin cậy về 0, lệnh gắp vật đó bị từ chối kèm lý do |

> **Câu then chốt khi trình bày phần này:**
>
> *"Một hệ thống chạy đúng khi mọi thứ thuận lợi là điều mặc định phải có. Thứ phân biệt là nó
> biết khi nào mình không nên hành động — vì trong sản xuất, một robot gắp sai còn tốn kém hơn
> một robot không gắp."*
>
> Và cần nói thêm vế thứ hai, nếu không sẽ bị hỏi ngay: các lớp bảo vệ **không chặn nhầm** chuyển
> động thật. Đã đo: trong cùng khoảng thời gian có 25 khung bị từ chối vì tay người, thì hai lần
> dời lon thật 177 mm và 170 mm **đều được ghi nhận đầy đủ**.

---

## Phần 7 — Chất lượng phần mềm (1 phút)

| # | Chức năng | Cách diễn | Hội đồng thấy gì |
|---|---|---|---|
| 7.1 | ⭐ **164 kiểm thử tự động** | `colcon test --packages-select delta_controller` | chạy xong trong **3 giây**, không cần mô phỏng, không cần camera |
| 7.2 | **Kiến trúc tách lớp** | giải thích | động học, quỹ đạo, lập kế hoạch, máy trạng thái **không phụ thuộc ROS** nên test được độc lập |
| 7.3 | **Một nguồn dữ liệu duy nhất** | mở `scene.py` | mọi tọa độ, kích thước, màu sắc khai báo một chỗ; đổi chiều băng tải chỉ sửa **một con số** |

---

## Nếu chỉ có 10 phút

Giữ đúng bốn thứ này:

1. **2.4** — Phân loại tự động toàn bộ *(hệ thống hoàn chỉnh)* — 2 phút
2. **4.1** — Vật thật dịch, vật ảo bám theo *(chuỗi camera → mô phỏng)* — 2 phút
3. **5.1 + 5.5** — Vòng băng tải và bàn giao quyền *(tính ứng dụng + chiều sâu kỹ thuật)* — 4 phút
4. **6.1 + 6.6** — Tay vào khung, rút cáp băng tải *(hệ thống biết từ chối)* — 2 phút

---

## Bảng số liệu nên thuộc

| Câu hỏi có thể gặp | Trả lời |
|---|---|
| Sai số định vị bao nhiêu? | **1,13 mm** (mô phỏng) · **4,50 mm** (camera thật) |
| So với yêu cầu? | dung sai cơ cấu hút **12 mm** → đạt, kể cả trường hợp xấu nhất |
| Tỉ lệ gắp thành công? | **15/15 vật**, 5/5 lượt, trên 5 bố trí ngẫu nhiên |
| Dùng camera so với dùng vị trí thật thì kém hơn bao nhiêu? | **bằng nhau** (30/30 cả hai), camera chậm hơn ~35 % |
| Tốc độ xử lý? | **10 hình/giây**, 42 ms mỗi ảnh |
| Vì sao phải thu nhỏ tỉ lệ 3 lần? | vùng làm việc cao ~120 mm, lon thật cao 147 mm → gắp tới nơi nhưng **không nhấc lên được** |
| Phóng to robot có được không? | không — đổi hình học sẽ **phá mối hàn mạch kín** và mọi kiểm chứng động học phải làm lại |
| Giới hạn của hệ thống? | mỗi màu một vật; hai vật chạm nhau bị từ chối; cần đặt cách nhau ≥ 80 mm trên băng |
