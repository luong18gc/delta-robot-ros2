# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Đồ án tốt nghiệp — Ứng dụng thị giác máy tính trong điều khiển Robot delta

## Bối cảnh

**Tên đề tài (kỹ sư hệ 4.5 năm): "Ứng dụng thị giác máy tính trong điều khiển Robot delta".**

Mục tiêu cuối: lấy tín hiệu từ **camera thật bên ngoài** để điều khiển robot delta **trong mô phỏng**
ROS 2/Gazebo. Phần động học, quỹ đạo, gắp–thả đã làm là **nền**; **thị giác máy tính là trọng tâm** mà
hội đồng chấm. Workspace dựa trên repo `LevinTamir/ros2_closed_loop_ws` (mô phỏng robot mạch động học
kín trong Gazebo).

**Điểm nối cho phần thị giác:** vị trí vật hiện vào hệ điều khiển qua `/objects/<vật>/odometry`
(ground truth từ Gazebo). Kết quả nhận dạng từ camera nên đi vào đúng chỗ này (topic tương đương hoặc
lớp chọn nguồn), không sửa logic gắp–thả; giữ ground truth để **đo sai số nhận dạng**. Phát triển với
camera mô phỏng trước (có ground truth), rồi mới sang camera thật.

Phần cứng/phần mềm sẵn có trên máy (cập nhật 2026-09-28): webcam tích hợp `/dev/video0`, `/dev/video1`
(nhìn vào người, **không dùng được** cho đồ án); OpenCV 4.6 (Python); `cv_bridge`, `image_transport`
của ROS Jazzy; **`v4l-utils`** (lệnh `v4l2-ctl`, cài 2026-09-28). **Chưa có** `usb_cam`/`v4l2_camera`,
chưa có thư viện ArUco/AprilTag cho ROS (OpenCV tự có `cv2.aruco`, đang dùng cái này).
Camera cho Bước 10: xem mục "Camera thật" ở phần Tiến độ.

Người làm đồ án giao tiếp bằng **tiếng Việt**. Trả lời bằng tiếng Việt.

## Môi trường

- Ubuntu 24.04
- ROS 2 **Jazzy** (`source /opt/ros/jazzy/setup.bash`)
- Gazebo **Harmonic** (`gz sim`, KHÔNG phải Gazebo Classic)
- Workspace: `~/ros2_closed_loop_ws`
- RAM 7.6GB + 4GB swap → build nặng phải dùng `--executor sequential --parallel-workers 1`
- Git remote: `origin` = repo **private** của người làm đồ án
  `https://github.com/luong18gc/delta-robot-ros2` (sao lưu: commit xong `git push`);
  `upstream` = repo gốc `LevinTamir/ros2_closed_loop_ws` (chỉ để tham khảo, **không push**).

## Cấu trúc workspace

```
src/
├── closed_loop_description/   # URDF/xacro + mesh robot delta (từ repo gốc)
├── closed_loop_bringup/       # launch file + world (từ repo gốc)
├── joint_state_transformer/   # submodule HIT-Robotics: tính khớp bị động bằng Levenberg-Marquardt
├── robot_model/               # submodule HIT-Robotics
├── pinocchio/                 # submodule stack-of-tasks: thư viện động học C++
├── urdfdom/ urdfdom_headers/  # submodule HIT-Robotics (fork, hỗ trợ constraint mạch kín)
└── delta_controller/          # ⭐ PACKAGE TỰ VIẾT cho đồ án (ament_python)
```

**Lưu ý:** `closed_loop_moveit_config` từng tồn tại (do làm theo hướng dẫn khác) nhưng **đã xóa**
vì không thuộc repo gốc và gây lỗi. Không tạo lại trừ khi có lý do rõ ràng.
Hệ quả: các file `closed_loop_bringup/launch/*_moveit.launch.py` vẫn còn và **vẫn tham chiếu
package đã xóa** → chạy sẽ lỗi. Chỉ dùng `3dof_delta.launch.py` (không có MoveIt).

`delta_controller` hiện gồm:
- `joint_commander.py` — class `JointCommander` (không phải node), giữ 3 publisher `cmd_pos`,
  hàm `send(j1, j2, j3)`. Mọi node điều khiển nên dùng lại class này.
- `interactive_control_node.py` — node REPL nhập góc khớp, entry point `manual_control`.
- `delta_kinematics.py` — IK + FK thuần Python (không import ROS). FK = giao 3 mặt cầu tâm
  `C_i = khuỷu_i − e·u_i`, bán kính `re`, chọn nghiệm z nhỏ hơn; vòng IK→FK sai số ~1e-13.
- `trajectory.py` — thuần Python: đoạn thẳng với biên dạng bậc 5 (min-jerk, `v_max = 1.875·L/T`),
  `safe_waypoints` (nâng → ngang → hạ quanh `safe_z`), `plan_path` giải IK **toàn bộ** quỹ đạo
  trước khi chạy (điểm giữa đường ngoài tầm với → báo lỗi, robot chưa động).
- `cartesian_control_node.py` — node REPL, entry point `cartesian_control`. Lệnh: `x y z` (đi thẳng),
  `safe x y z`, `jump x y z` (gửi thẳng góc, để so sánh), `home` (đi safe), `where` (FK từ
  `/joint_states`), `state`, `speed v`. Tham số ROS: `max_speed` 0.05, `rate_hz` 50, `safe_z` -0.16.
  Điểm xuất phát quỹ đạo = FK của góc **đo được** (không phải lệnh cuối) → đúng cả khi bị vật chặn.
  Phát điểm theo đồng hồ thật (sim chạy RTF ≈ 1.0). Spin ở luồng phụ vì `input()`/vòng quỹ đạo
  chặn luồng chính. `rclpy.init(signal_handler_options=NO)` để Ctrl+C chỉ dừng quỹ đạo — handler
  mặc định của rclpy shutdown context.
- Topic `cmd_pos` không lưu lịch sử: publish trước khi bridge subscribe xong là **mất lệnh**
  (đã gặp khi pipe lệnh vào node vừa khởi động). Dùng `JointCommander.wait_for_connection()`.
- `gripper_logic.py` — thuần Python: `select_graspable` chỉ cho hút khi lệch ngang ≤ 12 mm và khe
  (mặt dưới platform − đỉnh vật) trong [-4, +6] mm; báo lỗi kèm gợi ý tọa độ.
- `gripper_node.py` (entry `gripper`) — dịch vụ `/gripper/grip`, `/gripper/release` (std_srvs/Trigger),
  topic latched `/gripper/held_object`. Vị trí platform = FK(`/joint_states`); vị trí vật =
  `/objects/<vật>/odometry` (OdometryPublisher trong world, pose world → trừ base_z 1.0).
  MultiThreadedExecutor + ReentrantCallbackGroup vì service chờ callback trạng thái.
- `launch/pick_place.launch.py` — include `3dof_delta.launch.py` (world `delta_objects_world`)
  + bridge riêng cho gripper/odometry + `gripper`. Danh sách vật đọc từ `scene.py`.
- `cartesian_control` có thêm `grip`/`release`; khi đang giữ vật, `safe` dùng `safe_z_holding` -0.14.
- `scene.py` — **nguồn duy nhất phía ROS** cho vật (tên model, nửa kích thước, tên tắt, `home_xy`,
  `color`, `shape`, `color_fraction`, `color_top_margin`), `SCALE` = 3.0, bàn `TABLE_Z`, ba khay
  `BINS` (mỗi loại một khay) + `BIN_LAYOUT`, và cảnh cũ `LEGACY_OBJECTS` / `LEGACY_BIN_LAYOUT`.
  Launch, `gripper_node`, planner, khối thị giác đều đọc. Xem mục "Bước 10b" ở phần Tiến độ.
- `task_planner.py` — thuần Python: lệnh cấp cao → chuỗi `Move`/`Grip`/`Release` từ vị trí **thật**
  của vật; `sort_order` = thứ tự phân loại **có xét tầm nhìn** (xem Bước 10b); `touch_point` = đỉnh vật + 0.003, `release_point` = đáy khay + 5 mm + cao vật + 0.003;
  `locate` (tren ban / o A / trong khay / dang giu), `check_reachable` kiểm IK mọi đích trước khi chạy.
- `task_executor.py` — chạy kế hoạch trên node + **kiểm chứng bằng odometry vật** (pick: vật phải
  nhấc lên ≥ 10 mm; place: vật phải nằm trong ô). `pickplace` kiểm ô trống **trước khi** nhặt;
  `sort` lập lại kế hoạch sau mỗi vật. Lệnh REPL: `objects|vat`, `goto|den`, `pick|nhat`,
  `place|tha` (vào ĐÚNG khay của loại đó), `pickplace|chuyen <vat>`, `sort|don` (PHÂN LOẠI),
  `unload|lay_ra <vat> [x y]`, `reset`.
  `lay_ra`: đặt ra bàn tại `table_release_point` (mặt bàn + 5 mm + cao vật + 0.003 = -0.182),
  `check_table_spot` từ chối điểm chồng khay (tính cả thành + 5 mm) hoặc cách tâm vật khác < 35 mm —
  kiểm tra **trước khi** nhặt; kiểm chứng: vật "tren ban", lệch ≤ 10 mm. `reset` = lay_ra mọi vật
  trong khay về `home_xy`. `_objects()` **chờ đủ vị trí mọi vật** (≤ 3 s): lệnh gõ ngay khi node
  vừa khởi động từng thấy danh sách rỗng → báo nhầm "Khong con vat nao tren ban".
- `color_detector.py`, `vision_node.py` (entry `vision`) — nhận dạng vật theo màu (Bước 8.2),
  đổi ra tọa độ robot khi có file hiệu chuẩn (Bước 8.3).
- `camera_model.py`, `calibrate_camera_node.py` (entry `calibrate_camera`) — hiệu chuẩn ArUco + PnP (Bước 8.3).
- `vision_eval.py` + `scripts/record_vision_dataset.py`, `scripts/evaluate_vision.py` — đánh giá sai số (Bước 8.4).
- `vision_estimation.py` — ước lượng có xét che khuất: hình bóng dự đoán, khớp **mép trên** (vật
  trong khay) và **mép đáy** (vật nhiều màu trên bàn), `color_shape` (bỏ nắp không mang màu), cờ tin cậy.
- `object_detector.py` — nhận dạng kiểu TÁCH NỀN TRƯỚC rồi phân loại từng vùng. CHƯA nối vào node
  `vision`: trong mô phỏng, ba khay xám cũng là "không phải mặt bàn" nên lon trong khay dính liền
  với khay thành một vùng và bị loại. Để dành cho camera THẬT (nền bàn đen trơn, có thể giới hạn ROI).
- `cartesian_control`: `object_source` camera (mặc định) | ground_truth, lệnh `nguon`; `scripts/run_pick_place_trials.py` (Bước 9).
- `scripts/probe_camera.py`, `scripts/make_chessboard_pdf.py`, `scripts/make_marker_pdf.py`
  (`--sim` cho bố trí ảo, mặc định là bố trí BÀN THẬT) — chuẩn bị camera thật (Bước 10).
- `scripts/measure_color_fraction.py` — đo `SceneObject.color_fraction` (dời vật qua 9 vị trí);
  `scripts/measure_occlusion.py` — đo độ nhạy của cờ tin cậy khi lon che lon.
- `test/` — lint + `test_delta_kinematics.py`, `test_trajectory.py`, `test_gripper_logic.py`,
  `test_task_planner.py`, `test_color_detector.py`, `test_camera_model.py`, `test_vision_eval.py`,
  `test_vision_estimation.py`, `test_task_executor.py` (ảnh mẫu trong `test/data/`).

### Giác hút ảo (DetachableJoint) — những điều đã kiểm chứng
- **4 DetachableJoint đóng mạch kín dùng topic mặc định chung**
  `/model/delta_3dof/detachable_joint/{attach,detach}` → publish nhầm vào đó đứt cả mạch kín.
  Giác hút (`urdf/3dof_delta.gripper.xacro`, 1 plugin/vật) dùng topic `/delta_3dof/gripper/<vật>/…`.
- Plugin gz-sim8 **tự attach khi khởi động** (không có tùy chọn tắt) → lúc đó robot bị 3 vật
  (đang tì trên bàn) giữ cứng. `gripper_node` gửi detach tới khi nhận `"detached"`.
  Topic `state` chỉ publish **khi đổi trạng thái**. Restart `gripper_node` khi đang giữ vật → vật rơi.
