// === Arduino Serial Command Receiver for Pump + LED Control ===

const int ledPins[8]  = {2, 3, 4, 5, 6, 7, 8, 9};
const int pumpPins[8] = {12, 13, 14, 15, 16, 17, 18, 19};

String inputString = "";
bool stringComplete = false;

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < 8; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);

    pinMode(pumpPins[i], OUTPUT);
    digitalWrite(pumpPins[i], LOW);
  }

  inputString.reserve(50); // avoid memory fragmentation
}

void loop() {
  if (stringComplete) {
    handleCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
      break;
    } else {
      inputString += inChar;
    }
  }
}

void handleCommand(String cmd) {
  cmd.trim();

  if (cmd.startsWith("LED_ON ")) {
    int index = cmd.substring(7).toInt();
    if (index >= 0 && index < 8) digitalWrite(ledPins[index], HIGH);
  } else if (cmd.startsWith("LED_OFF ")) {
    int index = cmd.substring(8).toInt();
    if (index >= 0 && index < 8) digitalWrite(ledPins[index], LOW);
  } else if (cmd.startsWith("PUMP_ON ")) {
    int index = cmd.substring(8).toInt();
    if (index >= 0 && index < 8) digitalWrite(pumpPins[index], HIGH);
  } else if (cmd.startsWith("PUMP_OFF ")) {
    int index = cmd.substring(9).toInt();
    if (index >= 0 && index < 8) digitalWrite(pumpPins[index], LOW);
  } else {
    Serial.println("Unknown Command: " + cmd);
  }
}
