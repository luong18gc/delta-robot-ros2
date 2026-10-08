# Băng chuyền — thiết kế và hướng dẫn tự làm

Mục tiêu: thay thao tác **dùng tay dời lon** bằng **băng chuyền một lon mỗi lượt**, theo góp ý của
giảng viên hướng dẫn (2026-10-08). Mô phỏng ra lệnh **dừng băng** khi lon tới điểm gắp → đồ án đạt
đúng định nghĩa **digital twin hai chiều**, thay vì chỉ là bóng số như hiện nay.

---

## 1. Ba ràng buộc từ phía thị giác (đọc TRƯỚC khi mua vật liệu)

Ba điều này quyết định chọn vật liệu; chọn sai là phải mua lại.

### 1.1. Mặt băng phải NHÁM và ĐỒNG NHẤT

Khối thị giác tách vật khỏi nền bằng cách **so với ảnh mặt bàn trống**. Băng chuyền thì **chuyển
động**, nên nếu mặt băng có vân, có mối nối nổi, hay sáng tối không đều thì ở mỗi vị trí mặt băng
lại khác ảnh chuẩn → **toàn bộ mặt băng bị coi là vật**.

Yêu cầu:
- mặt băng **nhìn y hệt nhau ở mọi vị trí** — không hoa văn, không sợi nổi;
- **mối nối phẳng** hết mức (nối chéo 45° và dán nhiệt tốt hơn nối vuông góc);
- **nhám**, không bóng.

Vật liệu nên dùng: **băng tải PVC trơn, dày 1,5–2 mm, màu xanh lá đậm hoặc đen nhám** (loại bán
theo mét cho băng tải thực phẩm). Tránh: vải bố có vân, cao su có gân, nhựa bóng.

### 1.2. Băng nhám XÓA luôn vấn đề ảnh phản chiếu

Mặt bàn hiện tại phản chiếu lon, vệt thò xuống **25–102 px** tùy khoảng cách — nguyên nhân của một
loạt rắc rối (xem mục 8.5 khóa luận). Mặt băng nhám không phản chiếu, nên:
- có thể **quay lại dùng khớp mép đáy**, vốn chính xác hơn mép trên (0,1–0,7 mm so với 5–12 mm
  trong mô phỏng);
- phép kiểm tra hình dáng lấy lại ngưỡng chiều cao đối xứng.

Đây là lợi ích phụ nhưng đáng kể — nên **ưu tiên độ nhám hơn là màu sắc**.

### 1.3. Marker nằm trên BÀN, không nằm trên băng; và mặt băng cao hơn mặt bàn

- Marker hiệu chuẩn **phải cố định** → dán trên mặt bàn hai bên băng, tuyệt đối không dán lên băng.
- Lon đứng trên băng thì **cao hơn mặt bàn một khoảng bằng chiều dày băng + khung** (dự kiến
  15–25 mm). Khối thị giác đang giả định vật đứng ở cao độ `TABLE_Z`, nên phải thêm một tham số
  **cao độ mặt băng** cho vùng băng chuyền. Việc nhỏ trong code, nhưng quên là sai hệ thống đúng
  bằng chiều dày băng chia cho 3 (tỉ lệ ảo).
- Càng **thấp càng tốt**: khung băng thấp thì sai số do quên bù cũng nhỏ, và lon ít bị khung che.

---

## 2. Bố trí hình học

Vùng robot với tới trên bàn thật (từ `scene.REAL_OBJECT_AREA_*`):

| | từ | đến |
|---|---|---|
| X (xa dần camera) | −60 mm | +160 mm |
| Y (ngang) | −180 mm | +180 mm |

**Băng chạy dọc theo trục Y**, tức ngang qua tầm nhìn camera. Lý do: lon đi ngang qua ảnh nên không
tự che mình, và không chạy vào/ra theo hướng nhìn (hướng mà sai số định vị lớn nhất).

```
        camera (x = −537)
             |
             v
   ┌─────────────────────────────┐  mặt bàn
   │  [M0]                 [M1]  │
   │                             │
   │   ╔═══════════════════╗     │   băng chuyền, chạy dọc Y
   │   ║ →  →  →  ▣        ║     │   ▣ = lon, đi từ y=+250 về y=0
   │   ╚═══════════════════╝     │
   │        ^ điểm gắp (y≈0)     │
   │  [M4]                 [M5]  │
   └─────────────────────────────┘
```