- Attach **giữ nguyên vị trí tương đối** lúc gắn (không giật vật về tool0); vật theo robot đúng từng mm.
- Bridge `/world/<w>/pose/info` → `tf2_msgs/TFMessage` **mất tên model** (child_frame_id rỗng) →
  dùng OdometryPublisher cho từng vật.
- Thêm vật mới: sửa 3 chỗ — world SDF (model + OdometryPublisher), `3dof_delta.gripper.xacro`,
  `OBJECTS` trong `delta_controller/scene.py`.
- Khi viết script test điều khiển REPL qua pipe: dấu nhắc `Nhap lenh > ` **không có xuống dòng** →
  đọc stdout theo dòng sẽ treo; đọc theo byte (`os.read`) + `PYTHONUNBUFFERED=1`.
- Đo quỹ đạo thật trong Gazebo: `gz topic -e -t /world/delta_world/dynamic_pose/info` có pose
  `tool0` tần số cao (z world − 1.0). Cẩn thận `pkill -f 'gz sim'` trong Bash tool: pattern khớp
  chính shell đang chạy → tự kill shell, không kill được sim; kill theo PID.

Muốn thêm node mới chạy bằng `ros2 run` phải khai báo trong `entry_points` của `setup.py` rồi build lại.

## Kiến trúc mô phỏng mạch kín (đọc README + `*.gazebo.xacro` + launch để hiểu)

- URDF chỉ mô tả được **cây**, nên mạch kín được đóng **lúc chạy** bằng plugin Gazebo
  `DetachableJoint` (hàn 2 link lại sau khi spawn). Hai link được hàn có frame **trùng nhau tại
  home pose** → nếu đổi hình học/home pose trong xacro thì mối hàn sẽ bị giật hoặc hỏng.
- Mỗi thanh chống có khớp cầu ở 2 đầu (= weld + chuỗi 3 khớp revolute). Platform treo trên chuỗi
  **3 khớp prismatic X-Y-Z bị động** → luôn nằm ngang, đúng 3 DOF tịnh tiến. Có thể đọc trực tiếp
  vị trí platform từ các khớp prismatic này để kiểm chứng FK/IK trong mô phỏng (nếu được publish).
- Khớp chủ động được điều khiển bằng `JointPositionController` (PID, trong `3dof_delta.gazebo.xacro`).
- `/joint_states` **chỉ chứa khớp chủ động** (lọc giống encoder thật). Launch bridge topic Gazebo
  `/world/delta_world/model/delta_3dof/joint_state` → `/joint_states`; tên world `delta_world` và
  tên model `delta_3dof` bị hardcode trong launch — đổi world thì phải sửa cả hai chỗ.
- Bridge `ros_gz_bridge` chỉ khai báo `/clock`, 3 topic `cmd_pos` và joint state. Topic mới giữa
  ROS ↔ Gazebo (vd. vật thể, attach/detach cho gắp–thả ở Bước 6) phải thêm vào `parameter_bridge`
  trong `3dof_delta.launch.py`.
- World gốc `delta_world.sdf` (physics DART) **dùng chung với delta 4-DOF** → không sửa.
  Vật thể đặt trong `delta_objects_world.sdf` (bản sao + bàn + vật), vẫn giữ `<world name="delta_world">`
  để topic hardcode trong launch còn đúng. Sửa file world xong phải
  `colcon build --packages-select closed_loop_description` (world được copy vào `install/`).
- ⚠️ **Chỉ `tool0` có `<collision>`** (hộp 0.05×0.05×0.006, thêm cho đồ án); mọi link khác chỉ có
  visual → cánh tay/thanh chống vẫn đi xuyên bàn/vật. Sửa URDF phải build lại
  `closed_loop_description` **và khởi động lại mô phỏng** (URDF chỉ đọc lúc spawn).
  Kết quả đo va chạm platform (world `delta_objects_world`, 2026-09-15):
  - đứng yên ở home: không rung (z ổn định tới 0.1 mm)
  - đẩy ngang hộp đỏ: hộp dịch đúng như tính (0.060 → 0.069, dự kiến 0.070), không rung
  - ép xuống bàn tĩnh: bị chặn đúng tại z = -0.217, không rung
  - **ép xuống vật động nằm trên bàn** (hộp, trụ, cầu đều vậy): platform **lún dần** vào vật
    (~5–8 mm, còn tăng chậm), vật không hỏng. Không phải do hình trụ–trụ (đã thử đổi platform
    trụ → hộp, vẫn lún). Nghi do vật nhẹ 50 g bị kẹp giữa lực PID lớn và bàn, bộ giải `pgs` không
    giải nổi chồng tiếp xúc — **chưa kiểm chứng**.
    ⇒ Khi gắp: hạ platform tới đúng đỉnh vật (`tool0` z ≈ đỉnh + 0.003) rồi attach, **không ra lệnh
    thấp hơn đỉnh vật**.

## Cách chạy (đã kiểm chứng hoạt động)

**Terminal 1 — khởi động mô phỏng:**
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_closed_loop_ws/install/setup.bash
ros2 launch closed_loop_bringup 3dof_delta.launch.py
```

**Terminal 2 — gửi lệnh khớp (baseline, đã chạy được):**
```bash
ros2 topic pub -1 /delta_3dof/Chain1_1/cmd_pos std_msgs/msg/Float64 "{data: 0.4}"
ros2 topic pub -1 /delta_3dof/Chain2_1/cmd_pos std_msgs/msg/Float64 "{data: 0.4}"
ros2 topic pub -1 /delta_3dof/Chain3_1/cmd_pos std_msgs/msg/Float64 "{data: 0.4}"
```

**Build:**
```bash
cd ~/ros2_closed_loop_ws
source /opt/ros/jazzy/setup.bash
colcon build --executor sequential --parallel-workers 1
```

Nếu build lại `pinocchio` (rất nặng RAM, ~11 phút) cần thêm:
```
--cmake-args -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O1" \
  -DBUILD_PYTHON_INTERFACE=OFF -DBUILD_TESTING=OFF -DBUILD_UTILS=OFF \
  -DBUILD_EXAMPLES=OFF -DBUILD_WITH_COLLISION_SUPPORT=OFF
```

**Làm việc hằng ngày — chỉ build/test package tự viết (tránh đụng pinocchio):**
```bash
colcon build --packages-select delta_controller
source install/setup.bash
ros2 run delta_controller manual_control            # node nhập góc khớp
ros2 run delta_controller cartesian_control         # node nhập x y z (IK)

colcon test --packages-select delta_controller && colcon test-result --verbose
python3 -m pytest src/delta_controller/test/test_flake8.py   # chạy một file test
```
Code Python (IK, v.v.) không phụ thuộc ROS nên test được bằng `pytest` thuần, không cần mở Gazebo.

## Kiến thức về robot (QUAN TRỌNG — đã phân tích kỹ)

Đây là **rotary delta** (delta dạng quay, kiểu Clavel), KHÔNG phải linear/prismatic delta.
Khớp `ChainN_1` là `revolute` → lệnh `cmd_pos` là **góc quay (radian)**, không phải khoảng cách.

### Thông số hình học (trích từ `3dof_delta.urdf.xacro`, đơn vị mét)

| Ký hiệu | Ý nghĩa | Giá trị | Nguồn trong URDF |
|---|---|---|---|
| `f`  | Bán kính đế | **0.0417** | origin joint `Chain1_1` |
| `e`  | Bán kính platform | **0.0276** | origin joint `Chain1_cl_A` |
| `rf` | Chiều dài cánh tay trên | **0.0758** | origin joint `Chain1_top_A` |
| `re` | Chiều dài thanh chống (forearm) | **0.1668** | origin `Chain1_tip_joint` |

- Góc pha 3 chân: φ₁=0°, φ₂=120°, φ₃=240°
- Giới hạn khớp: `[-1.0297442586766543, 1.4311699866353502]` rad
- **Home position:** θ₁=θ₂=θ₃=0 ⟺ platform tại `(0, 0, -0.1405)` — dùng làm điểm kiểm chứng chuẩn

### Hệ trục tọa độ

- Gốc O tại tâm `base_link`
- Trục X hướng ra chân 1 (φ=0°)
- Trục Z hướng **lên trên** → platform nằm dưới nên `z0` luôn **âm**
- Trục Y theo quy tắc bàn tay phải
- θᵢ = 0 ⟺ cánh tay trên nằm ngang hướng ra ngoài; θᵢ tăng → cánh tay hạ xuống

### Công thức IK (closed-form, đã tự kiểm chứng đúng)

Với mỗi chân i:
```
x_i = x0·cos(φᵢ) + y0·sin(φᵢ)
y_i = -x0·sin(φᵢ) + y0·cos(φᵢ)
z_i = z0

a_i = (x_i + e) - f
K_i = a_i² + y_i² + z_i² + rf² - re²

