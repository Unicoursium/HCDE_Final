# === Raspberry Pi code controlling Arduino LEDs via serial ===
# Buttons → Raspberry Pi GPIO (8 total)
# LEDs  → Arduino (serial commands)

from gpiozero import Button, LED
from time import sleep, time
from random import sample
import pygame, os, serial, threading

# ---------------- GPIO & Serial ----------------
button_pins = [17, 27, 22, 5, 6, 26, 16, 24]   # updated GPIO layout
buttons      = [Button(pin, pull_up=True) for pin in button_pins]

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
sleep(2)  # Arduino boot delay

mist = LED(26)  # optional relay

# ---------------- Audio (thread‑safe) ----------------
pygame.mixer.init()
_play_lock = threading.Lock()

def _play(path):
    with _play_lock:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Audio error: {e}")

def play_async(fname: str):
    threading.Thread(target=_play, args=(os.path.join("allure", fname),), daemon=True).start()

# ---------------- Arduino LED helpers ----------------
# one‑byte protocol: '0'..'7' = ON, 'A'..'H' = OFF

def send_led(i: int, on: bool):
    if 0 <= i < 8:
        ser.write((chr(ord('0')+i) if on else chr(ord('A')+i)).encode())

def leds_on(idx_iter):
    for i in idx_iter: send_led(i, True)

def leds_off(idx_iter):
    for i in idx_iter: send_led(i, False)

# ---------------- Helpers ----------------

def get_pressed():
    return [i for i,b in enumerate(buttons) if b.is_pressed]

def wait_release():
    while any(b.is_pressed for b in buttons):
        sleep(0.02)

# ---------------- Game Globals ----------------
genarr = []
player_count = 1
stepnum = step_size = current_step = 0

# ---------------- States ----------------

def code_state():
    print("Code state: waiting for first press …")
    while True:
        for i in range(8):
            send_led(i, True); sleep(0.12); send_led(i, False)
            if any(b.is_pressed for b in buttons):
                leds_off(range(8)); wait_release(); return


def waiting_state():
    global player_count
    print("Waiting state: dynamic 2‑second window …")
    cycles   = 40          # 40 × 0.05 s ≈ 2 s
    interval = 0.05
    current  = -1          # force initial update
    for _ in range(cycles):
        pressed = get_pressed()
        new_cnt = len(pressed) if pressed else 1
        if new_cnt != current:
            current = new_cnt
            player_count = new_cnt
            leds_on(range(current))          # light first N
            leds_off(range(current, 8))      # turn off the rest
        sleep(interval)
    leds_off(range(8))
    print(f"Players detected: {player_count}")
    wait_release()


def generate_state():
    global genarr, stepnum, step_size
    genarr.clear()
    stepnum   = 3 if player_count > 5 else 8 - player_count
    step_size = 5 if player_count > 5 else player_count
    for _ in range(stepnum):
        genarr.append(sample(range(8), step_size))
    print("Sequence:")
    for idx,s in enumerate(genarr,1):
        print(f"  Step {idx}: {[n+1 for n in s]}")


def water_state():
    print("Water state: preview pattern …")
    for s in genarr:
        leds_on(s); sleep(0.8); leds_off(s); sleep(0.4)


def play_state():
    global current_step
    current_step = 0
    while current_step < stepnum:
        targets  = genarr[current_step]
        achieved = [False]*8
        print(f"Stage {current_step+1}/{stepnum}: {[t+1 for t in targets]}")
        wait_release()
        while True:
            pressed = get_pressed()
            wrong = [i for i in pressed if i not in targets]
            if wrong:
                for _ in range(5): leds_on(wrong); sleep(0.15); leds_off(wrong); sleep(0.15)
                leds_off(range(8)); mist.off(); return False
            for i in targets:
                if i in pressed and not achieved[i]:
                    achieved[i] = True; send_led(i, True); mist.on()
            if all(achieved[i] for i in targets):
                play_async(f"p{current_step+1}.wav")
                leds_off(targets); mist.off(); current_step += 1; break
            sleep(0.04)
    return True


def win_state():
    play_async("p8.wav"); t0 = time()
    while time() - t0 < 10:
        leds_on(range(8)); mist.on(); sleep(0.4)
        leds_off(range(8)); mist.off(); sleep(0.4)
    pygame.mixer.music.stop(); mist.off()

# ---------------- Main ----------------

def main():
    while True:
        code_state(); waiting_state(); generate_state()
        while True:
            water_state()
            if play_state(): win_state(); break
            print("Restarting from water preview …")

if __name__ == "__main__":
    main()
