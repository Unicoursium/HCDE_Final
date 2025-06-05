# === Raspberry Pi code controlling Arduino LEDs via serial ===
# Updated button GPIOs + dynamic waiting_state logic

from gpiozero import Button, LED
from time import sleep, time
from random import sample
import pygame
import os
import serial
import threading

# ---------------------- GPIO & Serial Setup ----------------------
button_pins = [17, 27, 22, 5, 6, 26, 16, 24]  # updated pins
buttons = [Button(pin, pull_up=True) for pin in button_pins]

# Serial connection to Arduino
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
sleep(2)  # allow Arduino boot

mist = LED(26)  # local relay (optional)

# ---------------------- Audio ----------------------
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

def play_sound_async(fname: str):
    threading.Thread(target=_play_wave, args=(os.path.join("allure", fname),), daemon=True).start()

# ---------------------- Arduino LED helpers ----------------------

def send_led(idx: int, state: bool):
    if 0 <= idx < 8:
        ser.write((chr(ord('0') + idx) if state else chr(ord('A') + idx)).encode())

def leds_on(indices):
    for i in indices:
        send_led(i, True)

def leds_off(indices):
    for i in indices:
        send_led(i, False)

# ---------------------- Utilities ----------------------

def get_pressed():
    return [i for i, b in enumerate(buttons) if b.is_pressed]

def wait_release():
    while any(b.is_pressed for b in buttons):
        sleep(0.02)

# ---------------------- Game Globals ----------------------
genarr = []
player_count = 1
stepnum = step_size = current_step = 0

# ---------------------- States ----------------------

def code_state():
    print("Waiting for any button press …")
    while True:
        for i in range(8):
            send_led(i, True)
            sleep(0.12)
            send_led(i, False)
            if any(b.is_pressed for b in buttons):
                leds_off(range(8))
                wait_release()
                return


def waiting_state():
    global player_count
    print("Dynamic WAITING STATE (2 s window)")
    start = time()
    current_count = -1  # force first update
    while time() - start < 2:
        pressed = get_pressed()
        new_count = len(pressed) if pressed else 1
        if new_count != current_count:
            current_count = new_count
            player_count = new_count
            leds_on(range(current_count))
            leds_off(range(current_count, 8))
        sleep(0.05)
    leds_off(range(8))
    print(f"Final player count: {player_count}")
    wait_release()


def generate_state():
    global genarr, stepnum, step_size
    genarr.clear()
    stepnum = 3 if player_count > 5 else 8 - player_count
    step_size = 5 if player_count > 5 else player_count
    for _ in range(stepnum):
        genarr.append(sample(range(8), step_size))
    print("Sequence:")
    for idx, st in enumerate(genarr, 1):
        print(f"  Step {idx}: {[s+1 for s in st]}")


def water_state():
    print("Preview pattern …")
    for st in genarr:
        leds_on(st); sleep(0.8); leds_off(st); sleep(0.4)


def play_state():
    global current_step
    current_step = 0
    while current_step < stepnum:
        targets = genarr[current_step]
        achieved = [False]*8
        print(f"Stage {current_step+1}/{stepnum} → {[t+1 for t in targets]}")
        wait_release()
        while True:
            pressed = get_pressed()
            wrong = [i for i in pressed if i not in targets]
            if wrong:
                leds_on(wrong); sleep(0.15); leds_off(wrong)
                leds_off(range(8)); mist.off(); return False
            for i in targets:
                if i in pressed and not achieved[i]:
                    achieved[i] = True; send_led(i, True); mist.on()
            if all(achieved[i] for i in targets):
                play_sound_async(f"p{current_step+1}.wav")
                leds_off(targets); mist.off(); current_step += 1; break
            sleep(0.04)
    return True


def win_state():
    play_sound_async("p8.wav"); t0 = time()
    while time() - t0 < 10:
        leds_on(range(8)); mist.on(); sleep(0.4)
        leds_off(range(8)); mist.off(); sleep(0.4)
    pygame.mixer.music.stop(); mist.off()

# ---------------------- Main ----------------------

def main():
    while True:
        code_state(); waiting_state(); generate_state()
        while True:
            water_state()
            if play_state():
                win_state(); break
            else:
                print("Restarting from water preview …")

if __name__ == "__main__":
    main()
