# Hướng dẫn làm băng tải mini — cho người chưa làm bao giờ

Tài liệu này hướng dẫn **tự làm** một băng tải dài 40 cm, rộng 10 cm, chở lon nước 330 ml, điều
khiển chạy/dừng từ máy tính. Phần thiết kế và lý do chọn vật liệu nằm ở
[`../bang_chuyen_thiet_ke.md`](../bang_chuyen_thiet_ke.md); file này chỉ nói **làm thế nào**.

**Thời gian:** 1–2 buổi (chưa kể thời gian chờ mua đồ và chờ keo khô).
**Kỹ năng cần:** cưa gỗ, khoan, vặn vít. Không cần hàn, không cần tiện, không cần máy CNC.
**Chi phí:** khoảng 600 k – 1 triệu đồng.

> **Băng dài 400 mm, KHÔNG phải 500 mm.** Tính tia nhìn từ camera tới các marker hiệu chuẩn: băng
> dài 500 mm làm tia tới marker ID 2 và ID 3 chỉ hở 4 mm so với mặt băng — rung nhẹ là mất marker và
> cả hệ mất khóa tư thế. Với 400 mm thì hở 66–87 mm. Quãng chạy cần chỉ 200 mm nên 400 mm là dư.
>
> **Một điều cần yên tâm trước khi bắt đầu:** băng tải này **không cần chính xác**. Con lăn lệch tâm
> 1 mm chỉ làm tốc độ dao động 2–3%, mắt thường không thấy và hệ thống không quan tâm. Thứ *thật sự*
> quan trọng chỉ có ba: **băng phải căng**, **mặt băng phải phẳng và nhám**, **băng không được trôi
> lệch sang bên**. Ba thứ đó có cách xử lý riêng ở Bước 6 và Bước 7.

---

## 1. Dụng cụ cần có

| Dụng cụ | Dùng để | Thay thế nếu không có |
|---|---|---|
| Cưa tay (cưa gỗ) | Cắt gỗ, cắt ống PVC | Nhờ cửa hàng gỗ cắt sẵn theo kích thước |
| Khoan cầm tay | Khoan lỗ bắt vít | Bắt buộc phải có |
| Mũi khoan gỗ 3 mm, 8 mm | Lỗ vít và lỗ trục | |
| Thước, bút chì, ê-ke | Vạch dấu | |
| Giấy nhám | Làm nhẵn mặt tấm đỡ | |
| Tua vít | | |
| Kìm cắt dây, băng keo điện | Đấu điện | |

**Không cần:** máy khoan bàn, máy tiện, máy hàn, máy in 3D.

---

## 2. Danh sách mua và cách nói với người bán

### 2.1. Cơ khí

| Món | Số lượng | Nói với người bán |
|---|---|---|
| Băng tải PVC trơn 2 mm | khổ 10 cm × 1 m | *"Cho em băng tải PVC trơn dày 2 ly, khổ 10 phân, màu xanh đậm hoặc đen, loại mặt nhẵn không có vân."* |
| Ống nhựa PVC Ø 42 | 30 cm | Ống nước thường, cắt làm 2 đoạn 11 cm |
| Thanh ren M8 (hoặc trục trơn Ø 8) | 60 cm | Cắt làm 2 đoạn 25 cm |
| **Gối đỡ vòng bi KFL08** | **4 cái** | *"Gối đỡ vòng bi KFL08, lỗ 8 ly."* Loại bắt vít vào mặt phẳng |
| Khớp nối trục 6 mm – 8 mm | 1 cái | *"Khớp nối trục mềm 6 ly sang 8 ly."* Nối động cơ với trục |
| Gỗ thông dày 15–18 mm | 1 tấm 60 × 30 cm | Nhờ cắt sẵn theo kích thước ở mục 3 |
| Mica/formica mỏng | 45 × 10 cm | Phủ mặt tấm đỡ cho trơn |
| Keo dán tiếp xúc (keo con chó / X66) | 1 lọ | Nối băng |
| Vít gỗ 4 × 25 mm, đai ốc M8 | mỗi thứ ~20 cái | |