A = -2·rf·a_i
B =  2·rf·z_i
C =  K_i
```
Giải phương trình `A·cos(θ) + B·sin(θ) + C = 0` bằng phép thế Weierstrass `t = tan(θ/2)`:
```
(C-A)t² + 2Bt + (A+C) = 0
t = [-B ± √(A² + B² - C²)] / (C - A)
θ = 2·arctan(t)
```
**Chọn nghiệm theo nhánh "khuỷu ra ngoài"** (liên tục với home), tức nghiệm thỏa
`-A·sin(θ) + B·cos(θ) ≤ 0`, rồi mới kiểm tra giới hạn khớp. Không chọn đơn thuần "nghiệm trong
giới hạn": xét riêng một chân vẫn có điểm mà cả 2 nghiệm đều trong giới hạn (vd. chân 1 tại
x=-0.09, z=-0.02 → θ≈0.641 hoặc θ≈-1.020). Quét lưới cho thấy các điểm đó luôn nằm ngoài tầm với
của chân khác, nên trên không gian làm việc thật hai quy tắc cho cùng kết quả.

**Đã kiểm chứng:** thay home position vào → `A + C = 0` → t=0 → θ=0 ✓ khớp đúng URDF.

**Cạm bẫy đã gặp:** ban đầu viết nhầm `a_i = (x_i - e) - f` → ra Z=-0.0823 thay vì -0.1405.
Dấu đúng là `(x_i + e)`. Luôn kiểm chứng bằng home position trước khi tin công thức.

### Nguồn tham khảo học thuật

- Clavel, R. — US Patent 4,976,582 (1990) — phát minh gốc delta robot
- Williams II, R.L. "The Delta Parallel Robot: Kinematics Solutions" (2016),
  https://people.ohio.edu/williams/html/PDF/DeltaKin.pdf — công thức IK/FK chuẩn

## Tiến độ

### Đã xong
- [x] Cài ROS 2 Jazzy + Gazebo Harmonic trên Ubuntu 24.04
- [x] Clone repo (kèm `--recurse-submodules`), build sạch 7/7 package
- [x] Chạy mô phỏng, điều khiển robot qua topic `cmd_pos` — robot di chuyển OK
- [x] Tạo package `delta_controller`, viết `joint_commander.py` + `interactive_control_node.py`
      (node tương tác cho nhập 3 giá trị khớp liên tục, không cần gõ `ros2 topic pub` mỗi lần)
- [x] **Bước 1** — Xác định thông số hình học robot
- [x] **Bước 2** — Xây dựng công thức IK closed-form + kiểm chứng bằng tay

- [x] **Bước 3** — `delta_controller/delta_kinematics.py` (IK thuần Python, không phụ thuộc ROS)
      + `test/test_delta_kinematics.py` (home, ràng buộc độ dài `re`, đối xứng, chọn nhánh,
      điểm ngoài tầm với) — 28/28 pass (2026-09-15)

- [x] **Bước 4** — `cartesian_control` (2026-09-15). Kiểm chứng trong Gazebo: 9 điểm (home,
      trục Z, lệch X/Y, điểm xa (-0.04,-0.03,-0.19)) → vị trí `tool0` đo được lệch **< 1 mm**.

### Cách đo vị trí platform thật trong Gazebo (để kiểm chứng IK/FK)
`/joint_states` không có khớp `platform_x/y/z`, nên đọc pose link trực tiếp:
```bash
gz model -m delta_3dof -l tool0      # mục "Pose" là tọa độ world
```
`base_link` nằm tại world z = **1.0** → vị trí so với đế = pose − (0, 0, 1.0).
Ở home đo được z ≈ -0.1405…-0.1414 (võng nhẹ do trọng lực + PID).
Vùng với tới: người làm đồ án tự thử x, y = 0.1 trên Gazebo vẫn tới được; theo tính toán,
bán kính với tới mọi hướng ≈ 0.128 tại z=-0.14, 0.096 tại z=-0.19, 0 tại z=-0.24.

- [x] **Bước 5** — `delta_objects_world.sdf` (2026-09-15). Kiểm chứng: vật đứng yên trên bàn,
      robot tới phía trên cả 3 vật (sai lệch ~1–1.5 mm khi tay duỗi xa).
      ```bash
      ros2 launch closed_loop_bringup 3dof_delta.launch.py world_name:=delta_objects_world
      ```
      Tọa độ trong **hệ robot** (world z − 1.0), đơn vị m; vật cao 0.03, mặt bàn z = -0.22:

      | Model Gazebo | Hình | Tâm vật | Đỉnh vật |
      |---|---|---|---|
      | `red_box` | hộp 3 cm | (0.06, 0, -0.205) | z = -0.19 |
      | `green_cylinder` | trụ r=1.5 cm | (-0.03, 0.052, -0.205) | z = -0.19 |
      | `blue_sphere` | cầu r=1.5 cm (+ đế chống lăn vô hình) | (-0.03, -0.052, -0.2045) | z = -0.1895 |

      Platform dày 6 mm (±3 mm quanh `tool0`) → chạm đỉnh vật khi `tool0` z ≈ -0.187.

### Đang làm
- (chưa có)

### Hướng tiếp theo — thị giác máy tính (trọng tâm đề tài, chưa bắt đầu)
Quyết định của người làm đồ án (2026-09-17):
- Kịch bản: **cả hai** — (1) **bản sao số** làm chính: vật thật trên bàn thật → camera nhận dạng →
  vật ảo trong Gazebo đặt đúng vị trí tương ứng → robot tự gắp–thả; (2) chế độ **bám theo tay/marker**
  để demo.
- Camera thật: **chưa chọn** → thiết kế để đổi nguồn ảnh dễ dàng (camera mô phỏng / webcam / khác).
- **Làm với camera mô phỏng trong Gazebo trước** (có ground truth để đo sai số), rồi mới sang camera thật.

Lộ trình dự kiến (từng bước, hỏi lại trước quyết định lớn):
- [x] **Bước 8** — Camera mô phỏng (8.1–8.5 xong 2026-09-18).
  - [x] 8.1 Camera nhìn xiên (2026-09-17). Model `side_camera` trong `delta_objects_world.sdf`
    (+ plugin `gz-sim-sensors-system`, ogre2). Pose world **ground truth**: xyz (-0.40, 0, 1.03),
    rpy (0, 0.558599, 0) = nhìn xuống 32°, đặt hướng 180° (giữa chân 2 và 3, cánh tay ít che nhất);
    hệ robot (-0.40, 0, 0.03). 640×480, hfov 45° → fx = fy ≈ 772.5, cx 320, cy 240; 10 Hz; khai báo
    nhiễu gauss σ 0.007 nhưng **đo được là không có tác dụng** (xem 8.3); frame_id `side_camera` (thẻ `<gz_frame_id>`, `gz sdf -k` cảnh báo nhưng chạy đúng).
    Topic ROS: `/side_camera/image` (rgb8), `/side_camera/camera_info` (bridge trong
    `pick_place.launch.py`). Ảnh thấy trọn 3 vật + khay + platform; **có bóng đổ của robot** trên bàn
    (thử thách cho nhận dạng màu). Xem ảnh: `ros2 run rqt_image_view rqt_image_view /side_camera/image`.
  - [x] 8.2 Nhận dạng vật theo màu (2026-09-18). `color_detector.py` (thuần Python + OpenCV):
    BGR→HSV → `inRange` → mở/đóng hình thái học → vùng liên thông ≥ 30 px → **gộp mọi mảnh cùng màu**
    (mỗi màu = đúng 1 vật, bị che cắt đôi vẫn là 1) → tâm khối phần nhìn thấy + khung bao. Ngưỡng
    (H 0–180): đỏ [0,8]∪[172,180], xanh lá [45,85], xanh dương [95,125]; S ≥ 90–100 (loại bàn S≈77,
    đáy khay S≈20); V ≥ 40 (hộp đỏ trong bóng robot V≈95). Tách được khay cam (H 20), platform vàng
    (H 29). `SceneObject.color` gắn màu ↔ vật. Node `vision` (có trong `pick_place.launch.py`):
    `/vision/detections` (vision_msgs/Detection2DArray; `id` = tên vật, `bbox` = khung bao,
    `results[0].pose.pose.position.x/y` = tâm khối **pixel**) + `/vision/debug_image` (chỉ vẽ khi có
    người xem). Đo trên mô phỏng: xử lý **~12 ms/ảnh**; trong `don` + `reset` (607 khung) **99.5%**
    khung thấy đủ 3 vật (0.5% thiếu trụ xanh khi platform che kín). Test: `test_color_detector.py`
    (ảnh tổng hợp biết trước đáp án + 3 ảnh thật trong `test/data/`). ⚠️ Tâm khối là tâm **phần nhìn
    thấy** (mặt trên + mặt bên), **không phải** hình chiếu tâm 3D — Bước 8.3 phải tính tới độ lệch này.
    Sửa kèm: `cartesian_control` chờ `/gripper/held_object` (latched) trước khi nhận lệnh — trước đó
    `tha` gõ ngay sau khi mở node báo nhầm "Khong giu vat nao".
    **Quả cầu lăn — đã sửa (2026-09-18, người làm đồ án chọn "đế vô hình"):** DART không có cản lăn,
    cầu từng lăn khỏi ô B và lăn 25–51 mm sau `reset` (kiểm chứng báo thất bại). `blue_sphere` giờ có
    thêm collision `anti_roll_base` (đĩa r 7 mm dày 2 mm, nhô dưới đáy 0.5 mm; không có visual →
    camera vẫn thấy quả cầu; phải nghiêng > 24° mới đổ). Tâm cầu cao hơn 0.5 mm (z -0.2045). Đo lại:
    trong ô B đứng yên 20 s; `reset` lệch 2.7 mm rồi đứng yên 20 s; `don` + `reset` trọn vẹn.
    Nhận dạng trong lượt này (1117 khung): 98.6% đủ 3 vật, 1.4% thiếu cầu (platform che).
  - [x] 8.3 Hiệu chuẩn ngoại tham số + đổi pixel → tọa độ robot (2026-09-18). Người làm đồ án chọn
    **marker trên bàn** (dùng lại được cho camera thật ở Bước 10).
    - 6 marker ArUco `DICT_4X4_50` (id 0–5), ô đen 50 mm, vị trí trong `scene.CALIB_MARKERS`, model
      `calib_markers` trong world (chỉ visual). Ảnh + khối SDF sinh bằng
      `src/delta_controller/scripts/make_calib_markers.py`; texture ở
      `closed_loop_description/materials/textures/` (đã thêm `materials` vào install của CMake;
      SDF dùng `model://closed_loop_description/materials/textures/aruco_<id>.png`).
    - `camera_model.py` (thuần): `CameraModel` (K, dist, rvec, tvec: X_c = R·X_robot + t),
      `project`, `ray`, `pixel_to_plane(u, v, z)`; `estimate_pose` = **SQPnP + tinh chỉnh LM**;
      `marker_center` = **giao điểm 2 đường chéo** (ảnh đúng của tâm; trung bình 4 góc lệch khi nhìn
      xiên); `camera_model_from_gazebo_pose` (chỉ để đánh giá). ⚠️ **IPPE cho nghiệm sai** trên ảnh
      thật (chiếu lại 434 px) dù pass với điểm tổng hợp → không dùng.
    - `ros2 run delta_controller calibrate_camera`: 20 khung, `CORNER_REFINE_CONTOUR`, lưu
      `~/ros2_closed_loop_ws/calibration/side_camera.yaml` + `.png`. Kết quả: chiếu lại RMS
      **0.14 px**, vị trí camera lệch thật **0.35 mm**, hướng nhìn lệch **0.017°**.
    - `vision` nạp file hiệu chuẩn → `/vision/objects` (vision_msgs/Detection3DArray, `base_link`):
      tia qua tâm khối giao mặt phẳng **z = mặt bàn + nửa chiều cao vật**. Kiểm tra nhanh 3 vật ở vị
      trí ban đầu: lệch thật **0.5 / 0.7 / 1.1 mm**. Giao nhầm với mặt bàn → sai ~12 mm (có test).
    - Kiểm chứng mô hình: chiếu tâm 3D thật lên ảnh rơi cách tâm khối nhận dạng 0.7–1.2 px → với vật
      cao ≈ rộng, tâm phần nhìn thấy ≈ hình chiếu tâm 3D. Độ phân giải tại tâm bàn: 1 mm = 0.87 px
      (theo X, bị nén do nhìn xiên), 1.64 px (theo Y).
    - Phát hiện: tâm marker đo được lệch dự đoán **~0.5 px cùng chiều** — nghi do quy ước tâm pixel
      (Gazebo cx = 320 vs OpenCV 319.5), **chưa kiểm chứng**; PnP tự bù (~0.4 mm).
    - ⚠️ **Nhiễu camera `<noise>` không có tác dụng** (đo: 0.4% pixel thay đổi giữa 2 khung). Hệ quả:
      mọi khung gần như giống hệt nhau; 8.4 muốn đo độ bền với nhiễu phải **tự thêm nhiễu**.
    - Test: `test_camera_model.py` (12 bài, gồm hiệu chuẩn trên ảnh thật `test/data/side_camera_markers.png`).
    - Ảnh cho báo cáo: `docs/figures/vision_objects_mm.png`, `docs/figures/calibration_markers.png`.
  - [x] 8.4 Đo sai số hệ thống (2026-09-18). Kết quả đầy đủ: `docs/results/vision_eval.md` (+ `.csv`),
    hình `docs/figures/vision_error_map.png`, `docs/figures/vision_robustness.png`.
    - Bộ dữ liệu `datasets/vision_eval/` (172 ảnh + `labels.json`, 12 MB) thu bằng
      `python3 src/delta_controller/scripts/record_vision_dataset.py` khi sim chạy: dời vật bằng dịch vụ
      Gazebo `/world/delta_world/set_pose` (gọi `gz service`, ~0.37 s/lần) qua lưới 61 điểm × 3 vật,
      robot lơ lửng trên vật (khe 60/30/15/5 mm), vật trong 3 ô khay. Chụp ảnh **sau** khi dời + 0.8 s.
    - Phân tích offline: `vision_eval.py` (thuần, tái hiện đúng node `vision`; nhiễu Gauss/độ sáng
      tất định theo seed) + `python3 src/delta_controller/scripts/evaluate_vision.py` (~36 s).
    - **Vùng robot gắp được (58 mẫu): TB 1.13 mm, P95 3.7 mm, max 6.2 mm → 100% trong dung sai 12 mm.**
      Mọi điểm trong ảnh: TB 2.0 mm, trung vị 0.77, max 20.6 (đều ngoài tầm với). Lệch hệ thống 0.16 mm.
    - **Che khuất một phần = nguyên nhân sai số lớn** (tâm khối là tâm phần nhìn thấy, lệch theo hướng
      nhìn): vật sau platform (x ≥ 90 mm, y ≈ 0) → gần hơn thật ~19 mm; **vật trong khay: thành khay che
      nửa dưới → xa hơn thật +12…+20 mm (TB 13.4) → VƯỢT dung sai giác hút** → `lay_ra`/`reset` dựa
      camera sẽ hụt nếu chưa sửa. Platform sát đỉnh vật (khe 5 mm): TB 4.6 mm.
    - Bị cắt mép ảnh (góc gần camera, ngoài tầm với): TB 8.2 mm.
    - Nhiễu: vô hại tới σ 10 mức xám; σ 20 → 99.2% nhận dạng; σ 40 → 83%. Độ sáng ổn định 0.5×–1.6×;
      0.3× mất 16.5% (ngưỡng V ≥ 40).
    - Bộ dữ liệu đã đẩy lên GitHub (commit f61fc7f) theo yêu cầu người làm đồ án.
  - [x] 8.5 Ước lượng có xét che khuất (2026-09-18, người làm đồ án chọn cách a + b).
    `vision_estimation.py` (thuần): **hình bóng dự đoán** = bao lồi ảnh các điểm bề mặt vật
    (`SceneObject.shape` box/cylinder/sphere + `half_width`) qua mô hình camera. Kiểm chứng: vật không
    bị che có tỉ lệ nhìn thấy ≈ 0.99.
    - (b) Vật trong khay: nếu ước lượng thô gần khay (thành ngoài + 30 mm) → Newton 2 ẩn khớp **mép trên**
      (`bbox y − 0.5`) + tâm ngang của hình bóng dự đoán, tâm ở `BIN_FLOOR_Z + h`; nhận nếu nằm trong lòng
      khay. **Vật trong khay: TB 13.4 → 1.0 mm, max 19.7 → 1.9 mm**; 9/9 kích hoạt đúng, 0 nhầm.
    - (a) Cờ tin cậy: tỉ lệ nhìn thấy ≥ 0.85 và không chạm mép ảnh (hoặc đã khớp mép trên). Bắt **97%**
      ước lượng > 5 mm, báo nhầm 8%; ước lượng tin cậy: TB 0.90 mm, **max 5.65 mm**. Vật bị platform che
      phía trên vẫn sai ~20 mm nhưng **score = 0** → Bước 9 nên đưa robot tránh tầm nhìn rồi đo lại.
    - `vision` dùng bộ ước lượng này: `/vision/objects` `hypothesis.score` = tỉ lệ nhìn thấy (≤ 1) hoặc
      **0 nếu không tin cậy**; ảnh chú thích ghi `%`, `[mep tren]`, `BI CHE?`. Xử lý ~16 ms/ảnh.
      Chạy thật: hộp đỏ ở ô B lệch 1.0 mm (z −202); sau platform score 0.
    - `vision_eval.evaluate(..., use_top_edge=False)` tái hiện cách cũ để so trước/sau; `flag_quality`.
      `evaluate_vision.py` ghi thêm mục trước/sau + cờ tin cậy. Nhận xét viết tay tách riêng
      `docs/results/vision_eval_nhan_xet.md` (script ghi đè `vision_eval.md` mỗi lần chạy).
    - Test `test_vision_estimation.py` (ảnh thật `side_camera_red_in_bin.png`,
      `side_camera_red_behind_platform.png`). Giới hạn: hình bóng giả định hộp không xoay (yaw 0).

  **Hiệu năng (đo 2026-09-17/18).** Máy: i5-10300H (4 nhân/8 luồng), Intel UHD + **GTX 1650**.
  Driver NVIDIA **595.91 (`nvidia-driver-595-open`) đã cài 2026-09-18** (Secure Boot bật → đã enroll MOK);
  PRIME **on-demand**, phiên đồ họa chuyển sang **X11**. Gazebo chỉ dùng card rời khi đặt:
  `export __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia` (kiểm tra: `nvidia-smi` thấy `gz sim`).

  | Cấu hình (world có camera) | RTF |
  |---|---|
  | Intel, có cửa sổ | ~0.35 |
  | Intel, `gui:=false` | ~0.94 |
  | NVIDIA offload, có cửa sổ, **trước khi sửa** (`gripper_node` ăn 103% CPU) | 0.56 |
  | NVIDIA offload, có cửa sổ, **sau khi sửa** (2026-09-18), `balanced` | **0.77** |
  | như trên, `powerprofilesctl set performance` | 0.76 – 0.99 (dao động giữa các lần, có lúc tụt 0.15–0.3) |

  **Hai lỗi tải CPU đã sửa (2026-09-18):**
  1. **`/clock` + `use_sim_time`:** Gazebo phát `/clock` **mỗi bước mô phỏng** (~2000 Hz). Launch từng
     đặt `use_sim_time: True` cho `gripper_node` → nó nhận `/clock` và ăn **103% CPU** (chạy cô lập
     không có tin nhắn: 0.3%). Đã bỏ → **21%**. ⚠️ Đừng bật `use_sim_time` cho node Python không cần.
     (Chẩn đoán ban đầu đổ cho `/joint_states` là **sai** — đo lại mới thấy `/clock`.)
  2. **`/joint_states` ~2000 Hz:** `JointStatePublisher` (gz-sim8) **không có tùy chọn update_rate**.
     `3dof_delta.launch.py` giờ bridge ra `/joint_states_raw` rồi `topic_tools throttle` xuống
     **100 Hz** thành `/joint_states` (đo 96 Hz). `cartesian_control`: **88% → 14% CPU**.
     Cần gói `ros-jazzy-topic-tools` (đã cài 2026-09-18; khai báo `exec_depend` trong
     `closed_loop_bringup`). ⚠️ `throttle` bản Jazzy **chỉ nhận tham số vị trí**
     (`messages <in> <hz> <out>`); truyền qua tham số ROS → "Throttle type is missing" và tự thoát.
  Kiểm chứng sau khi sửa: `nhat do` → `tha A` đúng, home z = -0.1406.

  `cartesian_control` phát quỹ đạo theo **đồng hồ thật** → RTF < 1 làm quỹ đạo nhanh hơn trong thời
  gian mô phỏng (vẫn tới đích, bám kém hơn); chưa chuyển sang sim time.
  Sau khi dừng launch (TaskStop/kill GUI) có thể **sót tiến trình** bridge/robot_state_publisher →
  kiểm tra `ps` và kill theo PID. `pgrep -f`/`pkill -f` trong Bash tool cũng khớp chính shell.
