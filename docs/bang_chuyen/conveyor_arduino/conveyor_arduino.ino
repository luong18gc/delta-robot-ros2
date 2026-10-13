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
 * Giao thức serial 115200, mỗi lệnh một dòng, trả lời "OK" hoặc "ERR":
 *   R        chạy  (phải nhắc lại ít nhất mỗi 3 giây — xem bên dưới)
 *   S        dừng
 *   V<0-255> đặt tốc độ
 *   ?        in trạng thái
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
  Serial.setTimeout(50);
}

void handle(String line) {
  line.trim();
  if (line.length() == 0) {
    return;
  }
  char cmd = line.charAt(0);
  if (cmd == 'R' || cmd == 'r') {
    running = true;
    lastRunCommand = millis();
    applyOutput();
    Serial.println("OK");
  } else if (cmd == 'S' || cmd == 's') {
    running = false;
    applyOutput();
    Serial.println("OK");
  } else if (cmd == 'V' || cmd == 'v') {
    int value = line.substring(1).toInt();
    if (value < 0 || value > 255) {
      Serial.println("ERR toc do ngoai 0-255");
      return;
    }
    speedPwm = value;
    applyOutput();
    Serial.println("OK");
  } else if (cmd == '?') {
    Serial.print("chay=");
    Serial.print(running ? 1 : 0);
    Serial.print(" toc do=");
    Serial.println(speedPwm);
  } else {
    Serial.println("ERR lenh la");
  }
}

void loop() {
  if (Serial.available()) {
    handle(Serial.readStringUntil('\n'));
  }
  // Hết hạn lời khẳng định "chạy" -> dừng. Đây là lưới an toàn, không phải lỗi.
  if (running && millis() - lastRunCommand > RUN_TIMEOUT) {
    running = false;
    applyOutput();
    Serial.println("TIMEOUT dung bang");
  }
}
