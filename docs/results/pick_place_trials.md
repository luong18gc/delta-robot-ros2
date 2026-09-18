# Gắp–thả dựa trên camera so với vị trí thật (Bước 9)

10 bố trí ngẫu nhiên (seed 2026), mỗi lượt `don` rồi `reset`. Chấm bằng vị trí thật (odometry Gazebo): `don` thành công khi vật nằm trong một ô riêng; `reset` thành công khi vật về chỗ cũ lệch ≤ 10 mm.

| Chế độ | Vật vào ô | Lượt `don` trọn vẹn | Vật về chỗ cũ | Lượt `reset` trọn vẹn | Thời gian TB don + reset (s) |
|---|---|---|---|---|---|
| camera | 30/30 | 10/10 | 30/30 | 10/10 | 58 + 55 |
| ground_truth | 30/30 | 10/10 | 30/30 | 10/10 | 43 + 36 |

## Lỗi gặp phải

