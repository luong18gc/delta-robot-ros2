# Xây dựng phương trình động học cho robot Delta 3 bậc tự do

*Phần báo cáo tiến độ — mô phỏng trên ROS 2 Jazzy + Gazebo Harmonic.*
*Mọi công thức trong phần này đã được cài đặt trong `delta_controller/delta_kinematics.py` và
kiểm chứng bằng test tự động cùng mô phỏng.*

---

## 1. Mô hình hóa robot

### 1.1 Cấu trúc cơ khí

Robot khảo sát là **delta dạng quay (rotary delta, kiểu Clavel)**, không phải delta tịnh tiến.
Cơ cấu gồm:

- **Đế cố định** mang 3 động cơ, đặt cách đều nhau 120° trên đường tròn bán kính $f$.
- **3 cánh tay trên** (upper arm) chiều dài $r_f$, mỗi cánh tay quay quanh một trục nằm ngang,
  tiếp tuyến với đường tròn đế. Đây là **3 khớp chủ động** duy nhất, ký hiệu $\theta_1,\theta_2,\theta_3$.
- **3 thanh chống** (forearm) chiều dài $r_e$, nối với cánh tay trên và với bàn máy bằng **khớp cầu**
  ở cả hai đầu.
- **Bàn máy động** (platform) bán kính $e$, mang đầu công tác.

Nhờ cấu trúc hình bình hành của các thanh chống, bàn máy **luôn song song với đế**. Do đó bàn máy
chỉ có **3 bậc tự do tịnh tiến** và không quay; vị trí của nó được xác định đầy đủ bởi tọa độ tâm
$P = (x_0, y_0, z_0)$.

### 1.2 Hệ trục tọa độ quy ước

Hệ tọa độ gắn với đế (`base_link`):

| Yếu tố | Quy ước |
|---|---|
| Gốc $O$ | Tâm mặt đế cố định |
| Trục $X$ | Hướng ra chân 1 |
| Trục $Z$ | Hướng **lên trên** |
| Trục $Y$ | Theo quy tắc bàn tay phải |

Vì bàn máy luôn nằm **phía dưới** đế nên tọa độ $z_0$ **luôn âm**.

Góc pha của ba chân:

$$\varphi_1 = 0^\circ, \qquad \varphi_2 = 120^\circ, \qquad \varphi_3 = 240^\circ$$

Quy ước dấu góc khớp: $\theta_i = 0$ khi cánh tay trên **nằm ngang, hướng ra ngoài**;
$\theta_i$ **tăng** khi cánh tay **hạ xuống**.

### 1.3 Thông số hình học

Các thông số được trích trực tiếp từ mô hình URDF của robot (`3dof_delta.urdf.xacro`), đơn vị mét:

| Ký hiệu | Ý nghĩa | Giá trị (m) | Nguồn trong URDF |
|---|---|---|---|
| $f$ | Bán kính đế cố định | 0,0417 | `origin` của khớp `Chain1_1` |
| $e$ | Bán kính bàn máy động | 0,0276 | `origin` của khớp `Chain1_cl_A` |
| $r_f$ | Chiều dài cánh tay trên | 0,0758 | `origin` của khớp `Chain1_top_A` |
| $r_e$ | Chiều dài thanh chống | 0,1668 | `origin` của `Chain1_tip_joint` |

Giới hạn khớp chủ động (cả ba chân như nhau):

$$\theta_i \in [-1{,}0297\ \text{rad},\ 1{,}4312\ \text{rad}] \approx [-59{,}0^\circ,\ 82{,}0^\circ]$$

**Vị trí gốc (home):** $\theta_1 = \theta_2 = \theta_3 = 0$ tương ứng với bàn máy tại
$P_{home} = (0,\ 0,\ -0{,}1405)$ m. Đây là **điểm kiểm chứng chuẩn** dùng để xác minh mọi công thức
trước khi sử dụng.

### 1.4 Hai điểm đặc trưng của mỗi chân

