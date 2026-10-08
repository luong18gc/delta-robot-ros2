/*
 * Điều khiển băng tải cho đồ án robot delta.
 *
 * Phần cứng: Arduino Nano + mạch cầu H L298N + động cơ DC giảm tốc 12 V.
 *   D9 -> ENA (PWM)      D8 -> IN1      D7 -> IN2
 *   GND của L298N PHẢI nối với GND của Arduino.
 *   KHÔNG nối 5V của L298N vào 5V của Arduino (Arduino lấy điện từ USB).
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

const int PIN_PWM = 9;
const int PIN_IN1 = 8;
const int PIN_IN2 = 7;

const unsigned long RUN_TIMEOUT = 3000;   // ms không nhận "R" thì tự dừng
const int DEFAULT_SPEED = 120;            // PWM 0-255; ~50 mm/s với con lăn 42 mm

int speedPwm = DEFAULT_SPEED;
bool running = false;
unsigned long lastRunCommand = 0;

void applyOutput() {
  // IN1 cao / IN2 thấp = một chiều. Băng chạy ngược thì đảo hai dòng này.
  digitalWrite(PIN_IN1, running ? HIGH : LOW);
  digitalWrite(PIN_IN2, LOW);
  analogWrite(PIN_PWM, running ? speedPwm : 0);
}

void setup() {
  pinMode(PIN_PWM, OUTPUT);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
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
