const int ledPins[8] = {30, 31, 32, 33, 34, 35, 36, 37};

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 8; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }
  Serial.println("Arduino ready.");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim(); // Remove newline and whitespace

    if (cmd.startsWith("ON ")) {
      int index = cmd.substring(3).toInt();
      if (index >= 1 && index <= 8) {
        digitalWrite(ledPins[index - 1], HIGH);
        Serial.print("LED ");
        Serial.print(index);
        Serial.println(" ON");
      }
    } else if (cmd.startsWith("OFF ")) {
      int index = cmd.substring(4).toInt();
      if (index >= 1 && index <= 8) {
        digitalWrite(ledPins[index - 1], LOW);
        Serial.print("LED ");
        Serial.print(index);
        Serial.println(" OFF");
      }
    }
  }
}
