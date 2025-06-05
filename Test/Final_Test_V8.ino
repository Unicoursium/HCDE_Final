/* ==== Arduino Mega 2560 Pro  ==== 
   – D2-D9   : GAME LEDs  (index 0-7)
   – D10-D13 : WAIT LEDs  (index 0-3)
   – D22-D29 : PUMPS      (index 0-7)

   Receives newline-terminated text commands from Pi:
     LED_ON  n      | LED_OFF  n       (0-7)
     WAIT_ON n      | WAIT_OFF n       (0-3)
     PUMP_ON n      | PUMP_OFF n       (0-7)
*/

const int gameLed[8]  = {2,3,4,5,6,7,8,9};
const int waitLed[4]  = {10,11,12,13};
const int pumpPin[8]  = {22,23,24,25,26,27,28,29};

String inBuf;

void setup() {
  Serial.begin(9600);
  for(int i=0;i<8;i++){ pinMode(gameLed[i],OUTPUT); digitalWrite(gameLed[i],LOW);}
  for(int i=0;i<4;i++){ pinMode(waitLed[i],OUTPUT); digitalWrite(waitLed[i],LOW);}
  for(int i=0;i<8;i++){ pinMode(pumpPin[i],OUTPUT); digitalWrite(pumpPin[i],LOW);}
  inBuf.reserve(40);
}

void loop() {
  serialEvent();          // non-blocking: build lines
  if(!inBuf.isEmpty()){
      handleCmd(inBuf);
      inBuf="";
  }
}

/* ---------- Serial Helpers ------------ */
void serialEvent(){
  while(Serial.available()){
     char c = Serial.read();
     if(c=='\n'){  /* line complete */
        // leave newline out
        return;
     }
     inBuf += c;
  }
}

/* ---------- Command Parser ------------ */
void handleCmd(String s){
  s.trim();
  if(s.startsWith("LED_ON ")){   toggleBank(gameLed,8,s.substring(7).toInt(),HIGH); }
  else if(s.startsWith("LED_OFF ")){ toggleBank(gameLed,8,s.substring(8).toInt(),LOW); }

  else if(s.startsWith("WAIT_ON ")){  toggleBank(waitLed,4,s.substring(8).toInt(),HIGH); }
  else if(s.startsWith("WAIT_OFF ")){ toggleBank(waitLed,4,s.substring(9).toInt(),LOW); }

  else if(s.startsWith("PUMP_ON ")){  toggleBank(pumpPin,8,s.substring(8).toInt(),HIGH); }
  else if(s.startsWith("PUMP_OFF ")){ toggleBank(pumpPin,8,s.substring(9).toInt(),LOW); }
}

void toggleBank(const int* arr, int len, int idx, int state){
  if(idx>=0 && idx<len) digitalWrite(arr[idx], state);
}
