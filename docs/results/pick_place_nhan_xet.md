# Nhận xét thí nghiệm gắp–thả dựa trên camera (Bước 9)

Số liệu: `pick_place_trials.md` / `.json` (sinh bởi `scripts/run_pick_place_trials.py`). File này viết tay.

## Kết quả (10 bố trí ngẫu nhiên, seed 2026, sau khi sửa)
- **Camera: 30/30 vật vào ô, 10/10 lượt `don` trọn vẹn; 30/30 vật về chỗ cũ, 10/10 lượt `reset`.**
- Vị trí thật (đáp án Gazebo): cùng 30/30 và 10/10 → dùng camera **không làm giảm độ tin cậy**.
- Thời gian: camera 58 + 55 s mỗi lượt, vị trí thật 43 + 36 s → camera chậm hơn ~35% vì mỗi lần đo
  robot về tư thế quan sát (0, 0, −0.11) và chờ ≥ 2 khung ảnh mới.

## Lỗi ở lần chạy đầu (5 bố trí, ngưỡng tỉ lệ nhìn thấy 0.85) và cách sửa
- Camera, bố trí 4: hộp đỏ tại (8.4, −94.9) mm đứng **sau trụ xanh** khi nhìn từ camera → bị che ~15% →
  ước lượng lệch 8 mm nhưng tỉ lệ nhìn thấy vẫn nhỉnh hơn 0.85 → giác hút (dung sai 12 mm) hút **lệch
  tâm 8 mm** → thả ô A (cách thành khay 3 mm) → hộp đè thành, trượt sang ô B. **Bước kiểm chứng bằng
  camera bắt được** ("red_box đang ở ô B, không phải ô A") thay vì báo thành công giả.
- Kiểm tra giả thuyết: dời platform qua 6 tư thế quan sát → kết quả y hệt → không phải robot che, mà là
  **vật che vật**.
- Sửa: ngưỡng 0.85 → **0.90** (dữ liệu 8.4: bỏ sót ước lượng tệ 1/29 → 0/29, báo nhầm 10 → 12/143).
  Hộp đỏ bị coi là "chưa rõ" → vòng `don` gắp các vật khác trước, quan sát lại, lúc đó hộp đỏ đã lộ ra
  → gắp chính xác. Bố trí 4 chạy lại: thành công trọn vẹn.
- Vị trí thật, bố trí 4 (lần chạy đầu): khi lấy hộp đỏ khỏi ô C, trụ xanh ở ô A **văng khỏi bàn**.
  Không lặp lại ở lần chạy 10 bố trí. Nguyên nhân chưa rõ (nghi platform rộng 5 cm đè cả vật bên cạnh
  + xung lực tiếp xúc của bộ giải pgs, xem Bước 6.1) — ghi nhận như hạn chế của mô phỏng.

## Thiết kế đáng nêu trong báo cáo
- Tách **nhận thức** (camera → bộ lập kế hoạch) khỏi **phần cứng mô phỏng** (giác hút dùng vật lý/ground
  truth để quyết định hút được hay không) — giống hệ thật: giác hút không "biết" vị trí vật.
- Vật lơ lửng không đo được bằng mô hình "vật nằm trên bàn" → "đã nhấc lên" kiểm chứng bằng cảm biến
  giác hút; "đã thả đúng chỗ" kiểm chứng lại bằng camera.
- Quan sát ở tư thế không che + chỉ dùng khung ảnh chụp sau khi robot dừng + chỉ dùng ước lượng tin cậy
  + quan sát lại sau mỗi vật → xử lý được cả che khuất do robot lẫn do vật khác.

---

# Cảnh LON — thí nghiệm lại sau Bước 10b (2026-09-29)

Cảnh đã đổi từ ba khối vuông sang **ba lon nước ngọt** (tỉ lệ k = 3.0) và **ba khay phân loại theo
chủng loại**, nên mọi số liệu ở phần trên là của cảnh cũ. Chạy lại `run_pick_place_trials.py 5 2026
camera`.

## Kết quả cuối

| | camera |
|---|---|
| Lon vào **đúng khay của nó** | **15/15** |
| Lượt `don` trọn vẹn | **5/5** |
| Lon về chỗ cũ (≤ 10 mm) | **15/15** |
| Lượt `reset` trọn vẹn | **5/5** |
| Sai số về chỗ cũ | TB **5.5 mm**, trung vị 5.9, max **7.1 mm** |
| Thời gian mỗi lượt | 106 s (`don`) + 111 s (`reset`) |

Không một lỗi nào trong cả 5 bố trí.

## Ba lỗi đã tìm ra và sửa trong đợt này

Ba bố trí ngẫu nhiên trong năm rơi trúng cùng một kiểu hỏng, nhưng do **ba nguyên nhân khác nhau** —
mỗi nguyên nhân chỉ lộ ra sau khi sửa xong nguyên nhân trước.

### 1. Tỉ lệ màu danh nghĩa đã lỗi thời

`visible = diện tích màu / (hình bóng × color_fraction)`. Ba hằng số khai báo 0.43 / 0.39 / 0.39 đo
từ trước khi sửa lỗi gộp mảnh và trước khi nắp lon đổi sang trắng nhám. Đo lại bằng
`scripts/measure_color_fraction.py` (9 vị trí trong tầm với): **0.67–0.80 / 0.56–0.71 / 0.55–0.71**.
Sai gần gấp đôi → `visible` phồng lên ~1.87 → **cờ tin cậy mất tác dụng hoàn toàn**.