- **điểm gắp**: x ≈ +50 mm, y ≈ 0 — nằm giữa vùng với tới, dư an toàn mọi phía;
- **đầu nạp lon**: y ≈ +250 mm, **ngoài tầm với** — chỗ tay người đặt lon, robot không bao giờ tới;
- **chiều dài băng**: 450–550 mm (quãng chạy ~250 mm + hai đầu con lăn);
- **bề rộng băng**: 90–110 mm (lon Ø 57,5 mm, cần dư hai bên để lon không rơi);
- **chiều cao khung**: càng thấp càng tốt, dưới 40 mm.

⚠️ Kiểm tra trước khi khoan: băng không được che marker nào, và cả 6 marker vẫn phải trong khung
hình. Hiện ID 4 đã sát mép trên ảnh (cách 74 px) — nếu phải dời marker thì dời, nhưng **đo lại tọa
độ thật và điền vào `scene.REAL_CALIB_MARKERS`**; marker không cần nằm đúng chỗ thiết kế, chỉ cần
BIẾT ĐÚNG chỗ nó nằm.

---

## 3. Danh sách linh kiện

Giá tham khảo tại Việt Nam, 2026. Tổng ước tính **500 – 900 nghìn đồng**.

| Hạng mục | Gợi ý cụ thể | Ghi chú |
|---|---|---|
| Mặt băng | Băng tải PVC trơn 2 mm, xanh đậm/đen nhám, khổ 10 cm × 1,2 m | Mua dư để nối thử vài lần |
| Con lăn | Ống nhựa PVC Ø 40–50 mm, dài 12 cm, 2 cái | Hoặc trục gỗ tròn |
| Trục | Thanh ren M8 hoặc trục thép Ø 8 mm | Xuyên tâm ống PVC |
| Bạc đạn | Vòng bi 608ZZ, 4 cái | Loại dùng cho ván trượt, rất sẵn |
| Khung | Nhôm định hình 2020, hoặc gỗ thông 1,5 cm | Gỗ rẻ và dễ làm hơn |
| Động cơ | **DC giảm tốc JGB37-520, 12 V, 30–60 vòng/phút** | Phải CÓ hộp số: tốc độ thấp + mô-men đủ |
| Mạch lái | **L298N** (hoặc BTS7960 nếu muốn êm hơn) | L298N dư sức cho tải này |
| Vi điều khiển | **Arduino Uno hoặc Nano** | Nối USB với máy tính, ROS nói chuyện qua serial |
| Nguồn | Adapter 12 V – 2 A | Dùng chung cho động cơ |
| Lặt vặt | Dây, ốc, keo dán băng tải, công tắc hành trình dự phòng | |

**Vì sao động cơ phải có hộp số:** camera chạy 10 hình/giây. Băng chạy 50 mm/s thì mỗi khung lon đi
5 mm — bám tốt. Động cơ DC trần quay 3000 vòng/phút với con lăn Ø 45 mm cho 7 m/s, nhanh gấp 140
lần mức cần. Hộp số 30–60 vòng/phút cho 70–140 mm/s, rồi giảm tiếp bằng PWM.

---

## 4. Kiến trúc điều khiển

```
mô phỏng (ROS)  ──►  node belt  ──serial──►  Arduino  ──►  L298N  ──►  động cơ
     ▲                                                                    │
     └──────────── camera thấy lon tới điểm gắp ◄─────────────────────────┘
```

**Giao thức serial giữ thật đơn giản** — một ký tự mỗi lệnh:

| gửi | nghĩa |
|---|---|
| `R` | chạy (run) |
| `S` | dừng (stop) |
| `V<n>` | đặt tốc độ PWM 0–255 |

Arduino trả `OK` cho mỗi lệnh. Không cần giao thức phức tạp; càng ít trạng thái hai bên càng ít lỗi.

### Phát hiện lon tới điểm gắp: dùng CAMERA, không dùng cảm biến

