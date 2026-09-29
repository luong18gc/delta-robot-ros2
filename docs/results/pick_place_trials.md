# Gắp–thả dựa trên camera so với vị trí thật (Bước 9)

5 bố trí ngẫu nhiên (seed 2026), mỗi lượt `don` rồi `reset`. Chấm bằng vị trí thật (odometry Gazebo): `don` thành công khi vật nằm trong một ô riêng; `reset` thành công khi vật về chỗ cũ lệch ≤ 10 mm.

| Chế độ | Vật vào ô | Lượt `don` trọn vẹn | Vật về chỗ cũ | Lượt `reset` trọn vẹn | Thời gian TB don + reset (s) |
|---|---|---|---|---|---|
| camera | 15/15 | 5/5 | 15/15 | 5/5 | 106 + 111 |

## Lỗi gặp phải