- [x] **Bước 9** — Gắp–thả dựa trên camera (2026-09-18).
  - Nguồn vị trí vật cho **bộ não** (`cartesian_control` → `task_executor`): tham số `object_source`
    (**mặc định `camera`**) hoặc `ground_truth`; đổi lúc chạy bằng `nguon camera | nguon that`.
    **`gripper_node` vẫn dùng ground truth** — nó mô phỏng PHẦN CỨNG giác hút (hút được hay không là
    chuyện vật lý), không phải phần nhận thức.
  - Chế độ camera (`task_executor`): trước mỗi lần đo robot về **`scene.OBSERVE_XYZ = (0, 0, -0.11)`**
    (ở home platform che vật vùng xa: hộp tại x 120 mm score 0 / sai 17 mm → ở -0.11: 0.99 / 0.3 mm),
    rồi `node.observe_camera(after)` chờ ≥ 2 khung `/vision/objects` nhận SAU khi dừng + 0.3 s; chỉ
    dùng vật score > 0. Đang giữ vật → dùng lần quan sát trước khi nhặt (không quan sát lại).
    "Đã nhấc lên" = giác hút xác nhận (camera không đo được vật lơ lửng); "đã thả đúng chỗ" = camera
    sau khi quan sát lại. Vật không rõ → từ chối kèm lý do; `don`/`reset` bỏ qua và ghi chú.
  - **Một `TaskExecutor` cho cả phiên** (`node.task_executor`) — trước đó tạo mới mỗi lệnh nên `tha`
    gõ riêng sau `nhat` mất lần quan sát trước khi nhặt.
  - `task_executor.py` không import ROS → `test/test_task_executor.py` test chế độ camera bằng robot giả.
  - **Che khuất vật–vật**: hộp đỏ đứng sau trụ xanh (nhìn từ camera) bị che ~15% → lệch 8 mm nhưng tỉ
    lệ nhìn thấy nhỉnh hơn 0.85 → hút lệch tâm 8 mm → thả ô A (cách thành 3 mm) đè thành khay, trượt
    sang ô B (kiểm chứng bằng camera bắt được). Dời platform tới 6 tư thế: kết quả y hệt (không phải
    robot che). Sửa: **`VISIBLE_MIN` 0.85 → 0.90** (dữ liệu 8.4: bỏ sót 1/29 → 0/29, báo nhầm
    10 → 12/143; ước lượng tin cậy max 5.65 → 3.42 mm). Vòng `don` quan sát lại sau mỗi vật nên vật
    bị che sẽ được gắp sau khi vật phía trước đã dọn đi.
  - Thí nghiệm: `python3 src/delta_controller/scripts/run_pick_place_trials.py [n] [seed] [modes]`
    (bố trí ngẫu nhiên trong tầm với, `don` + `reset`, chấm bằng ground truth) →
    `docs/results/pick_place_trials.{md,json}` + nhận xét `docs/results/pick_place_nhan_xet.md`.
    **Kết quả (10 bố trí, seed 2026, ngưỡng 0.90): camera 30/30 vật vào ô, 10/10 `don`; 30/30 về chỗ
    cũ, 10/10 `reset` — bằng hệt chế độ ground truth.** Thời gian/lượt: camera 58 + 55 s, ground truth
    43 + 36 s (~35% chậm hơn do quan sát).
  - ⚠️ Chế độ ground truth, 1/5 lượt ở lần chạy đầu (không lặp lại ở lần 10 lượt): khi lấy hộp đỏ
    khỏi ô C, trụ xanh ở ô A bên cạnh **văng khỏi bàn (2.2 m)**. Chưa rõ nguyên nhân (nghi liên quan platform 5 cm đè cả vật bên cạnh + hiện tượng
    lún/xung lực ở 6.1) — **chưa kiểm chứng, chưa sửa**.
- [ ] **Bước 10** — Camera thật + bản sao số. **Quyết định 2026-09-28 (người làm đồ án):** vật thật là
  **lon nước ngọt** (Coca đỏ / Sprite lục / Pepsi lam — khớp đúng 3 lớp màu đã có), bản sao số
  **theo tỉ lệ k** (xem 10b), và về sau phân biệt thêm **theo chiều cao** (vd. 2 lon cùng màu cao–thấp).
  Chia 3 chặng, chặng sau chỉ bắt đầu khi chặng trước chạy được:
  - **10a — camera thật, vật nhỏ, tỉ lệ 1:1.** Hiệu chuẩn nội tham số (bàn cờ) + ngoại tham số
    (marker), đo sai số thật, đối chiếu 1.13 mm của mô phỏng. Dùng được bản in marker hiện tại.
  - **10b — lon thật + ánh xạ tỉ lệ.** Vị trí thật ÷ k → vị trí ảo; vật ảo giữ kích thước robot gắp
    được. `k ≈ đường kính lon / 30 mm` (lon 330 ml Ø 66 → k ≈ 2.2). **Marker thật phải đặt ở tọa độ
    k × tọa độ ảo** → sinh lại `aruco_markers_A4.pdf` với k, cần bàn ~60×65 cm. Chưa chốt k.
  - **10c — đo chiều cao + nhiều vật cùng màu.** Bỏ được nếu thiếu thời gian, đồ án vẫn trọn vẹn.
  - **Vì sao phải dùng tỉ lệ:** bàn z = −0.22, trần vùng làm việc ≈ −0.10 → chỉ ~120 mm chiều cao.
    Lon 330 ml cao 115 mm: đỉnh ở −0.105 = đúng trần → **gắp tới nơi nhưng không nhấc lên được**;
    khay lòng 70×70 mm cũng không chứa nổi lon Ø 66. Không phóng to robot được: đổi hình học trong
    xacro làm **hỏng mối hàn mạch kín** (2 link phải trùng frame tại home pose) và mọi kiểm chứng
    động học phải làm lại.
  - **Tỉ lệ KHÔNG làm sai số ảo xấu đi:** camera phủ vùng rộng gấp k (mm/pixel xấu đi k lần) nhưng
    sai số lại chia cho k khi quy về không gian ảo → triệt tiêu. Dung sai giác hút 12 mm ảo ≈ 26 mm
    thật. C270 1280×720 (gấp đôi camera mô phỏng 640×480 mỗi chiều) là phần dư bù cho nhiễu + méo.
  - **3 rủi ro đã nhận diện, đều xử lý được bằng code (chưa làm):**
    1. **Logo Pepsi có mảng đỏ** → `color_detector` hiện **gộp mù mọi mảnh cùng màu** (giả định
       1 màu = 1 vật) nên mảng đỏ trên lon Pepsi sẽ bị gộp với lon Coca, tâm khối rơi vào giữa.
       Sửa: chỉ gộp mảnh gần nhau trong phạm vi kích thước vật dự kiến (tính được từ mô hình camera).
    2. **Lóa kim loại**: `vision_estimation` tính `visible = detection.area / silhouette_area`, vệt
       lóa (S tụt, V bão hòa) bị loại khỏi mặt nạ → tỉ lệ nhìn thấy tụt → `VISIBLE_MIN = 0.90` hiểu
       nhầm là bị che → score 0 → **từ chối gắp**. Sửa: lấp lỗ trong vùng trước khi tính diện tích,
       hoặc coi điểm "V cao + S thấp nằm trong hình bóng" là thuộc vật. Lóa gắt cắt đôi lon thì code
       không cứu được → **chiếu sáng khuếch tán**.
    3. **Nhiều vật cùng màu** (10c) phá giả định 1 màu = 1 vật ở **cả chuỗi**: `color_detector`,
       `scene.OBJECTS` (danh sách cố định, mỗi vật 1 màu), `task_planner`/`task_executor` (gọi vật
       **theo tên**), `gripper_node` (tra vị trí thật theo tên model), toàn bộ test tương ứng.
       Chuyển từ "3 vật biết trước" sang "N thực thể phát hiện được" — việc lớn nhất còn lại.
  - **Đo chiều cao bằng camera đơn (10c)** = bài toán **ngược** của `fit_top_edge` (ở 8.5 biết chiều
    cao, giải x, y): đáy vật trên mặt bàn (z biết) → giao tia cho (x, y); mép trên cho chiều cao.
  - Code không sửa được: camera xê dịch sau hiệu chuẩn (né được bằng cách giữ marker trong khung và
    **hiệu chuẩn lại ngoại tham số mỗi khung**), thiếu sáng (σ > 20 là tụt nhận dạng), vật bị che kín.
  - Nên làm trước khi mua lon: **chụp 3 lon bằng điện thoại** → đo mảng đỏ trên lon Pepsi, phần xanh
    thật của lon Sprite, bề rộng vệt lóa.
  - Đã chuẩn bị: `docs/calibration/aruco_markers_A4.pdf` (2026-09-19; trang 1 hướng dẫn + sơ đồ bố
    trí tỉ lệ 1:3 + bảng tọa độ; trang 2–4: 6 marker vector đúng 50 mm — đã kiểm chứng render 200 dpi:
    nhận dạng đủ ID 0–5, cạnh đo 49.91 mm). Sinh bằng `scripts/make_marker_pdf.py` từ
    `scene.CALIB_MARKERS` (6 marker trải ~34×36 cm nên in rời từng marker, đo và dán theo tọa độ).
    `docs/calibration/chessboard_A4.pdf` (2026-09-28; 10×7 ô, cạnh 20 mm, 9×6 góc trong, có thước
    100 mm) sinh bằng `scripts/make_chessboard_pdf.py` — camera thật có méo ống kính nên **phải hiệu
    chuẩn nội tham số trước**; đã kiểm chứng render 200 dpi: `findChessboardCorners` ra 9×6, ô 20.00 mm.
  - Còn chờ người làm đồ án: **mua Logitech C270** (chốt 2026-09-28), giá đỡ/chân máy, in marker +
    bàn cờ ở tỉ lệ 100%, lon nước.