Có thể gắn cảm biến hồng ngoại ở cuối băng, nhưng **nên dùng chính camera**:
- đúng tinh thần đề tài — thị giác điều khiển cả vòng, không chỉ định vị;
- không thêm phần cứng, không thêm dây;
- hệ đã biết vị trí lon chính xác 4,5 mm, thừa sức biết lon đã qua mốc y hay chưa.

Giữ **công tắc hành trình cơ khí** ở cuối băng làm **chặn an toàn**, phòng khi thị giác mất dấu —
đây là chặn vật lý, không phải cảm biến chính.

---

## 5. Máy trạng thái — phần khó nhất, và nó không nằm ở phần cứng

Câu "tắt camera lúc robot gắp" của thầy đang che một vấn đề sâu hơn: **danh tính vật**.

Hệ hiện ngầm giả định *lon Coca thật ↔ lon Coca ảo, một đối một, vĩnh viễn*. Với băng chuyền thì:

1. lon thật tới cuối băng → lon ảo ở đó → robot ảo gắp, mang vào khay;
2. tay người nhấc lon thật ra, đặt **lon mới** lên đầu băng;
3. camera thấy "có lon ở đầu băng" → bản sao số kéo lon ảo **từ trong khay ra đầu băng**, xóa sạch
   việc robot vừa làm.

Tắt camera chỉ **hoãn** bước 3. Lời giải đúng là **bàn giao quyền sở hữu**: khi robot đã gắp, lon ảo
đó **thuộc về mô phỏng**, không soi gương lon thật nữa; lon thật mới xuất hiện thì nhận **một lon ảo
khác**. Có 3 lon ảo và băng một lon → chạy vòng là đủ.

```
CHO_LON    camera chưa thấy lon trên băng
   │ thấy lon ở đầu băng → nhận một lon ảo còn rảnh
   ▼
DANG_CHAY  băng chạy, bản sao số bám lon (robot có thể bám theo)
   │ lon qua mốc điểm gắp
   ▼
DUNG_BANG  gửi `S`; chờ lon đứng yên (vài khung liên tiếp)
   │
   ▼
DANG_GAP   robot gắp → mang tới khay → thả
           THỊ GIÁC BỊ BỎ QUA cho lon này (nó thuộc mô phỏng)
   │ thả xong
   ▼
NHA_QUYEN  lon ảo ở lại khay; lon ảo này được đánh dấu "đã dùng"
           gửi `R` cho băng chạy lại
   └──► CHO_LON
```

**Không cần tắt camera phần cứng.** Bỏ qua thị giác theo trạng thái cho cùng tác dụng, mà camera
vẫn chạy để xác nhận băng đã trống trước khi nhận lon mới. Tắt rồi bật lại camera USB còn mất vài
giây khởi động và **phải chụp lại ảnh nền**.

Phần lo "tay người trong khung làm nhiễu" thì **đã giải quyết** (đo 2026-10-07: 25 khung bị từ chối
khi đưa tay vào, không một cú dịch chuyển giả nào).

---

## 6. Thứ tự làm — mỗi chặng chạy được rồi mới sang chặng sau

| chặng | nội dung | kiểm chứng |
|---|---|---|
| 1 | Dựng khung, lắp băng, chạy bằng tay (cấp nguồn trực tiếp) | Lon đi hết băng không lệch, không trượt |
| 2 | Arduino + L298N, gõ `R`/`S` qua serial monitor | Băng dừng/chạy đúng lệnh |
| 3 | Chụp lại ảnh nền có băng; kiểm tra thị giác trên băng đứng yên | 3/3 khung thấy lon, tỉ lệ nhìn thấy ~1,0 |
| 4 | Node ROS điều khiển băng; thêm tham số cao độ mặt băng | Vị trí lon trên băng đúng trong 5 mm |
| 5 | Máy trạng thái + bàn giao danh tính | Chạy 5 lon liên tiếp không lỗi |
| 6 | Nối gắp–thả, đo tỉ lệ thành công | Số liệu cho Chương 10 khóa luận |

Chặng 3 là chỗ dễ vỡ nhất: nếu mặt băng không đồng nhất thì phải xử lý vật liệu trước khi đi tiếp.
**Thử chặng 3 bằng một mẩu băng tải trước khi mua cả mét** nếu người bán cho mẫu.