> **Vì sao dùng gối đỡ KFL08 mà không khoan lỗ gắn vòng bi vào gỗ:** gắn vòng bi vào gỗ cần mũi
> khoan 22 mm và lỗ phải thật chính xác, lệch là bi kẹt. Gối đỡ chỉ cần bắt 2 con vít, và nó **tự
> xoay lệch được vài độ** nên tha thứ cho sai số của mình. Đắt thêm ~80 k nhưng đổi lại gần như
> không thể làm sai.

### 2.2. Điện

| Món | Số lượng | Ghi chú |
|---|---|---|
| Động cơ DC giảm tốc **JGB37-520, 12 V, 30–60 vòng/phút** | **1 cái** | Phải có hộp số. Nói rõ *"loại có hộp số, 30 đến 60 vòng một phút"* |
| Mạch cầu H **L298N** | 1 cái | Loại module có tản nhiệt |
| **Arduino Nano** (kèm cáp USB) | 1 cái | Uno cũng được, Nano nhỏ gọn hơn |
| **Adapter 12 V – 3 A**, jack tròn | 1 cái | Có jack cái để đấu dây thì tiện |
| Dây điện, dây jumper cái–cái | 1 bộ | |
| Công tắc hành trình | 1 cái | Chặn cơ khí cuối băng, lắp sau cũng được |

⚠️ **Mua đủ trong một lần.** Thiếu cái khớp nối trục hoặc gối đỡ là phải dừng giữa chừng chờ mua.

---

## 3. Kích thước — cắt gỗ theo bảng này

```
        ┌───────────────────────────────────┐
        │                                   │  ← thành bên (2 tấm)
        │   ●                           ●   │    440 × 80 × 18 mm
        │  lỗ tròn                        lỗ RÃNH  │
        └──────────────────────────────────────────┘
         ↑                                        ↑
      con lăn chủ động                   con lăn bị động
      (gắn động cơ)                      (trượt để căng băng)

        khoảng cách tâm hai trục: 310 mm (chỉnh được tới 330)
```

| Chi tiết | Kích thước | Số lượng |
|---|---|---|
| Thành bên | 440 × 80 × 18 mm | 2 |
| Thanh ngang dưới (nối 2 thành) | 110 × 60 × 18 mm | 2 |
| Tấm đỡ | 320 × 104 × 10 mm (ván mỏng) | 1 |
| Con lăn (ống PVC) | dài 110 mm | 2 |
| Trục (thanh ren M8) | dài 250 mm | 2 |

**Bề rộng lòng giữa hai thành: 110 mm** (băng rộng 100 mm, dư mỗi bên 5 mm).

---

## 4. Bước 1 — Làm con lăn

Đây là bước nhiều người thấy khó nhất, nhưng có mẹo.

1. Cắt ống PVC thành **2 đoạn dài đúng 110 mm**. Cắt vuông góc, không cần đẹp.
2. Cắt 4 miếng gỗ tròn vừa khít lòng ống (nút bịt hai đầu). **Cách tìm tâm:** đặt ống lên miếng gỗ,
   vẽ theo lòng ống thành một đường tròn, cắt ra; rồi kẻ **hai đường kính bất kỳ**, chỗ cắt nhau
   là tâm.
3. Khoan lỗ **8 mm** xuyên tâm mỗi nút gỗ.
4. Đóng nút vào hai đầu ống, bôi keo. Xuyên thanh ren M8 qua, siết đai ốc hai bên để nút không tụt.
5. **Quấn 2–3 vòng băng dính ở CHÍNH GIỮA mỗi con lăn** — tạo chỗ phình đường kính lớn hơn hai đầu
   khoảng 1 mm.

