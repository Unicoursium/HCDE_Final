# === Raspberry Pi code rewritten to control Arduino LEDs over serial ===
# LED output is handled by Arduino via /dev/ttyUSB0
# Buttons are on GPIO, total 8 buttons, no status LED, no 9th button

from gpiozero import Button
from time import sleep
from random import sample
from signal import pause
import pygame
import os
import serial
import threading

# Button pins (8 buttons)
button_pins = [5, 14, 15, 18, 23, 24, 25, 8]
buttons = [Button(pin, pull_up=True) for pin in button_pins]

# Serial connection to Arduino
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
sleep(2)  # Wait for Arduino to initialize

# Mist pin (still local)
mist_pin = 26
from gpiozero import LED
mist = LED(mist_pin)

# Sound
pygame.mixer.init()
playback_lock = threading.Lock()

def play_soundend(filename):
    path = os.path.join("allure", filename)
    with playback_lock:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Failed to play {filename}: {e}")

def play_sound(filename):
    path = os.path.join("allure", filename)
    with playback_lock:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Failed to play {filename}: {e}")

def play_sound_threaded(filename):
    threading.Thread(target=play_sound, args=(filename,), daemon=True).start()

def send_led(index, state):
    if 0 <= index <= 7:
        cmd = chr(ord('0') + index) if state else chr(ord('A') + index)
        ser.write(cmd.encode())

def flash_leds(indices, duration=1.0):
    for i in indices:
        send_led(i, True)
    sleep(duration)
    for i in indices:
        send_led(i, False)

def get_pressed_indices():
    return [i for i, btn in enumerate(buttons) if btn.is_pressed]

def code_state():
    print("Waiting for any button press...")
    while True:
        for i in range(8):
            send_led(i, True)
            sleep(0.15)
            send_led(i, False)
            if any(btn.is_pressed for btn in buttons):
                for i in range(8):
                    send_led(i, False)
                return

def waiting_state():
    global player_count
    print("\nWAITING STATE: Waiting 2 seconds...")
    sleep(2)
    pressed = get_pressed_indices()
    player_count = len(pressed) if pressed else 1
    print(f"Detected players: {player_count}")
    for _ in range(2):
        for i in range(8):
            send_led(i, True)
        sleep(0.15)
        for i in range(8):
            send_led(i, False)
        sleep(0.15)

def generate_state():
    global genarr, stepnum, step_size
    genarr.clear()
    if player_count > 5:
        stepnum = 3
        step_size = 5
    else:
        stepnum = 8 - player_count
        step_size = player_count
    print(f"\ngen: stepnum = {stepnum}, step_size = {step_size}")
    for i in range(stepnum):
        step = sample(range(8), step_size)
        genarr.append(step)
    print("Generated sequence:")
    for idx, step in enumerate(genarr):
        print(f"  Step {idx+1}: {[s+1 for s in step]}")

def water_state():
    print("\nWATER STATE (Demo): Flashing LEDs for each step...")
    for idx, step in enumerate(genarr):
        print(f"  Step {idx+1}: Flashing LEDs for buttons {[s+1 for s in step]}")
        for i in step:
            send_led(i, True)
        sleep(1)
        for i in step:
            send_led(i, False)
        sleep(0.7)
    print("Moving to PLAY STATE...")

def play_state():
    global current_step
    current_step = 0
    while current_step < stepnum:
        step_targets = genarr[current_step]
        triggered = [False] * 8
        print(f"\nPLAY STATE: Step {current_step+1}, targets: {[x+1 for x in step_targets]}")
        while True:
            pressed = get_pressed_indices()
            for idx in pressed:
                if idx not in step_targets:
                    print(f"Wrong button {idx+1} pressed!")
                    for _ in range(5):
                        send_led(idx, True)
                        sleep(0.2)
                        send_led(idx, False)
                        sleep(0.2)
                    for i in range(8):
                        send_led(i, False)
                    mist.off()
                    return False
            for i in step_targets:
                if i in pressed and not triggered[i]:
                    send_led(i, True)
                    print(f"Water spraying at {i+1}")
                    mist.on()
                    triggered[i] = True
            if all(triggered[i] for i in step_targets):
                print(f"Step {current_step+1} complete!")
                play_sound_threaded(f"p{current_step+1}.wav")
                sleep(0.2)
                for i in step_targets:
                    send_led(i, False)
                sleep(2)
                mist.off()
                current_step += 1
                break
            sleep(0.05)
    return True

def win_state():
    print("\nWIN STATE")
    play_soundend("p8.wav")
    for _ in range(10):
        mist.off()
        mist.on()
        for i in range(8):
            send_led(i, True)
        print("All water pumps spraying!")
        sleep(0.5)
        for i in range(8):
            send_led(i, False)
        sleep(0.5)
    pygame.mixer.music.stop()
    mist.off()
    print("Resetting game...\n")

# Globals
genarr = []
player_count = 1
stepnum = 0
step_size = 0
current_step = 0

def main():
    while True:
        code_state()
        waiting_state()
        generate_state()
        while True:
            water_state()
            success = play_state()
            if success:
                win_state()
                break
            else:
                print("Restarting from WATER STATE...")

main()
