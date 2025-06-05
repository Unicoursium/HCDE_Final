import time
import board
import busio
from adafruit_pca9685 import PCA9685

# Set up I2C and PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 1000  # Suitable for LEDs

# Define LED channels (channels 5 to 12 = pins 6 to 13)
led_channels = [5, 6, 7, 8, 9, 10, 11, 12]
leds = [pca.channels[ch] for ch in led_channels]

try:
    while True:
        for led in leds:
            led.duty_cycle = 0xFFFF  # Turn on LED
            time.sleep(0.3)
            led.duty_cycle = 0x0000  # Turn off LED
except KeyboardInterrupt:
    # Turn off all LEDs when exiting
    for led in leds:
        led.duty_cycle = 0
    print("Program stopped.")