Ký hiệu $\mathbf{u}_i = (\cos\varphi_i,\ \sin\varphi_i,\ 0)$ là véc-tơ đơn vị hướng ra chân $i$.

**Khuỷu tay** $E_i$ (đầu ngoài của cánh tay trên, cũng là đầu trên của thanh chống):

$$E_i = (f + r_f\cos\theta_i)\,\mathbf{u}_i - r_f\sin\theta_i\,\hat{z}$$

**Khớp cầu trên bàn máy** $B_i$ (đầu dưới của thanh chống), phụ thuộc vị trí bàn máy $P$:

$$B_i = P + e\,\mathbf{u}_i$$

**Ràng buộc cơ bản** của mỗi chân là thanh chống có chiều dài không đổi:

$$\boxed{\ \lVert B_i - E_i \rVert = r_e \qquad (i = 1, 2, 3)\ }$$

Toàn bộ động học của robot được suy ra từ **ba phương trình ràng buộc này**. Bài toán ngược là biết
$P$ tìm $\theta_i$; bài toán thuận là biết $\theta_i$ tìm $P$.

---

## 2. Bài toán động học ngược (Inverse Kinematics)

**Đầu vào:** tọa độ tâm bàn máy $P = (x_0, y_0, z_0)$.
**Đầu ra:** ba góc khớp chủ động $\theta_1, \theta_2, \theta_3$.

### 2.1 Tách bài toán về từng chân

Do ba chân độc lập nhau trong ràng buộc, có thể giải **riêng cho từng chân**. Để công thức của cả ba
chân giống hệt nhau, ta chuyển điểm $P$ về **hệ tọa độ cục bộ của chân $i$** bằng phép quay quanh
trục $Z$ một góc $-\varphi_i$:

$$
\begin{aligned}
x_i &= x_0\cos\varphi_i + y_0\sin\varphi_i \\
y_i &= -x_0\sin\varphi_i + y_0\cos\varphi_i \\
z_i &= z_0
\end{aligned}
$$

Trong hệ này, chân đang xét nằm trong mặt phẳng $XZ$, khớp chủ động đặt tại $(f, 0, 0)$ và quay
quanh trục $Y$. Khi đó:

$$E_i = (f + r_f\cos\theta_i,\ 0,\ -r_f\sin\theta_i), \qquad
B_i = (x_i + e,\ y_i,\ z_i)$$

### 2.2 Thiết lập phương trình

Đặt

$$a_i = (x_i + e) - f$$

là khoảng cách theo phương $X$ từ khớp chủ động tới khớp cầu trên bàn máy. Thay vào ràng buộc
$\lVert B_i - E_i\rVert^2 = r_e^2$:

$$(a_i - r_f\cos\theta_i)^2 + y_i^2 + (z_i + r_f\sin\theta_i)^2 = r_e^2$$

Khai triển và dùng $\cos^2\theta_i + \sin^2\theta_i = 1$:

$$a_i^2 - 2a_i r_f\cos\theta_i + y_i^2 + z_i^2 + 2z_i r_f\sin\theta_i + r_f^2 = r_e^2$$

Nhóm lại thành phương trình lượng giác tuyến tính theo $\sin\theta_i$ và $\cos\theta_i$:

$$\boxed{\ A_i\cos\theta_i + B_i\sin\theta_i + C_i = 0\ }$$

với

$$
\begin{aligned}
A_i &= -2 r_f a_i \\
B_i &= 2 r_f z_i \\
C_i &= K_i = a_i^2 + y_i^2 + z_i^2 + r_f^2 - r_e^2
\end{aligned}
$$

### 2.3 Giải bằng phép thế Weierstrass

Đặt $t = \tan(\theta_i/2)$, khi đó

$$\cos\theta_i = \frac{1 - t^2}{1 + t^2}, \qquad \sin\theta_i = \frac{2t}{1 + t^2}$$

Thay vào và nhân hai vế với $(1 + t^2)$, thu được **phương trình bậc hai**:

$$(C_i - A_i)\,t^2 + 2B_i\,t + (A_i + C_i) = 0$$

Nghiệm:

$$t = \frac{-B_i \pm \sqrt{A_i^2 + B_i^2 - C_i^2}}{C_i - A_i}, \qquad
\theta_i = 2\arctan t$$

**Ý nghĩa của biệt thức** $\Delta_i = A_i^2 + B_i^2 - C_i^2$:

- $\Delta_i > 0$: hai nghiệm, ứng với hai cấu hình lắp ráp của chân.
- $\Delta_i = 0$: hai nghiệm trùng nhau — cánh tay trên và thanh chống **duỗi thẳng hàng**.
  Đây là **biên không gian làm việc**, đồng thời là **điểm kỳ dị (singularity)** của chân.
- $\Delta_i < 0$: **không có nghiệm** — điểm nằm ngoài tầm với của chân.

*Trường hợp suy biến:* khi $C_i - A_i \approx 0$, phương trình trở thành bậc nhất
$2B_i t + (A_i + C_i) = 0$; chương trình xử lý riêng nhánh này.

### 2.4 Chọn nghiệm đúng — nhánh "khuỷu ra ngoài"

Mỗi chân cho hai nghiệm toán học, nhưng robot thật chỉ lắp theo **một cấu hình**: khuỷu tay nằm
**phía ngoài** đường nối từ khớp chủ động tới khớp cầu trên bàn máy. Chọn sai nghiệm sẽ ra cấu hình
lắp ngược, không tồn tại trên robot.

Tiêu chí chọn nhánh là **dấu đạo hàm của vế trái** phương trình ràng buộc:

$$\frac{d}{d\theta_i}\left(A_i\cos\theta_i + B_i\sin\theta_i\right)
= -A_i\sin\theta_i + B_i\cos\theta_i \le 0$$

Đại lượng này tỉ lệ với tích có hướng giữa véc-tơ (khớp chủ động → khớp cầu bàn máy) và véc-tơ
(khớp chủ động → khuỷu tay), nên **dấu âm tương ứng với khuỷu nằm phía ngoài**. Kiểm chứng tại
vị trí home: $\theta_i = 0$ cho $-A_i\sin 0 + B_i\cos 0 = B_i = 2r_f z_0 < 0$ (vì $z_0 < 0$) ✓.

Sau khi chọn nhánh mới kiểm tra giới hạn khớp; nếu nghiệm khuỷu-ngoài vượt giới hạn thì điểm đó
**không với tới được**.

> **Ghi chú quan trọng (đã kiểm chứng bằng số).** Ban đầu tiêu chí chọn nghiệm dự kiến là
> "lấy nghiệm nằm trong giới hạn khớp". Khi quét lưới toàn không gian, phát hiện có những điểm mà
> xét riêng một chân thì **cả hai nghiệm đều nằm trong giới hạn** (ví dụ chân 1 tại $x = -0{,}09$,
> $z = -0{,}02$ cho $\theta \approx 0{,}641$ và $\theta \approx -1{,}020$), nên quy tắc đó **không
> đủ xác định**. Tiêu chí khuỷu-ngoài có cơ sở hình học rõ ràng nên được dùng thay thế. Trên
> 149 769 điểm mà cả ba chân đều giải được, hai quy tắc cho **kết quả trùng khớp hoàn toàn**.

### 2.5 Thuật toán tóm tắt

```
Cho (x0, y0, z0):
  với mỗi chân i = 1, 2, 3:
    1. Quay điểm về hệ cục bộ:  (xi, yi, zi)
    2. Tính  ai = (xi + e) - f
             Ki = ai² + yi² + zi² + rf² - re²
    3. Tính  Ai = -2·rf·ai,  Bi = 2·rf·zi,  Ci = Ki
    4. Δi = Ai² + Bi² - Ci²;  nếu Δi < 0 -> điểm ngoài tầm với
    5. Hai nghiệm t = (-Bi ± √Δi)/(Ci - Ai),  θ = 2·arctan(t)
    6. Chọn nghiệm có  -Ai·sin θ + Bi·cos θ ≤ 0   (khuỷu ra ngoài)
    7. Kiểm tra giới hạn khớp
  trả về (θ1, θ2, θ3)
```