> **Bước 5 là bước quan trọng nhất của cả bài.** Băng phẳng chạy trên con lăn hình trụ **luôn luôn**
> trôi dần sang một bên rồi tuột khỏi khung. Chỗ phình ở giữa kéo băng tự về giữa — đây là nguyên
> lý con lăn "tang trống" của mọi băng tải công nghiệp. Bỏ qua là bạn sẽ mất cả buổi loay hoay
> không hiểu vì sao băng cứ chạy lệch.

**Không cần lo lệch tâm.** Lệch 1 mm chỉ làm tốc độ dao động 2–3%, hoàn toàn vô hại.

---

## 5. Bước 2 — Khung gỗ và gối đỡ

1. Vạch tâm trục trên hai thành bên: cách mép dưới **40 mm**, cách đầu **45 mm**.
2. Đầu **chủ động**: khoan lỗ tròn bắt gối đỡ bình thường.
3. Đầu **bị động**: khoan **lỗ rãnh dài** — khoan 3 lỗ liền nhau rồi dũa thông, dài khoảng 25 mm
   theo chiều dọc băng. Gối đỡ sẽ trượt trong rãnh này để căng băng.
4. Bắt 4 gối đỡ KFL08 vào đúng vị trí. Đầu bị động **chỉ siết hờ** để còn trượt được.
5. Ghép hai thành bên bằng hai thanh ngang dưới. **Dùng ê-ke kiểm tra vuông góc** — khung xiên thì
   băng chắc chắn chạy lệch, và không mẹo nào cứu được.
6. Luồn hai con lăn vào gối đỡ.

**Kiểm tra trước khi đi tiếp:** quay tay cả hai con lăn — phải quay nhẹ, không kẹt, không lắc.

---

## 6. Bước 3 — Tấm đỡ

1. Cắt ván mỏng 320 × 104 mm.
2. Dán mica/formica lên mặt trên cho trơn. Không có thì **đánh giấy nhám thật nhẵn rồi xoa nến**.
3. Đặt tấm đỡ nằm giữa hai con lăn, mặt trên **ngang bằng đỉnh con lăn** (sai 1–2 mm không sao,
   nhưng tấm đỡ **không được cao hơn** đỉnh con lăn).
4. Bắt vít cố định vào hai thanh ngang.

> Không có tấm đỡ thì lon 340 g làm băng võng xuống, lon nghiêng, và vị trí camera đo được sai lệch.

---

## 7. Bước 4 — Nối băng thành vòng kín

**Cách dễ nhất: nhờ cửa hàng nối.** Nhiều nơi bán băng tải có máy ép nhiệt, nối một mối chỉ
10–20 k và chắc hơn tự dán nhiều. Nếu nhờ được, đưa họ số đo ở dưới rồi bỏ qua phần còn lại.

### Tính chiều dài vòng băng

```
chiều dài vòng = 2 × khoảng cách tâm trục + 3,14 × đường kính con lăn
               = 2 × 310 + 3,14 × 42
               = 620 + 132 = 752 mm
```

Cắt băng dài **750 mm** (ngắn hơn một chút để còn căng được bằng cách trượt con lăn bị động ra).

### Nếu tự nối — dùng mối nối ĐỐI ĐẦU, miếng vá nằm DƯỚI

```
   mặt trên (lon chạy)  ─────────────┊─────────────   ← hai mép chạm nhau, PHẲNG
   mặt dưới             ────────┏━━━━━━━━━┓────────   ← miếng vá dán phía dưới
                                 miếng vá 2×10 cm
```

1. Cắt hai đầu băng thật vuông góc.
2. Cắt một miếng vá cùng loại, rộng 10 cm × dài 2 cm.
3. Bôi keo tiếp xúc lên **mặt dưới** hai đầu băng và lên miếng vá. Chờ keo se mặt (5–10 phút theo
   hướng dẫn trên lọ).
4. Đặt hai đầu băng **chạm nhau, không chồng lên nhau**, dán miếng vá phía dưới, ép mạnh.
5. Để khô theo đúng thời gian ghi trên lọ keo, thường 24 giờ.

