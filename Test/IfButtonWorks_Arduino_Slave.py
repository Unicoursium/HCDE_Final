import serial
import time
import RPi.GPIO as GPIO

# Define button GPIOs
button_pins = [17, 27, 22, 5, 6, 26, 16, 24]

# Setup GPIO
GPIO.setmode(GPIO.BCM)
for pin in button_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Open serial connection to Arduino
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)  # Wait for Arduino to reset

# Track previous states
prev_states = [1] * 8

print("Raspberry Pi: Monitoring buttons and sending commands to Arduino...")

try:
    while True:
        for i in range(8):
            state = GPIO.input(button_pins[i])
            if state == 0 and prev_states[i] == 1:
                ser.write(f"ON {i+1}\n".encode())
                print(f"Button {i+1} pressed → Send: ON {i+1}")
                prev_states[i] = 0
            elif state == 1 and prev_states[i] == 0:
                ser.write(f"OFF {i+1}\n".encode())
                print(f"Button {i+1} released → Send: OFF {i+1}")
                prev_states[i] = 1
        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()
    ser.close()
    print("Program terminated.")