### Bước 10b — cảnh LON + ba khay phân loại (2026-09-29)

**Cảnh hiện tại là ba LON, không còn ba khối vuông.** `scene.OBJECTS` = `coca_can` (đỏ),
`pepsi_can` (lam), `sevenup_can` (lục); world `delta_cans_world.sdf`; `pick_place.launch.py` đã trỏ
sang world này. World cũ `delta_objects_world.sdf` và `scene.LEGACY_OBJECTS` / `LEGACY_BIN_LAYOUT`
**giữ lại** vì mọi ảnh trong `test/data/` và bộ dữ liệu `datasets/vision_eval/` chụp ở cảnh cũ;
`scripts/evaluate_vision.py` và `record_vision_dataset.py` truyền LEGACY_* vào.

- **Tỉ lệ k = 3.0** (`scene.SCALE`): lon thật Ø 57.5 × 147 mm -> lon ảo Ø 19.2 × 49 mm. Giữ nguyên
  tỉ lệ hình dạng nên lon ảo trông đúng như lon thật.
  ⚠️ **Vì sao 3.0 chứ không phải 2.5** (đo 2026-09-29): robot phải nhấc lon QUA ĐẦU lon khác khi
  mang tới khay, tức tool0 ≥ đỉnh lon đứng + nửa bề dày platform + chiều cao lon. Với k = 2.5 (lon
  cao 58.8 mm) cần tool0 ≥ −0.0994 — VƯỢT trần vùng làm việc (−0.10) nên không thể: lon đang mang
  chồng 30.6 mm vào lon đang đứng và ĐÁNH ĐỔ nó (thấy trong thí nghiệm bố trí ngẫu nhiên: lệch
  ngang chỉ 1.6 mm nhưng khe +17.7 mm ⇒ lon đã nằm). Với k = 3.0 chỉ cần tool0 ≥ −0.119. Lon ảo ghép từ 4 khối để tái tạo đúng ba vấn
  đề đo được trên ảnh thật: thân màu + **đĩa bạc** (nắp) + **vành trắng** (nhãn) + **vành đỏ**
  (logo, chỉ Pepsi và 7Up).
- **Ba khay riêng theo chủng loại** (`scene.BINS`), `don` = PHÂN LOẠI chứ không xếp vào ô trống.
  `tha` không còn tham số ô. Bỏ hẳn `BIN_SLOTS`, `resolve_slot`, `first_free_slot`, `occupied_slots`.
- **`safe_z_holding` −0.14 -> −0.112**: lon thò xuống dưới tool0 nhiều hơn khối 30 mm, phải nâng
  đủ cao để lon đang mang đi qua phía trên lon đang đứng.
- **Đầu hút được làm nổi bật**: 2 khối CHỈ HIỂN THỊ màu hồng cánh sen trong `3dof_delta.urdf.xacro`
  (mặt hút nằm âm trong bề dày platform + chóp trên đỉnh). H ≈ 157 nằm ngoài cả ba lớp màu.
- `3dof_delta.gripper.xacro` khai cả 6 vật (3 lon + 3 khối cũ); plugin có `suppress_child_warning`
  nên world thiếu vật nào cũng không sao.

**Bốn lỗi đã tìm ra khi chuyển sang lon (mỗi lỗi đều đáng viết vào khóa luận):**
1. **Tỉ lệ màu danh nghĩa.** Lon chỉ có một phần hình bóng mang màu (nắp bạc + vành trắng + vành
   logo), nên `visible = diện tích màu / hình bóng` luôn < 0.9 -> MỌI lon bị coi là bị che, robot từ
   chối gắp. Sửa: thêm `SceneObject.color_fraction`, chia cho phần *đáng lẽ* thấy được.
   **Đo lại 2026-09-29** bằng `scripts/measure_color_fraction.py` (dời vật qua 9 vị trí trong tầm
   với bằng `gz service set_pose`, robot ở tư thế quan sát): coca **0.67–0.80**, pepsi 0.56–0.71,
   7up 0.55–0.71 — KHÔNG phải hằng số, vì phép đóng hình thái học (kernel 5 px) lấp một phần vành
   nhãn: lon càng XA camera, ảnh càng nhỏ, vành càng bị lấp -> tỉ lệ màu càng cao (hồi quy theo
   diện tích hình bóng: R² ≈ 0.75). Chọn giá trị **nhỏ nhất** đo được (0.66 / 0.55 / 0.55) để lon
   lành lặn không bao giờ bị từ chối; đổi lại cờ tin cậy chỉ bắt được mức che > ~25%.
   ⚠️ Ba hằng số cũ 0.43/0.39/0.39 đo trước khi sửa lỗi gộp mảnh (lỗi 5) và trước khi nắp lon đổi
   sang **trắng nhám**, nên đã lỗi thời: `visible` phồng lên ~1.87, cờ che khuất mất tác dụng.
2. **Tâm khối vùng màu lệch xuống dưới** tâm hình bóng **32 px ≈ 28 mm** (phần trên là nắp bạc).
   Sửa: `fit_bottom_edge` — khớp **mép đáy** (thân lon có màu xuống tận đáy, đáy tì trên bàn) ->
   sai số còn **1.8 mm**. Dùng cho vật trên bàn có `color_fraction < 0.9`.
3. **Mép trên quan sát được là của phần MANG MÀU, không phải đỉnh lon.** Nắp bạc dày 2 mm làm phép
   khớp mép trên (vật trong khay) lệch hệ thống 11–15 mm. Sửa: `SceneObject.color_top_margin` +
   `vision_estimation.color_shape()` dựng hình bóng của riêng phần mang màu.
4. **Robot CHƯA TỚI NƠI khi ra lệnh hút.** Vòng phát điểm chạy theo **đồng hồ thật**, mô phỏng chạy
   RTF < 1 nên `move()` trả về lúc robot còn đang đi -> lệch **46–48 mm** so với vật, trong khi ước
   lượng camera chỉ lệch 1.8 mm. Sửa: `wait_until_arrived()` chờ vị trí ĐO ĐƯỢC (FK từ
   `/joint_states`) vào trong 2 mm. ⚠️ Lỗi này có từ Bước 4, khối vuông thấp nên chưa lộ ra.
   Kèm theo: `observe_camera` lấy **trung vị 5 khung** thay vì tin một khung.

**Bố trí khay — đã thử sai hai lần, ghi lại để không lặp:**
- khay xếp theo trục Y tại x = +0.075: khay giữa nằm **đúng sau thân robot** nhìn từ camera ->
  platform che phần trên lon trong khay, mép trên lệch 41 px, ước lượng sai **18–33 mm**;
- khay xếp theo trục X tại y = −0.08: ba khay gần như nằm **trên cùng hướng nhìn** -> lon trong khay
  **che nhau**, sai 7–18 mm;
- **đang dùng**: KHAY phía **−X (phía camera)** tại x = −0.06, y = −0.075 / 0 / +0.075; LON phía
  **+X** tại (0.06, −0.075), (0.09, 0), (0.06, 0.075). Tia nhìn tới khay chỉ quét x từ −0.40 tới
  −0.06 nên **không bao giờ đi qua robot**; lon ở phía xa vẫn thấy rõ khi robot lên tư thế quan sát.

**Lỗi thứ 5 — gộp mảnh màu làm MẤT phần trên của lon (2026-09-29).** `color_detector` gộp mảnh
theo khoảng cách so với khung bao của mảnh lớn nhất (0.35 lần mỗi phía). Lon bị vành trắng và vành
logo cắt thành nhiều đoạn xếp chồng; đoạn trên nằm ngoài phạm vi đó nên **bị bỏ** -> mặt nạ bắt đầu
thấp hơn đỉnh lon **49 px**, ước lượng sai 22 mm, lon trong khay bị gắn cờ không tin cậy và `don`
dừng giữa chừng. Sửa: gộp theo **CÙNG CỘT** — mảnh phải chồng theo phương ngang với mảnh lớn nhất và
cách nó theo phương dọc ≤ 1.5 lần BỀ RỘNG vật. Đoạn của cùng một lon xếp thẳng cột nên gộp đúng, còn
mảng logo đỏ nằm trên lon KHÁC thì lệch cột nên vẫn bị loại.

**Lỗi thứ 6 — quy tắc gộp mảnh quá lỏng, và ba lớp phòng vệ chống che khuất (2026-09-29).**
Sau khi sửa lỗi 5, quy tắc "cùng cột" vẫn cho gộp nhầm vì chỉ đòi khung bao **chạm** cửa sổ. Tìm ra
bằng `scripts/measure_occlusion.py` (cho lon Pepsi đứng chắn trước lon Coca rồi dịch dần sang ngang):
- **chạm nhau là gộp**: vành logo đỏ của Pepsi chỉ cần chạm mép cửa sổ 1 px -> khung bao nở
  30 -> 73 px, sai 5–6 mm mà cờ vẫn OK (diện tích màu TĂNG nên tỉ lệ nhìn thấy không tụt);
- đổi sang xét **tâm ngang** thì vẫn sót: lon 7Up nằm TRONG KHAY, gần camera hơn và gần thẳng hàng
  với lon Coca phía sau -> vành đỏ của nó rộng 62 px (Coca chỉ 35 px) nên tâm vẫn rơi vào cột ->
  sai **15.3 mm**, cờ vẫn OK. Đây đúng là lượt hỏng duy nhất trong 5 bố trí ngẫu nhiên.
- **đang dùng**: mảnh phải **NẰM GỌN** trong cột (khung bao nằm trọn trong cửa sổ). Cơ sở vật lý:
  hình trụ đứng có bề rộng ảnh gần như không đổi theo chiều cao, nên mảnh RỘNG HƠN HẲN chắc chắn
  thuộc vật khác (ở gần camera hơn). Tính chất thu được: **hễ cờ báo tin cậy thì sai số ≤ 5.8 mm**
  (dung sai giác hút 12 mm); mọi cấu hình che nặng đều bị cờ bắt.
- ⚠️ Khi hai vùng đỏ **dính liền pixel** thành một vùng liên thông (hai lon cách nhau 12–18 mm theo
  phương ngang) thì không quy tắc gộp nào tách được; sai số 5.8 mm, vẫn trong dung sai.

