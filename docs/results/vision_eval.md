# Đánh giá sai số thị giác (Bước 8.4)

Bộ dữ liệu: `/home/luong18gc/ros2_closed_loop_ws/datasets/vision_eval` — 172 ảnh, 172 lượt chấm vật.
Sai số = khoảng cách **ngang** (x, y) giữa vị trí camera ước lượng và vị trí thật (odometry Gazebo). Hiệu chuẩn: `/home/luong18gc/ros2_closed_loop_ws/calibration/side_camera.yaml`.

## 1. Tổng hợp

| Nhóm | Số mẫu | Nhận dạng được | TB (mm) | Trung vị | RMS | P95 | Max |
|---|---|---|---|---|---|---|---|
| Lưới — mọi điểm | 151 | 100.0% | 2.76 | 0.95 | 4.95 | 12.27 | 20.58 |
| Lưới — vật **trọn trong ảnh** | 133 | 100.0% | 2.03 | 0.77 | 3.97 | 8.43 | 20.58 |
| Lưới — vật **bị cắt mép ảnh** | 18 | 100.0% | 8.19 | 7.94 | 9.47 | 15.06 | 15.14 |
| Lưới — **trong tầm với của robot** | 58 | 100.0% | 1.13 | 0.83 | 1.66 | 3.68 | 6.16 |
| Lưới trọn trong ảnh — Hộp đỏ | 43 | 100.0% | 2.02 | 0.69 | 4.06 | 8.35 | 19.38 |
| Lưới trọn trong ảnh — Trụ xanh lá | 44 | 100.0% | 1.39 | 0.49 | 2.56 | 6.62 | 8.26 |
| Lưới trọn trong ảnh — Cầu xanh dương | 46 | 100.0% | 2.65 | 1.42 | 4.88 | 9.89 | 20.58 |
| Vật trong khay (mặt đáy cao hơn bàn 3 mm) | 9 | 100.0% | 1.01 | 0.88 | 1.08 | 1.63 | 1.91 |
| Chỉ các ước lượng **tin cậy** (mọi kịch bản) | 131 | 100.0% | 0.86 | 0.73 | 1.03 | 1.89 | 3.42 |

Độ lệch hệ thống (lưới, trọn trong ảnh): dx = +0.16 mm, dy = +0.00 mm.

## 2. Bị platform che (robot lơ lửng phía trên vật)

| Khe platform – đỉnh vật (mm) | Số mẫu | Nhận dạng được | TB (mm) | Trung vị | RMS | P95 | Max |
|---|---|---|---|---|---|---|---|
| 60 | 3 | 100.0% | 0.88 | 0.93 | 0.90 | 1.08 | 1.10 |
| 30 | 3 | 100.0% | 0.79 | 0.73 | 0.81 | 1.01 | 1.04 |
| 15 | 3 | 100.0% | 0.81 | 0.72 | 0.83 | 1.06 | 1.10 |
| 5 | 3 | 100.0% | 4.57 | 5.97 | 5.59 | 7.46 | 7.63 |

## 3. Trước / sau cải tiến Bước 8.5 (khớp mép trên cho vật trong khay)

| Nhóm | TB trước (mm) | Max trước | TB sau (mm) | Max sau |
|---|---|---|---|---|
| Lưới — trong tầm với | 1.13 | 6.16 | 1.13 | 6.16 |
| Lưới — mọi điểm | 2.76 | 20.58 | 2.76 | 20.58 |
| Vật trong khay | 13.44 | 19.74 | 1.01 | 1.91 |
| Platform sát vật (khe 5 mm) | 4.57 | 7.63 | 4.57 | 7.63 |

## 4. Cờ tin cậy (tỉ lệ nhìn thấy ≥ 0.90, không chạm mép ảnh, hoặc đã khớp mép trên)

- Ước lượng **tệ** (sai số > 5 mm): 29 — bị gắn *không tin cậy*: **100%**.
- Ước lượng **tốt** (≤ 5 mm): 143 — bị gắn nhầm *không tin cậy*: 8%.
- Sai số lớn nhất trong các ước lượng được gắn *tin cậy*: **3.42 mm**.
- Phương pháp dùng: 9 lần khớp mép trên, 163 lần tâm khối.

## 5. Độ bền với nhiễu Gauss (lưới, vật trọn trong ảnh)

| σ (mức xám) | Số mẫu | Nhận dạng được | TB (mm) | Trung vị | RMS | P95 | Max |
|---|---|---|---|---|---|---|---|
| 0 | 133 | 100.0% | 2.03 | 0.77 | 3.97 | 8.43 | 20.58 |
| 5 | 133 | 100.0% | 2.02 | 0.76 | 3.97 | 8.56 | 20.58 |
| 10 | 133 | 100.0% | 2.07 | 0.81 | 4.05 | 8.72 | 20.47 |
| 20 | 133 | 99.2% | 3.09 | 1.66 | 5.53 | 11.58 | 26.22 |
| 30 | 133 | 93.2% | 4.36 | 3.16 | 6.01 | 12.95 | 21.05 |
| 40 | 133 | 82.7% | 6.67 | 4.52 | 9.02 | 20.33 | 33.63 |
| 60 | 133 | 57.9% | 7.52 | 6.95 | 8.26 | 14.20 | 17.55 |

## 6. Độ bền với thay đổi độ sáng (lưới, vật trọn trong ảnh)

| Hệ số sáng | Số mẫu | Nhận dạng được | TB (mm) | Trung vị | RMS | P95 | Max |
|---|---|---|---|---|---|---|---|
| 0.2 | 133 | 52.6% | 21.19 | 19.65 | 23.02 | 36.53 | 42.75 |
| 0.3 | 133 | 83.5% | 3.97 | 3.33 | 5.28 | 8.22 | 31.90 |
| 0.5 | 133 | 100.0% | 2.04 | 0.80 | 3.99 | 8.47 | 20.58 |
| 0.7 | 133 | 100.0% | 2.03 | 0.78 | 3.97 | 8.43 | 20.58 |
| 1.0 | 133 | 100.0% | 2.03 | 0.77 | 3.97 | 8.43 | 20.58 |
| 1.3 | 133 | 100.0% | 2.03 | 0.78 | 3.97 | 8.43 | 20.58 |
| 1.6 | 133 | 100.0% | 1.98 | 0.74 | 3.96 | 8.44 | 20.58 |
| 2.0 | 133 | 100.0% | 3.59 | 1.04 | 5.39 | 9.03 | 20.58 |

Nhận xét và phân tích nguyên nhân: `docs/results/vision_eval_nhan_xet.md`.
