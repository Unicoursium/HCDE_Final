/* ==== Arduino Mega 2560 Pro ====               (英文代码部分)
   • GAME LEDs : D2–D9   (index 0–7)
   • WAIT LEDs : D10–D13 (index 0–3)
   • PUMPS     : D22–D29 (index 0–7)

   接收来自树莓派的串口指令（9600-8-N-1，换行结尾）：
     LED_ON  n      / LED_OFF  n
     WAIT_ON n      / WAIT_OFF n
     PUMP_ON n      / PUMP_OFF n
   （指令索引为 0-base，如需 1-base 将 toggleBank 内 idx-=1）
*/
const int gameLed[8] = {2,3,4,5,6,7,8,9};
const int waitLed[4] = {10,11,12,13};
const int pumpPin[8] = {22,23,24,25,26,27,28,29};

String inBuf;

void setup() {
  Serial.begin(9600);

  for (int i=0;i<8;i++){ pinMode(gameLed[i],OUTPUT); digitalWrite(gameLed[i],LOW);}
  for (int i=0;i<4;i++){ pinMode(waitLed[i],OUTPUT); digitalWrite(waitLed[i],LOW);}
  for (int i=0;i<8;i++){ pinMode(pumpPin[i],OUTPUT); digitalWrite(pumpPin[i],LOW);}

  inBuf.reserve(40);
  Serial.println("Ready");
}

void loop() { /* 空循环，所有解析工作在 serialEvent() 完成 */ }

void serialEvent() {                        // 立即处理每一行
  while (Serial.available()) {
    char c = Serial.read();
    if (c=='\n' || c=='\r') {               // 行结束
      if (inBuf.length()) {
        handleCmd(inBuf);
        inBuf="";                           // 清空缓冲
      }
    } else {
      inBuf += c;
    }
  }
}

void handleCmd(String s) {
  s.trim();
  if      (s.startsWith("LED_ON "))   toggleBank(gameLed ,8 ,s.substring(7).toInt(), HIGH);
  else if (s.startsWith("LED_OFF "))  toggleBank(gameLed ,8 ,s.substring(8).toInt(), LOW);

  else if (s.startsWith("WAIT_ON "))  toggleBank(waitLed ,4 ,s.substring(8).toInt(), HIGH);
  else if (s.startsWith("WAIT_OFF ")) toggleBank(waitLed ,4 ,s.substring(9).toInt(), LOW);

  else if (s.startsWith("PUMP_ON "))  toggleBank(pumpPin,8 ,s.substring(8).toInt(), HIGH);
  else if (s.startsWith("PUMP_OFF ")) toggleBank(pumpPin,8 ,s.substring(9).toInt(), LOW);
}

void toggleBank(const int* arr,int len,int idx,int state) {
  if (idx>=0 && idx<len) digitalWrite(arr[idx], state);
}