**Ba lớp phòng vệ chống che khuất, mỗi lớp bắt thứ lớp trước bỏ sót:**
1. **Cờ tin cậy** (`vision_estimation`) — không tin thứ nhìn không rõ.
2. **Thứ tự có xét tầm nhìn** (`task_planner.sort_order`) — ba khay nằm phía camera, nên lon đã vào
   khay che mất nửa dưới của lon còn đứng trên bàn ngay sau nó. Ràng buộc: nếu đường nhìn từ camera
   tới lon A quét qua mặt bằng khay của lon B thì **A phải gắp trước B**; sắp xếp tô-pô theo đó.
   Lúc mọi khay còn trống thì lon nào cũng nhìn rõ, nên chỉ cần gắp đúng thứ tự là xong.
   Dùng `scene.SIDE_CAMERA_GT_XYZ[:2]` làm vị trí camera. ⚠️ Với camera THẬT phải lấy vị trí camera
   từ file hiệu chuẩn, chưa nối.
3. **Trí nhớ quan sát** (`task_executor._with_memory`) — có bố trí mà A bị khay của B che VÀ B bị
   khay của A che: **vòng lặp**, không thứ tự nào gỡ được (gặp 1/5 bố trí). Nhưng lon không tự di
   chuyển, nên lấy vị trí của lần gần nhất thấy RÕ. Trí nhớ bị **xóa ngay khi giác hút chạm vào
   vật** -> sau khi thả phải nhìn thấy THẬT mới kiểm chứng được, không có chuyện lấy trí nhớ ra tự
   xác nhận việc mình vừa làm.
- ⚠️ **Phép khớp MÉP TRÊN không dùng được cho lon trên bàn** (đã thử rồi gỡ bỏ): đo trên 6 vị trí,
  mép trên cho **5–12 mm** trong khi mép dưới cho 0.1–0.7 mm. Lý do: mép trên của vùng MÀU không
  phải đặc trưng hình học rõ ràng — nắp trắng, vành nhãn và phép đóng hình thái học làm nó nhòe
  khác nhau tùy khoảng cách tới camera. 12 mm bằng đúng dung sai giác hút nên tin vào đó còn nguy
  hiểm hơn là từ chối. (Với lon TRONG KHAY thì mép trên vẫn tốt: 1.0 mm — xem 8.5.)

**Kiểm chứng cuối (2026-09-29, chế độ camera, chấm bằng odometry):**
- `don`: **3/3 lon vào đúng khay của nó**, lệch tâm khay **0.3 / 0.5 / 1.8 mm**.
- `reset`: **3/3 lon về đúng chỗ cũ**, lệch **4.9 / 7.0 / 7.4 mm** (ngưỡng 10 mm).
- Ước lượng lon đứng trên bàn: lệch **0.1–1.4 mm**. Camera 8.3–8.5 hình/s, xử lý 12.3 ms/ảnh.
- **Thí nghiệm 5 bố trí ngẫu nhiên (seed 2026), sau khi sửa lỗi 6 + ba lớp phòng vệ: 15/15 lon vào
  đúng khay, 5/5 lượt `don`; 15/15 về chỗ cũ (TB 5.5 mm, max 7.1 mm), 5/5 lượt `reset` — KHÔNG lỗi
  nào.** Thời gian 106 + 111 s mỗi lượt. Nhận xét chi tiết: `docs/results/pick_place_nhan_xet.md`
  (mục "Cảnh LON").

⚠️ **Phải dọn HẾT tiến trình cũ trước khi đo.** Lệnh dọn chỉ giết `gz sim` và bridge sẽ để sót node
`vision`/`gripper` của lần chạy trước; chúng chạy MÃ CŨ và cùng phát lên `/vision/objects`, làm kết
quả lẫn lộn và camera tụt còn 1–2 hình/s. Dọn đúng: lọc cả
`delta_controller/lib/delta_controller/(vision|gripper)`, `ros2 launch`, `throttle`,
`robot_state_publisher` rồi kill theo PID (đừng dùng `pkill -f`, nó khớp chính shell đang chạy).

⚠️ Đo hiệu năng phải xem `uptime` trước: `unattended-upgrade` của Ubuntu chạy nền từng kéo camera
mô phỏng từ 10 xuống **1 hình/giây** (load 10.5), làm mọi phép đo vô nghĩa.

**Công cụ mới:** `scripts/drive_repl.py` (gửi chuỗi lệnh vào REPL `cartesian_control`, tự nhận biết
dấu nhắc; dùng để chạy thử tự động) và `scripts/sweep_observe_pose.py` (quét tư thế quan sát, đo sai
số từng vật để chọn `OBSERVE_XYZ`).

### Mặt bàn ảo đổi sang ĐEN NHÁM (2026-09-28)
Bàn thật ở nhà người làm đồ án màu đen **nhám** (đã kiểm tra không bóng) → đổi `work_table` trong
`delta_objects_world.sdf` cho khớp (bản sao số): ambient 0.03, diffuse 0.06, **specular 0.02** (nhám).
Chỉ đổi visual, vật lý không đổi. Kiểm chứng sau khi đổi (sim chạy `gui:=false`):
- `/vision/objects` thấy **đủ 3 vật**, score 0.98–1.00; lệch thật **0.5 / 0.6 / 1.2 mm**
  (trước khi đổi: 0.5 / 0.7 / 1.1 mm) → **đổi màu bàn không ảnh hưởng độ chính xác**.
- Mặt bàn trong ảnh: **H 0, S 0, V 80** → bị loại nhờ ngưỡng **S ≥ 90**, dư an toàn.
- Nhận dạng ArUco: **đủ 6/6 marker** (texture marker có viền trắng nên nền đen không sao).
- Lợi thêm: **bóng đổ của robot gần như vô hình** trên nền đen (trên bàn sáng cũ đây là thử thách
  cho nhận dạng màu, xem 8.2).
- ⚠️ **Điểm ảnh tối có S cao giả tạo** vì `S = (max−min)/max`: đo trên ảnh camera thật, trong vùng
  V < 40 có **85% pixel S > 90**. Vậy với bàn đen, thứ loại được mặt bàn là **ngưỡng V ≥ 40** —
  **không được hạ ngưỡng V**; phần tối của vật thì xử lý bằng cách thêm ánh sáng.
- ⚠️ Bàn đen **bóng** sẽ phản chiếu vật (ảnh phản chiếu **cùng màu**, dính liền) → bị gộp vào vật,
  kéo lệch tâm khối và làm chiều cao đo dôi lên (10c). Bàn thật phải NHÁM, hoặc phủ vải nỉ/giấy nhám.
- ⚠️ Bộ dữ liệu 8.4 (172 ảnh) và các ảnh trong `test/data/` thu trên **bàn màu sáng cũ** — vẫn dùng
  được như bản ghi, nhưng chạy lại trực tiếp trên sim bây giờ sẽ ra ảnh khác.

### Camera thật — đo trên camera của lab (2026-09-28)
Lab có **Thronmax Stream Go Pro** (`0bda:132d`, `/dev/video2`) — **không mượn về được**, người làm đồ án
sẽ mua **Logitech C270** riêng. Buổi ở lab chỉ để khảo sát; mọi hiệu chuẩn phải làm lại trên camera mới
(nội tham số gắn với từng máy cụ thể, kể cả cùng model).
- `scripts/probe_camera.py` — kiểm tra một camera có dùng được không: liệt kê nút chỉnh bắt buộc, chọn
  chế độ MJPG lớn nhất ≥ 15 fps, khóa chế độ thủ công rồi **đọc lại xác nhận**, đo nhiễu cảm biến, in
  KẾT LUẬN. Có `--shots N --out DIR` để thu ảnh mẫu (dùng khi lên lab, mang dữ liệu về nhà làm offline).
  Chạy: `python3 src/delta_controller/scripts/probe_camera.py --device /dev/videoN`.
- Đo được trên Thronmax: 1920×1080 @ 30 fps MJPG; khóa được cả 3 (`focus_automatic_continuous`,
  `auto_exposure=1`, `white_balance_automatic=0`), đọc lại đúng; **nhiễu σ ≈ 5 mức xám** → theo 8.4 là
  vô hại (≤ 10). Đây là **mốc thực tế** đầu tiên cho phần đánh giá độ bền vốn chỉ dùng nhiễu nhân tạo.
- ⚠️ Ở 1080p, **YUYV chỉ 2 fps** → bắt buộc dùng MJPG.
- ⚠️ **Camera lấy nét cố định (C270) KHÔNG có nút focus nào** — đó là trường hợp **tốt nhất** (tiêu cự
  không thể trôi), không phải thiếu tính năng. `probe_camera.py` xử lý đúng: không có nút focus = đạt;
  có mô-tơ nhưng không tắt được tự động = loại.
- ⚠️ OpenCV trên máy là **4.6**: phải dùng `cv2.aruco.DetectorParameters_create()`; gọi kiểu mới
  `cv2.aruco.DetectorParameters()` **segfault** khi vào `detectMarkers` (đã gặp 2026-09-28).
- ⚠️ **Ngưỡng HSV của mô phỏng KHÔNG bê thẳng sang ảnh thật được.** Chạy `color_detector` trên ảnh thật
  ở lab: **tường phòng bị nhận nhầm là vật xanh lá** (15% diện tích ảnh, H ≈ 83, S ≈ 113 > ngưỡng
  S ≥ 90; trong mô phỏng nền có S ≈ 77 nên bị loại). Đèn huỳnh quang + cân bằng trắng 4600 K làm ảnh
  ngả xanh lơ. Bố trí thật camera chĩa xuống bàn nên tường không vào khung, nhưng **phải hiệu chỉnh lại
  ngưỡng trên ảnh thật** — và đây là một ý đáng viết vào khóa luận.
### Camera THẬT Logitech C270 — đã mua và kiểm tra (2026-09-29)
`046d:0825`, `/dev/video2`. Chạy `probe_camera.py`: **ĐẠT toàn bộ**.
- **1280x720 @ 30 fps MJPG** (gấp đôi camera mô phỏng 640x480 mỗi chiều).
- Khóa được `auto_exposure=1` (Manual), `white_balance_automatic=0`, `backlight_compensation=0`,
  `exposure_dynamic_framerate=0` — đọc lại xác nhận đúng.
- **Không có nút focus** = lấy nét cố định -> tiêu cự KHÔNG THỂ trôi sau khi hiệu chuẩn (tốt nhất).
- **Nhiễu σ ≈ 2.2 mức xám** (Thronmax ở lab: 5.0; ngưỡng 8.4: ≤ 10 là vô hại).
- Ảnh thử: sáng TB 141, cháy sáng 6.2%, không có vùng tối.

### Bố trí marker cho BÀN THẬT (2026-09-29)
`docs/calibration/aruco_markers_real_A4.pdf` — sinh bằng `scripts/make_marker_pdf.py` (không tham số;
`--sim` mới ra bố trí ảo cũ). Marker **ô đen 60 mm** (to hơn bản ảo 50 mm vì camera thật đặt xa hơn;
kích thước marker KHÔNG đi vào phép tính — `calibrate_camera_node` chỉ dùng **tâm** marker qua
`marker_center` — nên phóng to là lợi thuần túy cho độ tin cậy nhận dạng).
Đã kiểm chứng render 200 dpi: nhận đủ ID 0–5, cạnh đo **59.88 mm**.

⚠️ **Bố trí thật KHÔNG phải bố trí ảo nhân SCALE**: nhân 3 thì trải 810x870 mm, không vừa bàn rộng
600 mm. `scene.REAL_CALIB_MARKERS` là bố trí riêng (chiếm 560 mm trên bàn 600 mm), cùng
`REAL_OBJECT_AREA_X/Y` (vùng đặt lon thật x 0…280, y ±190 mm -> quy về ảo r = 113 mm, dư so với tầm
với 119 mm).

**Quy ước tỉ lệ khi hiệu chuẩn** (`scene.real_calib_markers_virtual()`): đưa vào PnP **tọa độ ẢO**
(= thật ÷ SCALE) ngay từ khâu hiệu chuẩn, KHÔNG hiệu chuẩn theo mm thật rồi chia kết quả về sau.
Thu nhỏ toàn bộ thế giới k lần chỉ làm **vectơ tịnh tiến của camera chia cho k**; ma trận nội tham
số, hệ số méo và phép chiếu đều không đổi. Nhờ vậy cả khối thị giác sẵn có (`pixel_to_plane`, hình
bóng dự đoán, khay, mặt bàn z = TABLE_Z) chạy nguyên trong hệ ảo, **không phải sửa dòng nào**. Đổi
lại vị trí camera in ra nhỏ hơn thật k lần — chỉ ảnh hưởng lúc báo cáo.

Ba file phải in ở **100% / "Actual size"** (mỗi trang có thước 100 mm để kiểm tra):
`chessboard_A4.pdf` (nội tham số, làm TRƯỚC), `aruco_markers_real_A4.pdf` (ngoại tham số).
`aruco_markers_A4.pdf` là bố trí mô phỏng — **không in**.