---

## 3. Bài toán động học thuận (Forward Kinematics)

**Đầu vào:** ba góc khớp $\theta_1, \theta_2, \theta_3$ (đo được từ encoder / `/joint_states`).
**Đầu ra:** tọa độ tâm bàn máy $P$.

### 3.1 Quy về bài toán giao ba mặt cầu

Viết lại ràng buộc của chân $i$ theo $P$:

$$\lVert P + e\,\mathbf{u}_i - E_i \rVert = r_e
\quad\Longleftrightarrow\quad
\lVert P - \underbrace{(E_i - e\,\mathbf{u}_i)}_{\textstyle C_i} \rVert = r_e$$

Vì $\theta_i$ đã biết nên $E_i$ tính được trực tiếp, do đó tâm $C_i$ là **điểm đã biết**:

$$C_i = \big(f + r_f\cos\theta_i - e\big)\,\mathbf{u}_i - r_f\sin\theta_i\,\hat{z}$$

Vậy bài toán thuận trở thành: **tìm giao điểm của ba mặt cầu** có tâm $C_1, C_2, C_3$ và **cùng bán
kính** $r_e$. Đây là phép **trilateration** (định vị ba điểm).

### 3.2 Công thức giải

Dựng hệ trục phụ trực chuẩn gốc tại $C_1$:

$$
\mathbf{\hat{u}} = \frac{C_2 - C_1}{d},\qquad
\mathbf{\hat{v}} = \frac{(C_3 - C_1) - i\,\mathbf{\hat{u}}}{j},\qquad
\mathbf{\hat{w}} = \mathbf{\hat{u}} \times \mathbf{\hat{v}}
$$

trong đó

$$d = \lVert C_2 - C_1 \rVert, \qquad
i = \mathbf{\hat{u}} \cdot (C_3 - C_1), \qquad
j = \lVert (C_3 - C_1) - i\,\mathbf{\hat{u}} \rVert$$

Tọa độ của $P$ trong hệ phụ (ba bán kính **bằng nhau** nên các số hạng $r_e^2$ triệt tiêu, công thức
rút gọn đáng kể):

$$
p_u = \frac{d}{2}, \qquad
p_v = \frac{i^2 + j^2 - 2\,i\,p_u}{2j}, \qquad
p_w = \pm\sqrt{r_e^2 - p_u^2 - p_v^2}
$$

$$P = C_1 + p_u\,\mathbf{\hat{u}} + p_v\,\mathbf{\hat{v}} + p_w\,\mathbf{\hat{w}}$$

**Chọn nghiệm:** hai giá trị $\pm p_w$ đối xứng nhau qua mặt phẳng chứa $C_1, C_2, C_3$; nghiệm vật
lý là nghiệm nằm **phía dưới** (giá trị $z$ nhỏ hơn), vì bàn máy treo dưới đế.

**Các trường hợp không hợp lệ:**

- $r_e^2 - p_u^2 - p_v^2 < 0$: ba mặt cầu không giao nhau — bộ góc khớp không lắp ráp được.
- $d \approx 0$ hoặc $j \approx 0$: ba tâm thẳng hàng — cấu hình suy biến.

### 3.3 Vai trò trong hệ điều khiển

Trong mô phỏng, `/joint_states` **chỉ chứa ba khớp chủ động** (mô phỏng đúng encoder thật, các khớp
bị động không được đo). Vì vậy động học thuận là **cách duy nhất** để hệ điều khiển biết bàn máy
đang ở đâu. Nó được dùng để:

1. Lấy **điểm xuất phát** khi sinh quỹ đạo, đảm bảo đường đi liên tục kể cả khi robot bị vật cản chặn.
2. Kiểm tra điều kiện hút vật của đầu công tác.
3. Hiển thị vị trí hiện tại cho người vận hành (lệnh `where`).

---

## 4. Không gian làm việc

Điều kiện để một điểm với tới được: **cả ba chân** đều có nghiệm khuỷu-ngoài nằm trong giới hạn khớp,
tức $\Delta_i \ge 0$ và $\theta_i \in [\theta_{min}, \theta_{max}]$ với mọi $i$.

Bán kính lớn nhất $r_{max} = \sqrt{x_0^2 + y_0^2}$ mà robot với tới được **theo mọi hướng**, tính
bằng chương trình tại từng cao độ:

| $z_0$ (m) | $r_{max}$ (m) |
|---|---|
| -0,11 | 0,138 |
| -0,14 | 0,128 |
| -0,16 | 0,118 |
| -0,18 | 0,105 |
| -0,20 | 0,085 |
| -0,22 | 0,057 |
| -0,24 | 0 |

Nhận xét: không gian làm việc có dạng **chỏm cụt thu nhỏ dần khi xuống thấp**, hội tụ về một điểm tại
$z_0 \approx -0{,}24$ m (lúc này ba chân duỗi thẳng hết cỡ). Phía trên $z_0 \approx -0{,}10$ m gần như
không với tới được do giới hạn khớp.

---

## 5. Kiểm chứng

Toàn bộ công thức được kiểm chứng theo ba mức độc lập, từ tính tay tới mô phỏng vật lý.

### 5.1 Kiểm chứng bằng tay tại vị trí home

Thay $P_{home} = (0, 0, -0{,}1405)$ vào công thức IK cho chân 1:

$$a_1 = e - f = 0{,}0276 - 0{,}0417 = -0{,}0141$$
$$K_1 = a_1^2 + z_0^2 + r_f^2 - r_e^2 = 0{,}000199 + 0{,}019740 + 0{,}005746 - 0{,}027822 = -0{,}002137$$
$$A_1 = -2 r_f a_1 = +0{,}002138 \quad\Rightarrow\quad A_1 + C_1 = A_1 + K_1 \approx 0$$

Vì $A_1 + C_1 = 0$ nên $t = 0$, suy ra $\theta_1 = 0$ — **đúng bằng giá trị home trong URDF** ✓
(tương tự cho chân 2 và 3 nhờ tính đối xứng).

> **Cạm bẫy đã gặp:** phiên bản đầu viết nhầm $a_i = (x_i - e) - f$. Kết quả cho home là
> $z_0 = -0{,}0823$ thay vì $-0{,}1405$. Sai dấu này được phát hiện **ngay lập tức** nhờ kiểm chứng
> bằng vị trí home. Bài học: luôn kiểm chứng công thức bằng một cấu hình đã biết trước khi tin dùng.

### 5.2 Kiểm chứng bằng số (test tự động)

| Phép kiểm tra | Phạm vi | Kết quả |
|---|---|---|
| Ràng buộc chiều dài thanh chống: $\lVert B_i - E_i\rVert = r_e$ sau khi giải IK | nhiều điểm mẫu | sai số < $10^{-9}$ m |
| Đối xứng: điểm trên trục $Z$ cho ba góc bằng nhau | 4 cao độ | trùng tới $10^{-12}$ |
| Đối xứng quay: quay điểm 120° thì ba góc hoán vị vòng | điểm bất kỳ | đúng |
| **Vòng lặp IK → FK** trả về đúng điểm ban đầu | **5 424 điểm** | sai số lớn nhất $5\times10^{-13}$ m |
| FK tại home | $\theta = (0,0,0)$ | $(0,\ 0,\ -0{,}14050)$ ✓ |
| Điểm ngoài tầm với bị từ chối | các điểm quá xa / phía trên đế | báo lỗi đúng |

