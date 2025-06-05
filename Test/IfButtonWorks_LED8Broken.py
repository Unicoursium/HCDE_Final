import time
import board
import busio
import RPi.GPIO as GPIO
from adafruit_pca9685 import PCA9685

# Button GPIOs
button_pins = [17, 27, 22, 5, 6, 26, 16, 24]

# LED channels on PCA9685 (LED1 to LED7)
pca_led_channels = [5, 6, 7, 8, 9, 10, 11]

# LED8 is now directly connected to Raspberry Pi GPIO18
gpio_led_pin = 18

# Setup GPIO
GPIO.setmode(GPIO.BCM)
for pin in button_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(gpio_led_pin, GPIO.OUT)
GPIO.output(gpio_led_pin, GPIO.LOW)

# Setup PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 1000

# Turn off all PCA LEDs at startup
for ch in pca_led_channels:
    pca.channels[ch].duty_cycle = 0x0000

# Track previous button states
prev_states = [1] * 8

print("Monitoring 8 buttons (LED8 directly on GPIO)...")

try:
    while True:
        for i in range(8):
            pin = button_pins[i]
            state = GPIO.input(pin)

            if i < 7:
                # LED1 ~ LED7 (PCA9685 control)
                channel_index = pca_led_channels[i]
                if state == 0 and prev_states[i] == 1:
                    pca.channels[channel_index].duty_cycle = 0xFFFF
                    print(f"[ON ] Button {i+1} (GPIO{pin}) → LED {i+1} ON → PCA Channel {channel_index}")
                    prev_states[i] = 0
                elif state == 1 and prev_states[i] == 0:
                    pca.channels[channel_index].duty_cycle = 0x0000
                    print(f"[OFF] Button {i+1} (GPIO{pin}) → LED {i+1} OFF → PCA Channel {channel_index}")
                    prev_states[i] = 1
            else:
                # LED8 (GPIO output control)
                if state == 0 and prev_states[i] == 1:
                    GPIO.output(gpio_led_pin, GPIO.HIGH)
                    print(f"[ON ] Button 8 (GPIO{pin}) → LED 8 ON → GPIO{gpio_led_pin}")
                    prev_states[i] = 0
                elif state == 1 and prev_states[i] == 0:
                    GPIO.output(gpio_led_pin, GPIO.LOW)
                    print(f"[OFF] Button 8 (GPIO{pin}) → LED 8 OFF → GPIO{gpio_led_pin}")
                    prev_states[i] = 1

        time.sleep(0.05)

except KeyboardInterrupt:
    for ch in pca_led_channels:
        pca.channels[ch].duty_cycle = 0
    GPIO.output(gpio_led_pin, GPIO.LOW)
    GPIO.cleanup()
    print("Program terminated.")
