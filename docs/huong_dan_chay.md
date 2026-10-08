# Hướng dẫn chạy và kiểm thử hệ thống

Mọi terminal đều phải nạp môi trường trước:

```bash
cd ~/ros2_closed_loop_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Nếu vừa sửa code thì build lại trước: `colcon build --packages-select delta_controller`

---

## A. Chuẩn bị phần cứng (làm một lần mỗi buổi)

1. **Cắm camera C270.** Kiểm tra: `python3 src/delta_controller/scripts/probe_camera.py`
2. **Bật đèn, kéo rèm.** Ánh sáng phải giống lúc chụp ảnh nền. Đây là điều kiện bắt buộc,
   không phải khuyến nghị — xem mục E.
3. **Đặt ba lon lên bàn, cách nhau ít nhất một thân lon.** Lon đứng sát nhau sẽ bị gộp thành
   một vùng và hệ sẽ từ chối cả ba (có cảnh báo, không bịa vị trí).

---

## B. Chạy bản sao số — vật thật điều khiển mô phỏng

**Terminal 1 — mô phỏng + camera thật + bản sao số:**

```bash
ros2 launch delta_controller digital_twin.launch.py
```

Thêm `gui:=false` nếu không cần cửa sổ Gazebo (nhanh hơn).

Chờ tới khi thấy dòng `Thay 3 vat: coca_can, pepsi_can, sevenup_can`.
Nếu chỉ thấy 1–2 vật thì sang mục E.

**Terminal 2 — xem tọa độ ở cả hai thế giới:**

```bash
python3 src/delta_controller/scripts/view_twin.py
```

Dịch một lon trên bàn thì cả ba cột cùng đổi. Cột **BÀN THẬT** chia cho 3 ra cột **CẢNH ẢO**;
cột **GAZEBO** là vị trí lon ảo đang thật sự nằm, đọc ngược từ mô phỏng.

**Terminal 3 — robot bám theo lon (tùy chọn):**

```bash
ros2 run delta_controller follow
ros2 run delta_controller follow --ros-args -p object:=sevenup_can   # bám lon khác
```

Đẩy lon trên bàn, robot ảo trong Gazebo đuổi theo, giữ đầu hút 60 mm trên đỉnh lon.

---

## C. Chạy gắp–thả trong mô phỏng (không cần camera thật)

**Terminal 1:**

```bash
ros2 launch delta_controller pick_place.launch.py
```

**Terminal 2:**

```bash
ros2 run delta_controller cartesian_control
```

Các lệnh hay dùng trong REPL:

| lệnh | nghĩa |
|---|---|
| `vat` | liệt kê vật và vị trí |
| `nhat coca` | gắp lon coca |
| `tha` | thả vào đúng khay của loại đó |
| `don` | phân loại cả ba lon vào ba khay |
| `reset` | đưa mọi lon về chỗ cũ |
| `nguon camera` / `nguon that` | đổi nguồn vị trí vật |
| `where` | vị trí đầu công tác hiện tại |

Chạy thí nghiệm nhiều bố trí ngẫu nhiên:

```bash
python3 src/delta_controller/scripts/run_pick_place_trials.py 5 2026
```

---

## D. Kiểm thử tự động (không cần mở Gazebo)

```bash
cd src/delta_controller && python3 -m pytest test/ -q
```

163 bài, chạy khoảng 5 giây. Phần tính toán không phụ thuộc ROS nên test được độc lập.

---

## E. Khi nhận dạng hỏng

Triệu chứng: chỉ thấy 1–2 lon, hoặc `score 0.00`, hoặc tọa độ nhảy lung tung.

**Nguyên nhân hay gặp nhất: ảnh nền không còn đúng.** Ảnh nền gắn với điều kiện chiếu sáng lúc
chụp, nên đổi đèn, kéo rèm, hoặc sang ngày khác là phải chụp lại.

Chụp lại **không cần tắt hệ**: nhấc hết lon khỏi bàn, để nguyên marker, rồi

```bash
ros2 service call /vision/capture_reference std_srvs/srv/Trigger
```

Chờ 2 giây rồi đặt lon trở lại.

Các nguyên nhân khác:

| triệu chứng | nguyên nhân | xử lý |
|---|---|---|
| `Chua khoa duoc tu the camera` | không đủ 5 marker trong khung | kiểm tra marker có bị che/bong không |
| một vùng to gấp nhiều lần lon | hai lon đứng sát nhau | tách lon ra xa |
| tọa độ nhảy rồi quay về | tay hoặc vật lạ trong khung | bình thường — các lớp lọc đang chặn |
| camera chỉ 1–2 hình/giây | còn sót node của lần chạy trước | xem mục F |

---

## F. Dọn tiến trình cũ

Phải dọn **hết** trước khi chạy lại hoặc trước khi đo, vì node cũ chạy mã cũ và cùng phát lên
`/vision/objects` làm kết quả lẫn lộn.

```bash
ps -eo pid,cmd | grep -E "gz sim|parameter_bridge|delta_controller/|robot_state_publisher|throttle" \
  | grep -v grep | awk '{print $1}' | xargs -r kill
```

⚠️ Đừng dùng `pkill -f` — mẫu tìm kiếm khớp cả chính shell đang chạy.

---

## G. Hiệu chuẩn lại (chỉ khi dời camera hoặc dán lại marker)

| việc | khi nào | lệnh |
|---|---|---|
| nội tham số | chỉ khi đổi camera | `python3 src/delta_controller/scripts/calibrate_intrinsics.py --show` |
| ngoại tham số | tự động mỗi khung, không phải làm gì | — |
| ảnh nền | mỗi khi đổi ánh sáng | xem mục E |
| đo lại sai số | sau khi dời camera | `python3 src/delta_controller/scripts/measure_real_accuracy.py` |

Ngoại tham số được giải lại ở **từng khung hình** từ marker, nên dời camera không cần hiệu chuẩn
lại — chỉ cần marker còn trong khung.
