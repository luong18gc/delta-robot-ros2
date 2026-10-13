/*
 * Điều khiển băng tải cho đồ án robot delta.
 *
 * ĐẤU NỐI THỰC TẾ (xác nhận 2026-10-13, băng đã chạy được):
 *   động cơ (+) -> OUTD,  động cơ (−) -> OUTC   (kênh B của L298N)
 *   ENB  -> Arduino D9    (PWM: vừa là tốc độ, vừa là công tắc chạy/dừng)
 *   D8   -> chân đã nối sẵn, chương trình GIỮ MỨC CAO và không bao giờ kéo xuống
 *   GND Arduino + (−) adapter -> GND của L298N;  (+) adapter -> VDD
 *
 * ⚠️ VÌ SAO D8 CHỈ ĐƯỢC ĐẶT MỨC CAO, KHÔNG BAO GIỜ MỨC THẤP:
 * Module L298N "V3" của người dùng không có nhãn IN3/IN4, nên chưa rõ chân nối với D8 là ngõ VÀO
 * điều hướng hay là chân 5V (ngõ RA của bộ ổn áp trên module). Nếu là chân 5V mà chương trình đặt
 * D8 xuống mức thấp thì nguồn 5V bị nối thẳng xuống đất QUA chân Arduino — chập, hỏng chân.
 * Đặt mức cao thì AN TOÀN trong cả hai trường hợp: nếu là ngõ vào điều hướng thì đó là mức cần để
 * quay; nếu là chân 5V thì hai bên cùng điện áp nên không có dòng chạy qua.
 * Vì vậy việc DỪNG băng làm bằng cách đưa PWM trên D9 về 0 — cách này đúng với mọi kiểu đấu nối.
 *
 * ĐIỀU KHIỂN ĐẢO NGƯỢC (đo được 2026-10-13 trên bố trí thật, nên để INVERTED = true):
 * Trên cách đấu hiện tại, D9 KHÔNG nằm trên chân cho phép mà nằm trên một chân ĐIỀU HƯỚNG, còn
 * chân điều hướng kia bị giữ mức cao. Hệ quả là quan hệ bị lật ngược:
 *     PWM 0   -> hai chân lệch mức -> động cơ CHẠY HẾT TỐC ĐỘ
 *     PWM 255 -> hai chân cùng mức cao -> PHANH, dừng
 * Triệu chứng dẫn tới kết luận này: ra lệnh dừng mà băng chạy hết tốc độ; đặt tốc độ thấp thì băng
 * chậm lại thật nhưng chỉ 1–2 giây rồi nhanh trở lại — đúng lúc lưới an toàn hết hạn và đưa PWM
 * về 0. Nếu PWM 0 là "tắt" thì băng phải dừng; nó lại chạy nhanh nhất, nên PWM 0 chính là "chạy".
 * Vì vậy chương trình tự lật ngược giá trị ghi ra, và mọi lệnh bên ngoài giữ nguyên ý nghĩa thông
 * thường: S là dừng, V255 là nhanh nhất.
 *
 * LỆNH DÒ "A": đặt D8 thành ngõ VÀO, tức THẢ NỔI, không phải kéo xuống mức thấp. Thả nổi thì an
 * toàn trong cả hai trường hợp — là ngõ vào điều hướng thì nó chỉ mất tín hiệu, là chân 5V thì
 * không có dòng nào chạy qua. Nhờ vậy dò được chân nào thật sự cho phép mạch chạy mà không phải
 * rút dây (rút rồi cắm lại dễ nhầm chỗ) và không có nguy cơ chập.
 *
 * Giao thức serial 115200. Mỗi lệnh xử lý NGAY khi nhận được ký tự, KHÔNG chờ xuống dòng:
 *   R        chạy  (phải nhắc lại ít nhất mỗi 3 giây — xem bên dưới)
 *   S        dừng
 *   V<0-255> đặt tốc độ   (áp dụng khi gặp ký tự không phải chữ số, hoặc sau 150 ms không gõ tiếp)
 *   ?        in trạng thái
 *   A        THẢ NỔI chân D8 (chỉ để dò đấu nối — xem ghi chú bên dưới)
 *   B        đưa D8 về mức cao như bình thường
 *   I        đảo/bỏ đảo chiều điều khiển (xem ĐIỀU KHIỂN ĐẢO NGƯỢC bên dưới)
 *
 * ⚠️ Vì sao không chờ ký tự xuống dòng: Serial Monitor của Arduino IDE mặc định có thể đang đặt
 * "No Line Ending", khi đó gõ S rồi Enter cũng KHÔNG gửi ký tự xuống dòng nào. Chương trình chờ
 * '\n' sẽ không bao giờ xử lý lệnh, và người dùng thấy băng không phản ứng — rất khó đoán ra.
 * Xử lý từng ký tự thì chạy đúng với mọi thiết lập của Serial Monitor và với cả node ROS.
 *
 * VÌ SAO "R" PHẢI NHẮC LẠI:
 * Lệnh chạy không phải công tắc bật-và-quên mà là một lời khẳng định có hạn dùng. Nếu máy tính
 * treo, cáp USB tuột, hay node ROS chết thì không ai gửi "R" nữa và băng TỰ DỪNG sau RUN_TIMEOUT.
 * Một băng tải chạy mãi vì phần mềm điều khiển đã chết là thứ không được phép tồn tại, và đây là
 * cách rẻ nhất để loại bỏ nó — không cần nút dừng khẩn, không cần cảm biến.
 */