### Bố trí THẬT đã dựng xong (2026-10-05)
Camera C270 trên giá kẹp bàn, 6 marker đã dán, hiệu chuẩn cả nội lẫn ngoại tham số xong.

| | giá trị đo được |
|---|---|
| nội tham số | `calibration/c270_intrinsics.yaml`: fx 1417.4, fy 1418.1, RMS **0.222 px** |
| camera | **lùi 557 mm, lệch ngang +1 mm, cao 631 mm trên mặt bàn, chúc 46.1°** |
| ngoại tham số | `calibration/c270.yaml`: 6/6 marker, **sai số 0.93 mm ảo** (2.8 mm trên bàn) |
| ánh sáng | phơi sáng ~400; cháy sáng TRONG mặt nạ màu **0.0%**; S mặt bàn **33** |

⚠️ Góc chúc thật là **46.1°**, không phải 32° như camera mô phỏng — người làm đồ án chọn giữ
nguyên vì bàn không đủ dài để lùi thêm 35 cm. Khối thị giác tự thích nghi (dùng mô hình camera đo
được, không giả định góc); chỉ cần nhớ khi so sánh kết quả thật với mô phỏng là có thêm biến này.
Góc dốc hơn còn LỢI cho che khuất (lon ít che nhau hơn).

**Ba cạm bẫy đo đạc đã mắc phải trong buổi dựng này — đều là lỗi của công cụ, không phải của người
dựng, và đều suýt dẫn tới bóc marker dán lại:**
1. **Quy đổi chiều cao camera quên mặt bàn ở `TABLE_Z`.** `position_real_mm` lấy `z_ảo × SCALE`
   nên báo camera ở **−45 mm**, tức dưới mặt bàn. Test cũ không bắt được vì nó so kết quả với
   chính `truth.position()` — cả hai vế cùng sai một kiểu thì vẫn pass. Test giờ so với hình học
   giá đỡ thật (lùi 900, cao 545).
2. **`estimatePoseSingleMarkers` nói dối trên marker nhỏ nhìn xiên.** Dùng nó để đo khoảng cách
   giữa các marker, nó báo ID 4 và 5 lệch **+65 mm** — hai lần liên tiếp. Cách đo ĐÚNG: khớp tư
   thế bằng một nhóm marker đáng tin rồi **giao tia với mặt bàn** để suy ra vị trí nhóm còn lại;
   làm vậy thì cả 6 marker đều nằm trong **8 mm** so với thiết kế.
3. **Chấm điểm bằng PIXEL là sai đơn vị.** Công cụ báo "LOI RMS 3.25 px quá lớn" trong khi quy ra
   chỉ **0.93 mm ảo**, ngang mô phỏng. Cùng một sai số pixel ứng với số milimét khác hẳn tùy camera
   gần hay xa. Ngưỡng giờ tính theo mm ảo so với dung sai giác hút 12 mm (≤ 3 đạt, > 6 lỗi).

**Tường và sàn nhà lọt vào khung (18% diện tích) KHÔNG gây nhận nhầm** (đo 2026-10-05: 0 pixel
vượt ngưỡng màu) vì gạch sáng nhưng nhạt màu (S = 57 < 90). Nhưng điều đó phụ thuộc ánh sáng hôm
đó — ở lab tường từng bị nhận là vật xanh lá (S ≈ 113). Khi làm node thị giác thật nên **giới hạn
vùng xét theo hình học**: chiếu mặt bàn lên ảnh và bỏ mọi thứ ngoài đó.

### Camera THẬT dùng nhận dạng TÁCH NỀN TRƯỚC, mô phỏng vẫn theo màu (2026-10-05)
`real_vision_node` (entry `real_vision`) đọc thẳng C270, giải lại ngoại tham số MỖI KHUNG từ
marker, giới hạn vùng xét theo hình học, và nhận dạng bằng `object_detector` (tách nền trước rồi
phân loại từng vùng) chứ KHÔNG dùng `color_detector` như node mô phỏng. Phát đúng các topic cũ
(`/vision/objects`, `/vision/detections`, `/vision/debug_image`) nên `task_executor`, cờ tin cậy
và trí nhớ quan sát chạy lại nguyên vẹn. Đo: 10 hình/s, **42 ms/ảnh**, 100/100 khung khóa tư thế.

**Vì sao phải đổi — cả khối ước lượng ngầm giả định MẶT NẠ CHÍNH LÀ HÌNH BÓNG VẬT.** Đúng với lon
ảo (thân một màu đặc), sai hẳn với lon thật (màu nằm thành vành, xen mảng trắng và logo lớn).
Đo cùng một khung hình, lon đứng yên:

| | theo màu | tách nền |
|---|---|---|
| tỉ lệ cao/rộng đỏ / lam / **lục** | 2.28 / 1.88 / **0.93** | 2.45 / 2.26 / **2.65** |
| diện tích ba lon (px) | 14 645 / 5 603 / 2 003 | 28 449 / 22 261 / 22 240 |
| nhiễu vị trí X (mm thật) | 3.4 / 5.9 / **13.8** | 3.0 / 7.1 / **4.4** |
| nhảy lớn nhất giữa 2 khung | 11.6 / 19.3 / **48.1** mm | 8.9 / 22.6 / **16.0** mm |
| tỉ lệ nhìn thấy | phải đoán bằng hằng số | **0.99 ± 0.01** |
| cờ tin cậy | pepsi, 7up bị coi là bị che Ở MỌI KHUNG | **60/60 tin cậy** |

Ba lon cùng kích thước mà nhận theo màu cho diện tích chênh **7 lần** — vì đo thiết kế nhãn chứ
không đo vật. Và tỉ lệ nhìn thấy 0.99 nghĩa là hình bóng đo được khớp hình bóng dự đoán: **cơ chế
phát hiện che khuất lấy lại đúng định nghĩa ban đầu**, thay vì chia cho một hằng số đoán được.

Kèm theo: tiêu chí chọn khớp **mép đáy** đổi từ `color_fraction < 0.9` sang **hình dáng**
(`half_height >= 1.5 × half_width`, hằng số `TALL_RATIO`). Tiêu chí cũ là suy luận vòng vo — lấy
mức độ nhiều màu để đoán hình dáng; đúng tình cờ với lon ảo, vô nghĩa khi mặt nạ là hình bóng thật.

⚠️ **Hai thế giới dùng hai bộ nhận dạng khác nhau, và đó là KẾT LUẬN chứ không phải chắp vá:** nền
mô phỏng có ba khay xám (tách nền thất bại, xem ghi chú `object_detector`), nền thật là bàn đen
trơn. Bản sao số phải giống nhau về **hình học**, còn khâu nhận dạng là bài toán riêng của từng
thế giới. Đây cũng là câu trả lời cho "lon ảo chỉ mang tính tượng trưng": nó không cần giống thật
về bề ngoài, chỉ cần giống về hình học.

⚠️ Còn tồn: lon Coca cho tỉ lệ nhìn thấy **1.19** (hình bóng đo được lớn hơn dự đoán 19%) — nghi
bóng đổ dính chân lon; chưa truy. Nhiễu X của Pepsi nhỉnh lên 5.9 -> 7.1 mm.

### Sai số THẬT đo xong — 4,50 mm ảo (2026-10-07)
18 phép đo (3 lon × 6 vị trí, đặt theo dấu bút chì trên bàn), ghi vào
`docs/results/real_accuracy.json` (`scripts/measure_real_accuracy.py`, in **cả hai** cách khớp).

| | TB | tệ nhất | lệch hệ thống X (mm thật) |
|---|---|---|---|
| khớp **mép trên** (đang dùng) | **4,50 mm ảo** | 6,31 | +9,2 … +10,2 |
| khớp mép đáy | 11,42 | 20,55 | −31,7 … −34,3 |

Mô phỏng đạt 1,13 mm; dung sai giác hút 12 mm → **đạt, kể cả trường hợp tệ nhất**.
Bỏ phần lệch hệ thống ra thì còn **2,35 mm ảo** → phép đo rất ổn định, phần dư là lỗi mô hình.

**Ngưỡng cố định KHÔNG bền với ánh sáng — đây là kết luận chính của buổi này.** Cùng bố trí, cùng
bộ ngưỡng: ban ngày mặt bàn sáng lên **và ám màu** nên lọt vào mặt nạ; thắp một đèn thì bàn quá tối,
`S = (max−min)/max` hóa nhiễu nên **gần như cả mặt bàn** lọt vào. Hai kiểu hỏng **ngược cơ chế**;
quét phơi sáng 80–2600 và gain 0–100 đều không cứu được (C270 bão hòa phơi sáng ở 800).
⇒ `object_detector.foreground_from_reference` so với **ảnh mặt bàn trống**
(`scripts/capture_table_reference.py`, node tự nạp `calibration/table_reference.png`).
Cảnh không đổi: mặt nạ mới báo **0,00%** khung, cách lấy ngưỡng báo 12,06%; nhiễu cảm biến 1 mức
xám so với ngưỡng 30. ⚠️ **Đổi ánh sáng hoặc xê dịch camera là phải chụp lại ảnh nền.**

**Mặt bàn PHẢN CHIẾU lon → mép đáy không dùng được.** Phản chiếu dính liền chân lon (phình đáy
24–57 px) nên mép đáy của mặt nạ không còn là chỗ lon chạm bàn; nó sai **đều −33 mm ở cả ba lon**,
đúng chiều cao ảnh phản chiếu. Trừ nền KHÔNG xóa được (phản chiếu chỉ có khi có lon). Phản chiếu
luôn nằm **dưới** nên **mép trên miễn nhiễm** → `estimate_object(..., reflective_table=True)`,
`real_vision_node` bật cờ này.
⚠️ Trước khi trừ nền, mép đáy *trông* chính xác hơn (9,08 mm) — vì đám lốm đốm phình **đỉnh** bù
trừ một phần cho phản chiếu phình **đáy**. Hai lỗi triệt tiêu nhau tạo ra con số đẹp giả tạo; dọn
sạch một lỗi mới thấy lỗi kia. Bài học: **đừng chọn phương pháp theo con số tổng khi mặt nạ còn bẩn.**
⚠️ Kết luận cũ của 8.5 "mép trên không dùng được cho lon trên bàn" chỉ áp cho mặt nạ **MÀU** (mép
trên là mép vành màu, bị nắp và vành nhãn làm nhòe). Với **hình bóng** thì mép trên là vành miệng
lon — đặc trưng hình học sạch.

**Bộ giải Newton phân kỳ vì điểm xuất phát.** Xuất phát từ tâm khối (bị phản chiếu kéo xuống) thì
mọi lon đặt tại (−70, −160) đều cho **cùng một đáp án sai** (+88,7, −28,7) bất kể là lon nào — dấu
hiệu rơi vào nghiệm lạ, không phải sai số đo. Xuất phát từ ước lượng mép đáy → hết hẳn.

**Ảnh phản chiếu thổi phồng tỉ lệ nhìn thấy → cờ che khuất mất tác dụng một nửa.** Phản chiếu vẫn
nằm trong mặt nạ nên tỉ lệ nhìn thấy xuất phát từ **1,08–1,29** thay vì ~1,00; mà cờ báo khi tỉ lệ
**tụt** dưới `VISIBLE_MIN = 0,90`, nên phải bị che tới ~30% mới báo. Sửa: `ObjectDetection` mang thêm
`row_counts` (số pixel từng hàng — gọn hơn giữ cả mặt nạ), `estimate_object` chỉ đếm phần **phía trên
chân vật dự đoán**. Đo lại: **0,99 / 1,00 / 1,02**, cờ lấy lại đủ dư địa.

**Kiểm chứng đầu-cuối (2026-10-07, ảnh nền đã chụp):** 3/3 lon, `method = top_edge_table`, tỉ lệ
cao/rộng **2,41–2,89** (lon thật 2,56), **nhiễu vị trí 0,5–0,9 mm** (trước khi trừ nền: 3,0–13,8 mm),
50/50 khung tin cậy, 6/6 marker, 12,3 hình/s.

**Phần lệch hệ thống còn lại +9,6 mm là do MARKER, không phải chiều cao lon.** Sai chiều cao sinh
ra lệch **tăng** theo x (tính được: −13 → −19,8), còn đo được thì **giảm** (+12,5 / +12,4 / +3,9 tại
x = −70 / +60 / +190) → bác bỏ. Đo riêng từng marker (khớp tư thế bằng các marker còn lại rồi giao
tia với mặt bàn): **ID 0 lệch 26 mm, ID 4 lệch 29 mm**, ID 1/3/5 lệch 9–15 mm, **ID 2 không nhận ra
được** → ngoại tham số tụt từ 0,93 xuống **1,96 mm ảo**. Muốn tốt hơn thì **đo lại tọa độ thật của
6 marker bằng thước rồi điền vào `scene.REAL_CALIB_MARKERS`** — marker không cần nằm đúng chỗ thiết
kế, chỉ cần **biết đúng** chỗ nó nằm.