> **Vì sao miếng vá phải nằm dưới:** mặt trên băng là thứ camera nhìn. Hệ thống nhận dạng bằng cách
> so ảnh với "ảnh mặt băng trống"; một gờ nổi chạy qua chạy lại sẽ bị nhận nhầm là vật. Mối nối
> chồng mép sẽ tạo gờ trên mặt trên — tránh.

---

## 8. Bước 5 — Căng băng và chỉnh thẳng

1. Lồng vòng băng qua hai con lăn.
2. Trượt gối đỡ đầu bị động ra xa cho băng căng, rồi siết vít.
3. **Mức căng đúng:** ấn ngón tay vào giữa mặt băng trên, lún khoảng **5–10 mm**. Căng quá thì bi
   nhanh hỏng và động cơ ì; chùng quá thì băng trượt.
4. Quay tay con lăn chủ động vài vòng, **nhìn băng có trôi lệch sang bên không**.

### Nếu băng trôi lệch

| Hiện tượng | Cách sửa |
|---|---|
| Băng trôi sang trái | Siết gối đỡ bị động **bên trái** ra xa thêm 1–2 mm (căng bên trái hơn) |
| Băng trôi sang phải | Làm ngược lại |
| Trôi mãi không hết | Kiểm tra khung có vuông góc không; kiểm tra chỗ phình băng dính còn đúng giữa không |

**Chỉnh từng chút một, 1 mm mỗi lần, rồi quay thử 10 vòng.** Băng tải cần vài vòng mới ổn định,
đừng chỉnh dồn dập.

---

## 9. Bước 6 — Lắp động cơ

1. Bắt động cơ vào thành bên, trục động cơ **thẳng hàng với trục con lăn chủ động**.
2. Nối hai trục bằng khớp nối 6–8 mm, siết hai vít lục giác.
3. Quay tay — phải quay được, hơi nặng do hộp số là bình thường.

> Trục lệch nhau nhiều thì khớp nối mềm vẫn chạy được nhưng rung và mau hỏng. Căn mắt thường là đủ.

---

## 10. Bước 7 — Đấu điện

```
  adapter 12V ──┬── L298N: chân +12V
                └── L298N: chân GND ──┬── Arduino GND   ← BẮT BUỘC nối chung
                                      │
  động cơ ───── L298N: OUT1, OUT2     │
                                      │
  Arduino D9  ── L298N: ENA (PWM)     │
  Arduino D8  ── L298N: IN1           │
  Arduino D7  ── L298N: IN2           │
  Arduino ─────USB───── máy tính ─────┘
```

⚠️ **Ba điều bắt buộc:**
1. **Nối GND của L298N với GND của Arduino.** Không chung đất thì tín hiệu không có mốc, động cơ
   chạy loạn hoặc không chạy.
2. **KHÔNG nối chân 5 V của L298N vào chân 5 V của Arduino.** Arduino đã có điện từ USB; hai nguồn
   5 V đánh nhau.
3. **KHÔNG lấy điện động cơ từ Arduino.** Động cơ kẹt là cháy mạch Arduino.

Trên module L298N giữ nguyên **jumper ENA** đã tháo (để dùng PWM), và **jumper 5V-EN** cắm vào
(module tự tạo 5 V cho phần logic của nó).

---

## 11. Bước 8 — Nạp chương trình Arduino

Mở Arduino IDE, chọn board Nano, dán chương trình trong
[`conveyor_arduino.ino`](conveyor_arduino.ino), nạp vào.

**Thử bằng Serial Monitor** (tốc độ 115200, chọn "Newline"):

| Gõ | Kết quả mong đợi |
|---|---|
| `V120` | trả `OK`, chưa chạy |
| `R` | trả `OK`, băng **chạy** |
| `S` | trả `OK`, băng **dừng** |
| `R` rồi để yên 3 giây | băng chạy rồi **tự dừng** — đúng, đó là cơ chế an toàn |

