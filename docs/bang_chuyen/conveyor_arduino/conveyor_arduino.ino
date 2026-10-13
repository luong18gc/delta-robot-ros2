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
 * Giao thức serial 115200. Mỗi lệnh xử lý NGAY khi nhận được ký tự, KHÔNG chờ xuống dòng:
 *   R        chạy  (phải nhắc lại ít nhất mỗi 3 giây — xem bên dưới)
 *   S        dừng
 *   V<0-255> đặt tốc độ   (áp dụng khi gặp ký tự không phải chữ số, hoặc sau 150 ms không gõ tiếp)
 *   ?        in trạng thái
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

int speedPwm = DEFAULT_SPEED;
bool running = false;
unsigned long lastRunCommand = 0;

// Trạng thái gom chữ số cho lệnh V
bool collecting = false;
int pending = 0;
int digits = 0;
unsigned long lastCharAt = 0;

void applyOutput() {
  // Dừng = PWM 0. KHÔNG đụng tới PIN_DIR.
  analogWrite(PIN_PWM, running ? speedPwm : 0);
}

void setup() {
  pinMode(PIN_PWM, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  digitalWrite(PIN_DIR, HIGH);   // đặt một lần, giữ nguyên suốt chương trình
  applyOutput();
  Serial.begin(115200);
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
    case '?':
      Serial.print("chay=");
      Serial.print(running ? 1 : 0);
      Serial.print(" toc do=");
      Serial.println(speedPwm);
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