const int PIN_PWM = 9;    // ENB
const int PIN_DIR = 8;    // xem ghi chú ở trên: CHỈ đặt mức cao

const unsigned long RUN_TIMEOUT = 3000;   // ms không nhận "R" thì tự dừng
const int DEFAULT_SPEED = 120;            // PWM 0-255

// true: PWM 255 là dừng, PWM 0 là chạy hết tốc độ (xem ĐIỀU KHIỂN ĐẢO NGƯỢC ở trên).
// Đổi bằng lệnh I khi thử trên bố trí khác, không phải nạp lại chương trình.
bool inverted = true;

int speedPwm = DEFAULT_SPEED;
bool running = false;
unsigned long lastRunCommand = 0;

// Trạng thái gom chữ số cho lệnh V
bool collecting = false;
int pending = 0;
int digits = 0;
unsigned long lastCharAt = 0;

void applyOutput() {
  // KHÔNG đụng tới PIN_DIR. Chỉ ghi ra PIN_PWM; lật ngược nếu mạch đấu kiểu đảo.
  int duty = running ? speedPwm : 0;
  analogWrite(PIN_PWM, inverted ? 255 - duty : duty);
}

void setup() {
  // Phanh TRƯỚC KHI làm bất cứ việc gì khác. Với mạch đấu đảo ngược, chân thả nổi nghĩa là CHẠY,
  // nên thứ tự ở đây không phải chuyện thẩm mỹ: mỗi dòng chậm lại là thêm một quãng băng tự chạy.
  pinMode(PIN_DIR, OUTPUT);
  digitalWrite(PIN_DIR, HIGH);   // đặt một lần, giữ nguyên suốt chương trình
  pinMode(PIN_PWM, OUTPUT);
  applyOutput();                 // running = false -> phanh
  Serial.begin(115200);
  // ⚠️ Vẫn còn ~1,5 giây băng tự chạy ở MỖI LẦN ARDUINO RESET (kể cả khi mở cổng serial), vì lúc
  // đó bộ nạp khởi động đang chạy và các chân còn thả nổi — chương trình chưa có quyền. Không sửa
  // được bằng code trên chân này. Muốn hết hẳn thì phải nối chân cho phép của module tới Arduino
  // và để điện trở kéo xuống giữ nó ở mức thấp khi chân thả nổi.
}

void run(bool on) {
  running = on;
  if (on) {
    lastRunCommand = millis();
  }
  applyOutput();
  Serial.println("OK");
}

void applySpeed() {
  if (digits == 0) {
    Serial.println("ERR thieu so");
  } else if (pending < 0 || pending > 255) {
    Serial.println("ERR toc do ngoai 0-255");
  } else {
    speedPwm = pending;
    applyOutput();
    Serial.println("OK");
  }
  collecting = false;
  digits = 0;
  pending = 0;
}

void handleChar(char c) {
  // Đang gom chữ số cho lệnh V: chữ số thì gom tiếp, thứ khác thì chốt rồi xử lý ký tự đó.
  if (collecting) {
    if (c >= '0' && c <= '9') {
      pending = pending * 10 + (c - '0');
      digits++;
      lastCharAt = millis();
      return;
    }
    applySpeed();
  }
  switch (c) {
    case 'R': case 'r': run(true); break;
    case 'S': case 's': run(false); break;
    case 'V': case 'v':
      collecting = true;
      pending = 0;
      digits = 0;
      lastCharAt = millis();
      break;
    case 'A': case 'a':
      pinMode(PIN_DIR, INPUT);          // thả nổi — KHÔNG BAO GIỜ kéo xuống mức thấp
      Serial.println("OK D8 tha noi");
      break;
    case 'B': case 'b':
      pinMode(PIN_DIR, OUTPUT);
      digitalWrite(PIN_DIR, HIGH);
      Serial.println("OK D8 muc cao");
      break;
    case 'I': case 'i':
      inverted = !inverted;
      applyOutput();
      Serial.print("OK dao nguoc=");
      Serial.println(inverted ? 1 : 0);
      break;
    case '?':
      Serial.print("chay=");
      Serial.print(running ? 1 : 0);
      Serial.print(" toc do=");
      Serial.print(speedPwm);
      Serial.print(" dao nguoc=");
      Serial.println(inverted ? 1 : 0);
      break;
    case '\r': case '\n': case ' ': break;      // bỏ qua, không phải lỗi
    default: Serial.println("ERR lenh la"); break;
  }
}

void loop() {
  while (Serial.available()) {
    handleChar((char) Serial.read());
  }
  // Gõ "V120" rồi thôi: chốt giá trị sau một quãng im lặng, không bắt phải gõ thêm gì.
  if (collecting && millis() - lastCharAt > 150) {
    applySpeed();
  }
  // Hết hạn lời khẳng định "chạy" -> dừng. Đây là lưới an toàn, không phải lỗi.
  if (running && millis() - lastRunCommand > RUN_TIMEOUT) {
    running = false;
    applyOutput();
    Serial.println("TIMEOUT dung bang");
  }
}
