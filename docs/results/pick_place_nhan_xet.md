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
