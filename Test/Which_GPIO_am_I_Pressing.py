import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# Temporarily test all 8 pins to see which button is on which GPIO
test_pins = [17, 27, 22, 5, 6, 26, 16, 24]

for pin in test_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Press buttons one by one to test mapping...")

try:
    while True:
        for pin in test_pins:
            if not GPIO.input(pin):
                print(f"GPIO {pin} is being pressed")
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Done.")
