const int ledPins[8] = {2, 3, 4, 5, 6, 7, 8, 9};

void setup() {
  Serial.begin(9600); // USB serial connection to Raspberry Pi
  for (int i = 0; i < 8; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }
  Serial.println("[Arduino] Ready");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();

    if (c >= '0' && c <= '7') {
      int index = c - '0';
      digitalWrite(ledPins[index], HIGH);
    }

    if (c >= 'A' && c <= 'H') {
      int index = c - 'A';
      digitalWrite(ledPins[index], LOW);
    }
  }
}
