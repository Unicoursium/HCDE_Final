#!/usr/bin/env python3
"""
Raspberry Pi master:
 – 8 GPIO buttons
 – Talks to Arduino Mega 2560 Pro via /dev/ttyUSB0 9600 bps
 – Uses threaded audio so music never blocks button reads
 – WAIT-state player LEDs are the four extra LEDs on Arduino D10-D13
 – GAME LEDs are on Arduino D2-D9
 – Pumps on Arduino D22-D29 (index 0-7)
"""

import os, threading, time, serial, pygame
from random import sample
from gpiozero import Button

# ------------------ GPIO ------------------
BUTTON_PINS = [17, 27, 22, 5, 6, 26, 16, 24]        # 8 buttons
buttons = [Button(pin, pull_up=True) for pin in BUTTON_PINS]

# ---------------- Serial ------------------
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)              # give Arduino time to reset

def send(cmd: str):
    """Send a '\n'-terminated textual command to Arduino."""
    ser.write((cmd + '\n').encode())

# helpers
def game_led(idx, on):   send(f"LED_{'ON' if on else 'OFF'} {idx}")
def wait_led(idx, on):   send(f"WAIT_{'ON' if on else 'OFF'} {idx}")
def pump(idx, on):       send(f"PUMP_{'ON' if on else 'OFF'} {idx}")

# ---------------- Audio -------------------
pygame.mixer.init()

def play_sound_async(filename: str):
    """Interrupt any current track and start new one in a thread."""
    def _worker(path):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print("Audio error:", e)
    path = os.path.join("allure", filename)
    threading.Thread(target=_worker, args=(path,), daemon=True).start()

# -------------- Utilities ----------------
def pressed_indices():
    return [i for i, b in enumerate(buttons) if b.is_pressed]

# -------------- Game Globals -------------
genarr       = []   # 2-D steps list
player_count = 1
stepnum      = 0
step_size    = 0

# -------------- States -------------------
def code_state():
    print("\nCODE STATE → waiting for first press")
    prev = any(pressed_indices())
    while True:
        for i in range(8):
            game_led(i, True); time.sleep(0.15); game_led(i, False)
            cur = any(pressed_indices())
            if cur and not prev:           # rising edge
                for j in range(8): game_led(j, False)
                return
            prev = cur

def waiting_state():
    global player_count
    cycles, dt = 40, 0.05                 # ≈2 s total
    player_count = 1

    for _ in range(cycles):
        now = pressed_indices()
        live = len(now) if now else 1
        if live != player_count:
            player_count = live
            # update 4 waiting LEDs (cap at 4)
            for i in range(4):
                wait_led(i, i < player_count)
        time.sleep(dt)

    # clear wait LEDs
    for i in range(4): wait_led(i, False)
    print("Players detected:", player_count)

def generate_state():
    global genarr, stepnum, step_size
    genarr.clear()
    if player_count > 5:
        stepnum, step_size = 3, 5
    else:
        stepnum, step_size = 8 - player_count, player_count
    for _ in range(stepnum):
        genarr.append(sample(range(8), step_size))
    print("Sequence:", [[n+1 for n in s] for s in genarr])

def water_state():
    print("WATER STATE → demo spray each step")
    for step in genarr:
        for i in step: pump(i, True)
        time.sleep(1)
        for i in step: pump(i, False)
        time.sleep(0.7)

def play_state():
    for stage, targets in enumerate(genarr, start=1):
        triggered = [False]*8
        print(f"PLAY STATE step {stage}", [n+1 for n in targets])

        while True:
            pressed = pressed_indices()

            # wrong press?
            wrong = [idx for idx in pressed if idx not in targets]
            if wrong:
                idx = wrong[0]
                print("Wrong:", idx+1)
                for _ in range(5):
                    game_led(idx, True);  time.sleep(0.2)
                    game_led(idx, False); time.sleep(0.2)
                for i in range(8): game_led(i, False); pump(i, False)
                return False

            # correct presses
            for idx in targets:
                if idx in pressed and not triggered[idx]:
                    game_led(idx, True)
                    pump(idx, True)
                    triggered[idx] = True

            if all(triggered[i] for i in targets):
                play_sound_async(f"p{stage}.wav")
                time.sleep(0.5)
                for idx in targets:
                    game_led(idx, False); pump(idx, False)
                break

            time.sleep(0.05)
    return True

def win_state():
    print("WIN STATE")
    play_sound_async("p8.wav")
    t0 = time.time()
    while time.time()-t0 < 10:
        for i in range(8): game_led(i, True); pump(i, True)
        time.sleep(0.5)
        for i in range(8): game_led(i, False); pump(i, False)
        time.sleep(0.5)

# -------------- Main Loop ---------------
while True:
    code_state()
    waiting_state()
    generate_state()
    while True:
        water_state()
        if play_state():
            win_state()
            break
        else:
            print("Restarting from WATER STATE")
