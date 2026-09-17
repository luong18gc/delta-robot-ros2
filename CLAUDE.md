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

Phần cứng/phần mềm sẵn có trên máy (kiểm tra 2026-09-17): `/dev/video0`, `/dev/video1`; OpenCV 4.6
(Python); `cv_bridge`, `image_transport` của ROS Jazzy. **Chưa có** `usb_cam`/`v4l2_camera`, chưa có
thư viện ArUco/AprilTag cho ROS.

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
- `scene.py` — **nguồn duy nhất phía ROS** cho vật (tên model, nửa chiều cao, tên tắt, `home_xy` =
  vị trí ban đầu, phải khớp `<pose>` trong world), bàn `TABLE_Z`, khay (`BIN_CENTER`, `BIN_FLOOR_Z`,
  `BIN_OUTER_HALF`) và ô thả `BIN_SLOTS` A/B/C. Launch, `gripper_node`, planner đều đọc.
- `task_planner.py` — thuần Python: lệnh cấp cao → chuỗi `Move`/`Grip`/`Release` từ vị trí **thật**
  của vật; `touch_point` = đỉnh vật + 0.003, `release_point` = đáy khay + 5 mm + cao vật + 0.003;
  `locate` (tren ban / o A / trong khay / dang giu), `check_reachable` kiểm IK mọi đích trước khi chạy.
- `task_executor.py` — chạy kế hoạch trên node + **kiểm chứng bằng odometry vật** (pick: vật phải
  nhấc lên ≥ 10 mm; place: vật phải nằm trong ô). `pickplace` kiểm ô trống **trước khi** nhặt;
  `sort` lập lại kế hoạch sau mỗi vật. Lệnh REPL: `objects|vat`, `goto|den`, `pick|nhat`,
  `place|tha [o]`, `pickplace|chuyen <vat> [o]`, `sort|don`, `unload|lay_ra <vat> [x y]`, `reset`.
  `lay_ra`: đặt ra bàn tại `table_release_point` (mặt bàn + 5 mm + cao vật + 0.003 = -0.182),
  `check_table_spot` từ chối điểm chồng khay (tính cả thành + 5 mm) hoặc cách tâm vật khác < 35 mm —
  kiểm tra **trước khi** nhặt; kiểm chứng: vật "tren ban", lệch ≤ 10 mm. `reset` = lay_ra mọi vật
  trong khay về `home_xy`. `_objects()` **chờ đủ vị trí mọi vật** (≤ 3 s): lệnh gõ ngay khi node
  vừa khởi động từng thấy danh sách rỗng → báo nhầm "Khong con vat nao tren ban".
- `test/` — lint + `test_delta_kinematics.py`, `test_trajectory.py`, `test_gripper_logic.py`,
  `test_task_planner.py`.

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
      | `blue_sphere` | cầu r=1.5 cm | (-0.03, -0.052, -0.205) | z = -0.19 |

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
- [ ] **Bước 8** — Camera mô phỏng.
  - [x] 8.1 Camera nhìn xiên (2026-09-17). Model `side_camera` trong `delta_objects_world.sdf`
    (+ plugin `gz-sim-sensors-system`, ogre2). Pose world **ground truth**: xyz (-0.40, 0, 1.03),
    rpy (0, 0.558599, 0) = nhìn xuống 32°, đặt hướng 180° (giữa chân 2 và 3, cánh tay ít che nhất);
    hệ robot (-0.40, 0, 0.03). 640×480, hfov 45° → fx = fy ≈ 772.5, cx 320, cy 240; 10 Hz; nhiễu
    gauss σ 0.007; frame_id `side_camera` (thẻ `<gz_frame_id>`, `gz sdf -k` cảnh báo nhưng chạy đúng).
    Topic ROS: `/side_camera/image` (rgb8), `/side_camera/camera_info` (bridge trong
    `pick_place.launch.py`). Ảnh thấy trọn 3 vật + khay + platform; **có bóng đổ của robot** trên bàn
    (thử thách cho nhận dạng màu). Xem ảnh: `ros2 run rqt_image_view rqt_image_view /side_camera/image`.
  - [ ] 8.2 Nhận dạng vật theo màu (OpenCV, HSV).
  - [ ] 8.3 Hiệu chuẩn + đổi pixel → tọa độ robot (homography mặt bàn); so với pose ground truth ở trên.
  - [ ] 8.4 Đo sai số so với ground truth.

  **Hiệu năng camera (đã đo 2026-09-17):** máy chưa cài driver NVIDIA (đang `nouveau`) → Gazebo render
  bằng GPU Intel UHD. **Cửa sổ Gazebo + camera cùng lúc: RTF ~0.35** (1280×720 hay 640×480 đều vậy).
  Server không GUI + camera: **RTF ~0.9–1.0**, ảnh 9.4 Hz. ⇒ Khi dùng camera chạy
  `ros2 launch delta_controller pick_place.launch.py gui:=false` (tham số `gui` mới thêm vào
  `closed_loop_bringup/3dof_delta.launch.py`, mặc định `true`) và xem cảnh qua rqt_image_view.
  Muốn vừa cửa sổ vừa camera: cần cài driver NVIDIA (GTX 1650) — việc của người dùng (sudo, khởi động lại).
  `cartesian_control` phát quỹ đạo theo **đồng hồ thật** → RTF thấp làm quỹ đạo nhanh hơn trong thời gian
  mô phỏng (vẫn tới đích, bám kém hơn); chưa chuyển sang sim time.

  **Tải CPU:** `JointStatePublisher` (gz-sim8, **không có tùy chọn update_rate**) phát `/joint_states`
  **mỗi bước mô phỏng** (~2000 Hz ở RTF 1). `gripper_node` (MultiThreadedExecutor) ăn ~100% một nhân
  chỉ để nhận topic này — **không** làm giảm RTF (đã đo) nhưng tốn CPU; chưa sửa.
  Sau khi dừng launch (TaskStop/kill GUI) có thể **sót tiến trình** bridge/robot_state_publisher →
  kiểm tra `ps` và kill theo PID. `pgrep -f`/`pkill -f` trong Bash tool cũng khớp chính shell.
- [ ] **Bước 9** — Đưa kết quả thị giác vào hệ điều khiển (chọn nguồn vị trí: ground truth / camera);
  `don` chỉ dựa trên camera.
- [ ] **Bước 10** — Camera thật + bản sao số (đặt/di chuyển vật ảo theo vật thật).
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

## Ghi chú về cách làm việc

- Đi **từng bước một**, không dồn hết vào một lần. Hỏi lại khi cần làm rõ,
  đặc biệt với phần động học vì đây là phần quan trọng nhất của đồ án.
- Luôn kiểm chứng công thức/code bằng dữ liệu đã biết trước khi tin dùng.
- Ưu tiên giải thích để hiểu bản chất, không chỉ đưa code chạy được.
