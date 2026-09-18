# Nhận xét kết quả đánh giá thị giác (Bước 8.4 – 8.5)

Số liệu: `vision_eval.md` (sinh tự động bởi `scripts/evaluate_vision.py`). File này viết tay.

## Độ chính xác
- **Trong vùng robot gắp được** (58 mẫu lưới): sai số ngang TB 1.13 mm, max 6.2 mm → **100% trong dung
  sai giác hút 12 mm**. Sai số lớn chỉ xuất hiện ngoài tầm với.
- **Độ lệch hệ thống** ~0.16 mm theo x → hiệu chuẩn không có sai lệch đáng kể.

## Nguyên nhân sai số lớn: che khuất một phần (Bước 8.4)
Tâm khối là tâm **phần nhìn thấy**; khi một phần vật bị che, tâm dịch theo và sai số đi theo **hướng nhìn**
(trục x):
- vật ở vùng xa, **sau platform** (x ≥ 90 mm, y ≈ 0): platform che nửa trên → ước lượng **gần** camera hơn
  thật (vd. hộp đỏ tại x = 120 mm → 100.6 mm, −19 mm);
- vật **trong khay**: thành khay trước che nửa dưới → ước lượng **xa** hơn thật (+12…+20 mm theo x) →
  vượt dung sai giác hút; riêng mặt phẳng z giả định lệch 3 mm chỉ đóng góp ~2 mm;
- platform hạ sát đỉnh vật (khe 5 mm): TB 4.6 mm (khe ≥ 15 mm: < 1.1 mm);
- vật **bị cắt mép ảnh** (góc gần camera, ngoài tầm với): TB 8.2 mm.

## Cải tiến Bước 8.5: dự đoán hình bóng vật
Hình bóng dự đoán = bao lồi ảnh các điểm bề mặt vật (vật lồi) qua mô hình camera đã hiệu chuẩn.
Kiểm chứng: vật không bị che có tỉ lệ nhìn thấy ≈ 0.99 → mô hình hình bóng khớp thực tế.
- **(b) Khớp mép trên** cho vật trong khay (mặt trên luôn lộ vì camera nhìn xuống 32°): giải Newton 2 ẩn
  (x, y) để mép trên + tâm ngang của hình bóng dự đoán trùng quan sát. Vật trong khay:
  **TB 13.4 → 1.0 mm, max 19.7 → 1.9 mm**. Chỉ kích hoạt khi ước lượng thô gần khay và kết quả nằm trong
  lòng khay → 9/9 lần đúng là vật trong khay, 0 lần kích hoạt nhầm cho vật trên bàn.
- **(a) Cờ tin cậy** = tỉ lệ nhìn thấy ≥ ngưỡng, không chạm mép ảnh (hoặc đã khớp mép trên).
  Ngưỡng ban đầu 0.85: bắt 97% ước lượng tệ (> 5 mm), báo nhầm 10/143, tin cậy max 5.65 mm.
  **Ngưỡng 0.90 (từ Bước 9)**: bắt **100%** ước lượng tệ, báo nhầm 12/143 (8%), ước lượng tin cậy
  **max 3.42 mm**. Lý do nâng: Bước 9 gặp đúng ca bị bỏ sót ở 0.85 (hộp bị vật khác che ~15%, lệch 8 mm,
  hút lệch tâm rồi thả trượt ô) — xem `pick_place_nhan_xet.md`. Cờ không sửa được vị trí vật bị platform che (không biết phần bị che) — hệ
  điều khiển nên **đưa robot tránh tầm nhìn rồi đo lại** khi gặp cờ này.

## Độ bền
- **Nhiễu Gauss**: không ảnh hưởng tới σ = 10 mức xám; σ = 20 bắt đầu giảm (99.2% nhận dạng); σ ≥ 40 tụt
  mạnh (≤ 83%). Ở σ lớn, P95 giảm lại là do **chỉ tính trên các vật còn nhận dạng được**, không phải tốt hơn.
- **Độ sáng**: ổn định từ 0.5× tới 1.6×; tối 0.3× mất 16.5% nhận dạng (ngưỡng V ≥ 40), 0.2× mất một nửa.
- Camera mô phỏng **không có nhiễu thật** (`<noise>` không tác dụng) → mọi thử nghiệm nhiễu là nhân tạo.

## Giới hạn còn lại
- Hình bóng dự đoán giả định hộp **không xoay** (yaw = 0); hộp bị xoay có diện tích khác → tỉ lệ nhìn thấy
  kém chính xác hơn.
- Khớp mép trên chỉ áp dụng cho vật trong khay; vật bị che **phía trên** (sau platform) vẫn chỉ được gắn cờ.