### Bước 10b — BẢN SAO SỐ đã chạy (2026-10-07)
`digital_twin_node.py` (entry `digital_twin`) + `launch/digital_twin.launch.py`. Lon THẬT dịch trên
bàn → lon ẢO trong Gazebo dịch theo.

```
lon thật → C270 → real_vision → /vision/objects → digital_twin → Gazebo
                   (hệ ẢO)        (hệ ẢO)          (+ BASE_Z 1.0)
```

**Chỗ nối mỏng đúng như phải thế**: khối thị giác đã phát tọa độ trong hệ ẢO sẵn (tọa độ ảo đi vào
PnP ngay từ khâu hiệu chuẩn — xem `real_calib_markers_virtual`), nên ở tầng này chỉ còn cộng độ cao
đế robot. **Không có phép đổi tỉ lệ nào ở đây.**

- Ghi pose qua **dịch vụ ROS đã cầu nối** `/world/delta_world/set_pose@ros_gz_interfaces/srv/SetEntityPose`.
  Gọi `gz service` bằng tiến trình con mất ~0,37 s/lần → 3 lon hơn 1 giây, không theo kịp camera 10 Hz.
- ⚠️ Launch này chạy `real_vision`, **KHÔNG** chạy `vision` (camera mô phỏng). Hai node cùng phát
  `/vision/objects` là lẫn lộn.
- Ba điều node **từ chối làm**: (1) bỏ qua lon `score = 0`; (2) chỉ ghi pose khi lon thật dịch quá
  `MIN_MOVE` = 0,002 m ảo (6 mm thật, rộng so với nhiễu 0,5–0,9 mm) — dưới mức đó để bộ giải vật lý
  tự lo thay vì ghi đè 10 lần/giây; (3) không đụng lon giác hút đang giữ.
- Dịch vụ phải gọi **bất đồng bộ** — gọi đồng bộ trong callback là khóa chết executor.

**Kiểm chứng (chấm bằng odometry Gazebo):** lon ảo nằm **0,0–0,4 mm ảo** so với chỗ camera báo, z
đúng độ cao lon đứng (−195,5 mm) nên chúng nằm yên trên bàn chứ không rơi. Dịch coca hơn 100 mm →
lon ảo bám theo trong **1 mm thật = 0,3 mm ảo**. Khởi động lại thì lon ảo **tự đồng bộ ngay** từ vị
trí spawn trong SDF về vị trí thật.

**Lỗi tìm ra khi chạy thật: BÀN TAY bị nhận là lon Coca.** Tay người ngả đỏ cam nên rơi vào lớp màu
của Coca; lon ảo nhảy **294 mm rồi quay về**. Cờ tin cậy **không chặn được** vì nó chỉ hỏi tỉ lệ nhìn
thấy có **TỤT** dưới `VISIBLE_MIN` không — **không có chặn trên**, nên vùng to gấp mấy lần vẫn lọt.
Sửa một nửa: thêm **`VISIBLE_MAX = 1.30`** (lon lành lặn đo được 0,99–1,02), chặn này bắt được **hai
lon dính liền pixel** — thứ mà quy tắc gộp mảnh ở lỗi thứ 6 không tách nổi.

⚠️ **Nhưng cờ tin cậy VỀ NGUYÊN TẮC không bắt được vị trí sai** — tính chất cấu trúc, không phải
ngưỡng đặt chưa khéo. `estimate_object` ước lượng vị trí **trước**, rồi mới dựng hình bóng dự đoán
**tại chính vị trí đó**. Vùng ảnh to hơn → phép khớp đẩy vật lại **gần camera hơn** → hình bóng dự
đoán ở đó **cũng to hơn** → tỉ lệ **tự chuẩn hóa** về ~1. Nó chỉ bắt được **che khuất** (méo hình
dáng mà phép khớp không bù được). Thử lại bằng cách giơ tay vào khung: lon ảo vẫn nhảy 284 mm
**trong khi score = 1,00**.

**Ràng buộc không tự chuẩn hóa duy nhất là VẬT LÝ**: lon không dịch 284 mm trong 1/10 giây. Nhảy quá
`JUMP` = 0,02 m ảo (60 mm thật, tức 0,6 m/s ở 10 Hz) phải có **`CONFIRM_FRAMES` = 5 khung liên tiếp**
xác nhận mới ghi vào Gazebo. Nhấc lon đặt sang chỗ khác thì chỗ mới **trụ lại** nên vẫn đi theo (trễ
0,5 s); nhiễu thoáng qua thì không. Cùng tinh thần với **trí nhớ quan sát** ở `task_executor`: đừng
tin một khung.

- [ ] **Bước 11** — Chế độ bám theo tay/marker.
- [ ] **Bước 12** — Đánh giá (độ chính xác, độ trễ, tỉ lệ gắp thành công) + báo cáo.

### Kế hoạch đã làm (yêu cầu của giảng viên)
> "Tạo môi trường với đối tượng cụ thể: object để thực thi câu lệnh, xây dựng phương trình
> và lập trình động học (kinematics). Robot có thể tương tác với môi trường và vật thể
> trong môi trường interaction."

- [x] **Bước 6** — Tương tác robot–vật thể. Đã chọn **cách kết hợp**: va chạm vật lý cho platform
      + gắp/thả "giác hút" bằng `DetachableJoint` + quỹ đạo an toàn nội suy x,y,z.
  - [x] 6.1 Thêm collision cho `tool0` + đo va chạm (xem mục Kiến trúc)
  - [x] 6.2 Nội suy quỹ đạo + FK (2026-09-15). Đo trên Gazebo (ghi `tool0` từ `dynamic_pose/info`):
    `where` khớp pose Gazebo (0.1 mm); home→trên hộp đỏ: `jump` lệch đường thẳng 4.5 mm, đi thẳng
    2.5 mm (khoảng cách ngắn nên chênh không lớn); `safe` lệch đường nâng–ngang–hạ ≤ 4.4 mm, z thấp
    nhất khi đi ngang -0.1611 (safe_z -0.16); vật không bị chạm; Ctrl+C dừng quỹ đạo, node sống tiếp.
  - [x] 6.3 Gắp/thả + khay `drop_bin` (2026-09-15). Chạy: `ros2 launch delta_controller
    pick_place.launch.py` + `ros2 run delta_controller cartesian_control`. Kiểm chứng Gazebo: gắp cả
    3 vật (chạm đỉnh tool0 z = -0.187) thả vào 3 ô khay → cả 3 nằm trong khay, z = -0.202 (nằm
    trên đáy); `grip` khi chưa chạm vật bị từ chối kèm gợi ý; robot về home vẫn chính xác (-0.1410).
    Khay: tâm (0.0375, 0.065), lòng 7×7 cm, thành cao 2 cm; ô thả tool0 A (0.0205, 0.048, -0.179),
    B (0.0545, 0.048, -0.179), C (0.0205, 0.082, -0.179).
- [x] **Bước 7** — Lệnh cấp cao (2026-09-15), trong `cartesian_control` + `pick_place.launch.py`.
      Kiểm chứng Gazebo: lỗi đầu vào (vật/ô sai, place khi không giữ) bị từ chối; **đẩy lệch hộp đỏ
      bằng platform (0.060 → 0.0686) rồi `pick do` gắp đúng vị trí mới**, nhấc 44 mm; `place B` ✓;
      `pickplace xanhla B` (ô đã có vật) bị từ chối, robot không nhặt; `don` dọn 2 vật còn lại vào
      A, C (~28 s) ✓; `sort` lần 2 → "Khong con vat nao tren ban". Cầu lăn nhẹ trong ô (lệch ~5 mm).
  - [x] 7.1 `lay_ra` + `reset` (2026-09-15). Gazebo: `don` 3 vật (~39 s) → `lay_ra do` từ ô B
    về (0.06, 0) lệch 0.6 mm; trụ ở ô A bên cạnh **không xê dịch** dù platform 5 cm đè cả đỉnh
    vật bên cạnh; điểm chồng khay / ngoài tầm với bị từ chối, robot không nhặt; `lay_ra xanhla -0.07 0`
    lệch 0.8 mm; `reset` 2 vật về chỗ cũ (trụ lệch 0.5 mm, **cầu 5.3 mm rồi tiếp tục lăn tới ~7 mm**).
    ⚠️ Quả cầu không có cản lăn: lăn chậm cả trong ô (trôi ~4 mm theo thời gian) lẫn trên bàn.
    → Đã sửa bằng đế chống lăn vô hình ở Bước 8.2.

## Tài liệu cho người làm đồ án

- `docs/Huong_dan_do_an_robot_delta.docx` (2026-09-19) — tài liệu Word giải thích toàn bộ Bước 1–9 để
  người làm đồ án tự hiểu và báo cáo giảng viên (11 chương + phụ lục câu hỏi/đáp, thuật ngữ, bản đồ
  file; 16 bảng, 7 hình). Sinh bằng `docs/tools/build_guide_docx.py` — cần `python-docx`, máy **không
  có pip/LibreOffice/Node**: tải wheel `python_docx` (và `defusedxml` cho công cụ kiểm tra) từ PyPI,
  giải nén vào thư mục tạm, chạy với `PYTHONPATH=<thư mục>`. Đã qua validate.py của skill docx (lỗi
  thứ tự `<w:shd>`, `<w:updateFields>`, thiếu `w:percent` của zoom đã sửa trong script). **Chưa xem
  được giao diện** (không có LibreOffice) — người dùng mở kiểm tra. Mục lục là trường TOC, Word tự
  cập nhật khi mở. Khi số liệu thay đổi phải sửa nội dung trong script rồi sinh lại.
- `docs/Khoa_luan_tot_nghiep.docx` (2026-09-25) — **bản thảo khóa luận** (Bước 1–9) để người làm đồ án
  viết tiếp thành khóa luận nộp. Sinh bằng `docs/tools/build_thesis_docx.py` (cùng cách chạy như trên).
  Định dạng theo *Quy định về trình bày ĐATN* của Trường ĐH Công nghệ ĐHQGHN (bản PDF trên uet.edu.vn):
  A4, TNR 13pt, dãn dòng 1,3; lề trên 2,5 / dưới 3 / trái 3 / phải 2 cm; cách đoạn 6pt, thụt đầu dòng
  1 cm; **số trang đánh lại từ 1 ở phần Mở đầu**, đặt giữa chân trang (2 section, `pgNumType start=1`);
  tiêu đề **bảng đặt TRÊN**, **hình đặt DƯỚI**; TLTK tách theo ngôn ngữ, đánh số `[n]` (tiếng Việt [1]–[2],
  tiếng Anh [3]–[16] → **đổi số trích dẫn phải sửa cả hai chỗ**). Thứ tự phần: bìa → phụ bìa → tóm tắt
  (≈360 từ, 12pt) → abstract → cam đoan → cảm ơn → mục lục → danh mục viết tắt/hình/bảng → Mở đầu →
  7 chương → Kết luận → Phụ lục A–D → TLTK. Số hiệu hình/bảng lấy từ 2 danh sách `FIGURES`/`TABLES` đầu
  script (cuối script assert mọi mục đã dùng đúng 1 lần) → **thêm hình/bảng phải khai báo ở đó**.
  Chỗ cần người làm đồ án điền: `STUDENT`, `MAJOR`, `SUPERVISOR`, `YEAR` ở đầu phần nội dung.
  ~19 800 từ, 7 hình, 27 bảng, ước lượng ~55–60 trang; quy định yêu cầu 50–75 trang → còn phải viết thêm
  (Bước 10–12). **Chưa xem được giao diện** (không có LibreOffice) — người dùng mở Word kiểm tra.
- Hình sơ đồ: `docs/figures/system_architecture.png`, `ros_graph.png`, `delta_leg_diagram.png`.
- `docs/bao_cao_kinematics.md` — phần động học dạng báo cáo.

## Ghi chú về cách làm việc

- Đi **từng bước một**, không dồn hết vào một lần. Hỏi lại khi cần làm rõ,
  đặc biệt với phần động học vì đây là phần quan trọng nhất của đồ án.
- Luôn kiểm chứng công thức/code bằng dữ liệu đã biết trước khi tin dùng.
- Ưu tiên giải thích để hiểu bản chất, không chỉ đưa code chạy được.
