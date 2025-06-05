import time
import board
import busio
import RPi.GPIO as GPIO
from adafruit_pca9685 import PCA9685

# Define button GPIOs and corresponding PCA9685 LED channels
button_pins = [17, 27, 22, 5, 6, 26, 16, 24]
led_channels = [5, 6, 7, 8, 9, 10, 11, 12]

# Set up GPIO
GPIO.setmode(GPIO.BCM)
for pin in button_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set up I2C and PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 1000

# Initialize LED channels
leds = [pca.channels[ch] for ch in led_channels]

# Store button previous state to avoid repeated printing
prev_states = [1] * 8  # All released initially (pull-up = 1)

try:
    while True:
        for i in range(8):
            current_state = GPIO.input(button_pins[i])
            if current_state == 0:
                leds[i].duty_cycle = 0xFFFF
                if prev_states[i] == 1:
                    print(f"Button {i+1} (GPIO {button_pins[i]}) pressed → LED {i+1} ON")
                prev_states[i] = 0
            else:
                leds[i].duty_cycle = 0x0000
                if prev_states[i] == 0:
                    print(f"Button {i+1} (GPIO {button_pins[i]}) released → LED {i+1} OFF")
                prev_states[i] = 1
        time.sleep(0.05)  # 50ms debounce polling

except KeyboardInterrupt:
    for led in leds:
        led.duty_cycle = 0
    GPIO.cleanup()
    print("Program terminated.")
