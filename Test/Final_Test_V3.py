# === Raspberry Pi code rewritten to control Arduino LEDs over serial ===
# LED output is handled by Arduino via /dev/ttyUSB0
# Buttons are on GPIO, total 8 buttons, no status LED, no 9th button

from gpiozero import Button, LED
from time import sleep, time
from random import sample
import pygame
import os
import serial
import threading

# ---------------------- GPIO & Serial Setup ----------------------
button_pins = [5, 14, 15, 18, 23, 24, 25, 8]   # 8 physical floor buttons
buttons = [Button(pin, pull_up=True) for pin in button_pins]

# Serial connection to Arduino (TX/RX)
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
sleep(2)  # allow Arduino boot

# Local mist relay (optional)
mist = LED(26)

# ---------------------- Audio (thread‑safe) ----------------------
pygame.mixer.init()
_play_lock = threading.Lock()

def _play_wave(path: str):
    with _play_lock:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Failed to play '{path}': {e}")

def play_sound_async(filename: str):
    threading.Thread(target=_play_wave, args=(os.path.join("allure", filename),), daemon=True).start()

# ---------------------- Arduino LED helpers ----------------------
# send one byte: '0'..'7' turn LED i ON  |  'A'..'H' turn LED i OFF

def send_led(idx: int, state: bool):
    if 0 <= idx < 8:
        ser.write((chr(ord('0') + idx) if state else chr(ord('A') + idx)).encode())

# group helpers

def leds_on(indices):
    for i in indices:
        send_led(i, True)

def leds_off(indices):
    for i in indices:
        send_led(i, False)

# ---------------------- Utility ----------------------

def get_pressed():
    return [i for i, btn in enumerate(buttons) if btn.is_pressed]

# wait until all buttons released (debounce between stages)

def wait_release():
    while any(btn.is_pressed for btn in buttons):
        sleep(0.02)

# ---------------------- Game State ----------------------
genarr = []
player_count = 1
stepnum = step_size = current_step = 0

# ---------------------- Game Phases ----------------------

def code_state():
    print("Waiting for player input …")
    while True:
        for i in range(8):
            send_led(i, True)
            sleep(0.12)
            send_led(i, False)
            if any(btn.is_pressed for btn in buttons):
                leds_off(range(8))
                wait_release()
                return

def waiting_state():
    global player_count
    print("Detecting players … 2 s window")
    sleep(2)
    pressed = get_pressed()
    player_count = len(pressed) or 1
    print(f"Players detected: {player_count}")
    for _ in range(2):
        leds_on(range(8))
        sleep(0.25)
        leds_off(range(8))
        sleep(0.25)


def generate_state():
    global genarr, stepnum, step_size
    genarr.clear()
    stepnum  = 3 if player_count > 5 else 8 - player_count
    step_size = 5 if player_count > 5 else player_count
    for _ in range(stepnum):
        genarr.append(sample(range(8), step_size))
    print("Sequence:")
    for idx, st in enumerate(genarr, 1):
        print(f"  Step {idx}: {[s+1 for s in st]}")


def water_state():
    print("Previewing pattern …")
    for st in genarr:
        leds_on(st)
        sleep(0.8)
        leds_off(st)
        sleep(0.4)
    print("Ready to play!")


def play_state():
    global current_step
    current_step = 0
    while current_step < stepnum:
        targets = genarr[current_step]
        achieved = [False]*8
        print(f"Stage {current_step+1}/{stepnum} targets {[t+1 for t in targets]}")
        wait_release()  # ensure fresh press
        while True:
            pressed = get_pressed()
            # Incorrect button pressed
            wrong = [idx for idx in pressed if idx not in targets]
            if wrong:
                print(f"Wrong button {wrong[0]+1}")
                for _ in range(5):
                    leds_on(wrong)
                    sleep(0.15)
                    leds_off(wrong)
                    sleep(0.15)
                leds_off(range(8)); mist.off(); return False
            # Correct buttons pressed
            for idx in targets:
                if idx in pressed and not achieved[idx]:
                    achieved[idx] = True
                    send_led(idx, True)
                    mist.on()
            # Stage complete?
            if all(achieved[idx] for idx in targets):
                print("Stage complete")
                play_sound_async(f"p{current_step+1}.wav")
                leds_off(targets)
                mist.off()
                current_step += 1
                break
            sleep(0.04)
    return True


def win_state():
    print("WIN state – celebration!")
    play_sound_async("p8.wav")
    t0 = time()
    while time() - t0 < 10:
        leds_on(range(8)); mist.on(); sleep(0.4)
        leds_off(range(8)); mist.off(); sleep(0.4)
    pygame.mixer.music.stop(); mist.off()

# ---------------------- Main Loop ----------------------

def main():
    while True:
        code_state()
        waiting_state()
        generate_state()
        while True:
            water_state()
            if play_state():
                win_state(); break
            else:
                print("Restarting from water preview …")

if __name__ == "__main__":
    main()
