const int ledPins[8] = {2, 3, 4, 5, 6, 7, 8, 9};

void setup() {
  Serial.begin(9600);   // USB serial (to your PC)
  Serial1.begin(9600);  // TX1/RX1 (to Raspberry Pi)

  for (int i = 0; i < 8; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }

  Serial.println("Arduino is ready. Listening on Serial1 (TX1/RX1).");
}

void loop() {
  if (Serial1.available()) {
    String cmd = Serial1.readStringUntil('\n');
    cmd.trim();

    // Echo command to PC
    Serial.print("[From Pi] ");
    Serial.println(cmd);

    if (cmd.startsWith("ON ")) {
      int index = cmd.substring(3).toInt();
      if (index >= 1 && index <= 8) {
        digitalWrite(ledPins[index - 1], HIGH);
        Serial.print("LED ");
        Serial.print(index);
        Serial.println(" turned ON");
      }
    } else if (cmd.startsWith("OFF ")) {
      int index = cmd.substring(4).toInt();
      if (index >= 1 && index <= 8) {
        digitalWrite(ledPins[index - 1], LOW);
        Serial.print("LED ");
        Serial.print(index);
        Serial.println(" turned OFF");
      }
    }
  }
}