> **Vì sao băng tự dừng sau 3 giây:** lệnh `R` không phải công tắc bật-và-quên mà là **lời khẳng
> định phải nhắc lại**. Chương trình ROS sẽ gửi `R` đều đặn mỗi 0,5 giây trong lúc muốn băng chạy.
> Nhờ vậy nếu máy tính treo, dây USB tuột, hay node ROS chết thì **băng tự dừng** thay vì chạy mãi.
> Đây là cách làm chuẩn cho mọi thứ chuyển động được điều khiển từ xa.

Nếu băng chạy **ngược chiều**: đảo hai dây động cơ ở OUT1/OUT2, hoặc đổi `IN1`/`IN2` trong code.

---

## 12. Bước 9 — Thử tải thật

1. Đặt một lon nước lên băng, cho chạy.
2. **Lon phải đi thẳng, không xoay, không trượt lại phía sau.**
3. Gõ `S` khi lon đang chạy — **lon phải dừng gần như ngay**, trôi thêm dưới 5 mm.

| Trục trặc | Nguyên nhân | Sửa |
|---|---|---|
| Lon trôi thêm nhiều sau khi dừng | Băng chùng, trượt trên con lăn | Căng lại băng (Bước 5) |
| Băng đứng im, động cơ kêu | Băng quá căng, hoặc kẹt | Nới bớt; kiểm tra con lăn quay nhẹ không |
| Lon xoay tròn khi chạy | Mặt băng không đều, hoặc tấm đỡ cao hơn con lăn | Hạ tấm đỡ |
| Băng trôi lệch | Xem bảng ở Bước 5 | |
| Động cơ nóng | Băng quá căng | Nới bớt |

**Tốc độ nên đặt:** khoảng **50 mm/s**. Camera chạy 10 hình/giây nên mỗi khung lon đi 5 mm — hệ bám
rất tốt. Chỉnh bằng lệnh `V<n>`, thử từ `V100` rồi tăng dần.

---

## 13. Kiểm tra cuối trước khi nối vào ROS

Đủ 6 mục này mới sang bước phần mềm:

- [ ] Băng chạy 2 phút liên tục **không trôi lệch** quá 3 mm
- [ ] Lệnh `S` làm lon dừng, **trôi thêm dưới 5 mm**
- [ ] Băng tự dừng sau 3 giây nếu không nhận lệnh `R`
- [ ] Mặt băng **không có gờ nổi** ở mối nối (sờ tay không thấy cộm)
- [ ] Đặt lon ở 5 chỗ khác nhau trên băng, **lon không nghiêng** chỗ nào
- [ ] Khung và mặt băng **không bóng** dưới ánh đèn

Xong 6 mục này thì báo tôi — tôi sẽ hướng dẫn đặt băng vào đúng vị trí trên bàn, chụp lại ảnh nền,
và nối vào ROS.

---

## 14. Những lỗi người làm lần đầu hay mắc

| Lỗi | Hậu quả | Phòng tránh |
|---|---|---|
| Quên quấn băng dính giữa con lăn | Băng trôi lệch, không hiểu vì sao | Bước 1 mục 5 |
| Khung ghép không vuông | Băng trôi lệch, chỉnh kiểu gì cũng không hết | Dùng ê-ke ở Bước 2 |
| Nối băng kiểu chồng mép | Gờ nổi mặt trên → camera nhận nhầm | Bước 4, miếng vá nằm dưới |
| Quên tấm đỡ | Băng võng, lon nghiêng, đo sai | Bước 3 |
| Không nối GND chung | Động cơ chạy loạn hoặc không chạy | Bước 7 |
| Lấy điện động cơ từ Arduino | **Cháy Arduino** | Bước 7 |
| Mua động cơ không có hộp số | Nhanh gấp trăm lần mức cần, không dùng được | Mục 2.2 |
| Quên mua khớp nối trục | Lắp xong không nối được động cơ vào trục | Mục 2.1 |