Vòng lặp IK → FK là phép kiểm tra mạnh nhất: hai công thức được xây dựng **độc lập nhau** (một dùng
phép thế Weierstrass, một dùng giao ba mặt cầu), nên việc chúng khử lẫn nhau chính xác tới cỡ sai số
làm tròn của máy tính cho thấy cả hai đều đúng.

### 5.3 Kiểm chứng trên mô phỏng Gazebo

Đây là kiểm chứng quan trọng nhất: so sánh vị trí **tính toán** với vị trí **thực tế** của bàn máy
trong mô phỏng vật lý (đọc trực tiếp pose của link `tool0`).

Ra lệnh cho robot tới 9 điểm rồi đo lại:

| Lệnh $(x, y, z)$ m | Gazebo đo được (m) | Sai lệch |
|---|---|---|
| (0; 0; -0,1405) | (0,0002; -0,0002; -0,1406) | < 0,3 mm |
| (0; 0; -0,12) | (0,0001; -0,0001; -0,1199) | < 0,2 mm |
| (0; 0; -0,18) | (0,0002; -0,0002; -0,1802) | < 0,3 mm |
| (0,03; 0; -0,15) | (0,0297; -0,0001; -0,1502) | < 0,4 mm |
| (-0,03; 0; -0,15) | (-0,0293; -0,0001; -0,1502) | < 0,8 mm |
| (0; 0,03; -0,15) | (0,0001; 0,0294; -0,1502) | < 0,7 mm |
| (0,02; -0,02; -0,16) | (0,0198; -0,0197; -0,1602) | < 0,4 mm |
| (-0,04; -0,03; -0,19) | (-0,0387; -0,0295; -0,1905) | < 1,4 mm |

**Kết luận:** sai lệch dưới 1 mm trong vùng làm việc chính, tăng nhẹ tới ~1,5 mm khi tay duỗi xa.
Phần sai lệch còn lại **không đến từ công thức** mà từ mô phỏng vật lý: bàn máy võng nhẹ dưới tác
dụng trọng lực và bộ điều khiển PID của khớp có sai số xác lập (cỡ 0,003–0,01 rad). Điều này phù hợp
với hành vi của robot thật.

Động học thuận cũng được kiểm chứng tương tự: giá trị FK tính từ `/joint_states` **khớp với pose
thật** của bàn máy trong Gazebo tới 0,1 mm.

---

## 6. Cài đặt phần mềm

Công thức được cài đặt trong package tự viết `delta_controller`, dạng **Python thuần không phụ thuộc
ROS**, nhờ đó có thể kiểm thử tự động bằng `pytest` mà không cần khởi động Gazebo.

| Thành phần | Chức năng |
|---|---|
| `delta_kinematics.py` | Toàn bộ động học: IK và FK |
| `DeltaGeometry` | Thông số $f, e, r_f, r_e$ và giới hạn khớp |
| `solve_leg(x, y, z, phi)` | Giải một chân (mục 2.2 – 2.4) |
| `inverse_kinematics(x, y, z)` | Trả về $(\theta_1, \theta_2, \theta_3)$ |
| `forward_kinematics(θ1, θ2, θ3)` | Giao ba mặt cầu (mục 3.2) |
| `elbow_position`, `platform_joint_position` | Tính $E_i$, $B_i$ phục vụ kiểm chứng |
| `UnreachableError` | Ngoại lệ khi điểm ngoài không gian làm việc |

Chạy kiểm thử:

```bash
colcon test --packages-select delta_controller && colcon test-result --verbose
```

---

## 7. Tài liệu tham khảo

1. Clavel, R. *Device for the Movement and Positioning of an Element in Space.*
   US Patent 4,976,582, 1990. — Bằng sáng chế gốc của robot delta.
2. Williams II, R. L. *The Delta Parallel Robot: Kinematics Solutions.*
   Ohio University, 2016. https://people.ohio.edu/williams/html/PDF/DeltaKin.pdf
   — Tài liệu chuẩn về công thức động học thuận/ngược của delta dạng quay.