Phát hiện phụ đáng ghi: tỉ lệ này **không phải hằng số**. Phép đóng hình thái học (kernel 5 px) lấp
một phần vành nhãn trắng; lon càng XA camera ảnh càng nhỏ, vành càng bị lấp → tỉ lệ màu càng cao
(hồi quy theo diện tích hình bóng: R² ≈ 0.75, dư sai tới 0.04). Chọn giá trị **nhỏ nhất** đo được để
lon lành lặn không bao giờ bị từ chối; đổi lại cờ chỉ bắt được mức che > ~25%.

### 2. Quy tắc gộp mảnh quá lỏng

Đo bằng `scripts/measure_occlusion.py` (cho một lon đứng chắn trước lon khác rồi dịch dần sang ngang):

| quy tắc gộp | kết quả |
|---|---|
| khung bao **chạm** cửa sổ | vành logo đỏ của lon khác chỉ cần chạm 1 px là bị gộp → khung bao nở 30 → 73 px, sai 5–6 mm, cờ vẫn OK |
| **tâm ngang** nằm trong cửa sổ | lon trong khay (gần camera hơn, gần thẳng hàng) có vành đỏ rộng 62 px so với 35 px → tâm vẫn rơi vào cột → sai **15.3 mm**, cờ vẫn OK |
| khung bao **nằm gọn** trong cửa sổ | đạt |

Cơ sở vật lý của quy tắc cuối: hình trụ đứng có bề rộng ảnh gần như không đổi theo chiều cao, nên
một mảnh **rộng hơn hẳn** chắc chắn thuộc vật khác ở gần camera hơn.

Tính chất thu được — và đây mới là điều đáng nói: **hễ cờ báo tin cậy thì sai số ≤ 5.8 mm** (dung
sai giác hút 12 mm). Trước đó không có bảo đảm nào như vậy; cờ báo OK mà sai 15 mm mới là chỗ nguy
hiểm, vì hệ thống hành động dựa trên nó.

### 3. Khay che lon — sửa ở khâu LẬP KẾ HOẠCH, không phải khâu thị giác

Ba khay đặt phía camera (bố trí này đã chọn ở 10b sau khi hai bố trí khác đều tệ hơn), nên **lon đã
vào khay che mất nửa dưới của lon còn đứng trên bàn ngay sau nó**. 2/5 bố trí rơi trúng cảnh này.

Thử cứu bằng thị giác trước: lon bị che mất mép đáy nhưng **mép trên vẫn nguyên vẹn**, mà đáy lon
vẫn tì trên mặt bàn (z đã biết) → về nguyên tắc khớp mép trên là lấy lại được vị trí. Đo thử trên
6 vị trí:

| phép khớp | sai số |
|---|---|
| mép **đáy** (đang dùng cho lon trên bàn) | 0.1 – 0.7 mm |
| mép **trên** (đang dùng cho lon trong khay) | **5 – 12 mm** |

12 mm bằng đúng dung sai giác hút → tin vào đó còn **nguy hiểm hơn là từ chối**. Lý do mép trên kém:
nó là mép của vùng **mang màu**, không phải đỉnh lon — nắp trắng, vành nhãn và phép lọc hình thái
học làm nó nhòe đi khác nhau tùy khoảng cách. (Với lon trong khay thì mép trên vẫn tốt, 1.0 mm, vì
ở đó mép đáy bị thành khay che hẳn nên không có lựa chọn nào khác để so.)

Nên bỏ hướng đó và sửa ở chỗ rẻ hơn nhiều: **lúc mọi khay còn trống thì lon nào cũng nhìn rõ** (đo
lại đúng bố trí hỏng: lệch 0.3 / 0.8 / 0.6 mm, cả ba tin cậy). Chỉ cần gắp đúng thứ tự.

`task_planner.sort_order`: nếu đường nhìn từ camera tới lon A quét qua mặt bằng khay của lon B thì
**A phải gắp trước B**; sắp xếp tô-pô theo ràng buộc đó. Cả hai bố trí hỏng đều sạch ngay.

Nhưng bố trí thứ ba lộ ra một **vòng lặp**: lon Pepsi bị khay của Coca che, mà lon Coca lại bị khay
của Pepsi che. Không thứ tự nào gỡ được. Lớp cuối là **trí nhớ quan sát**
(`task_executor._with_memory`): lon không tự di chuyển, nên dùng vị trí của lần gần nhất thấy rõ.
Chốt chặn quan trọng: trí nhớ bị **xóa ngay khi giác hút chạm vào vật** — sau khi thả, vật phải được
*nhìn thấy thật* mới kiểm chứng được, không có chuyện lấy trí nhớ ra tự xác nhận việc mình vừa làm.

## Điều rút ra

Ba lớp xếp chồng, mỗi lớp bắt thứ lớp trước bỏ sót: **cờ tin cậy** (không tin thứ nhìn không rõ) →
**thứ tự có xét tầm nhìn** (gắp trước cái sắp bị che) → **trí nhớ** (cứu trường hợp vòng lặp).

Và: **không phải lỗi thị giác nào cũng nên sửa bằng thị giác.** Ở đây khâu lập kế hoạch giải quyết
triệt để và rẻ hơn nhiều so với việc cố ước lượng một vật đang bị che.
