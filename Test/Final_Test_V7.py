# === Raspberry Pi master script (Final_Test_V6.py) ===
# Buttons on GPIO, LEDs driven by Arduino via Serial1 commands
# • 8 buttons (GPIO 17 27 22 5 6 26 16 24)
# • 8 LEDs on Arduino D2–D9  (index 0-7)
# • Optional “mist” MOSFET on Pi GPIO 26 (can be removed)
# • Audio: threaded playback so button input is never blocked

from gpiozero import Button, LED
from time import sleep, time
from random import sample
import threading, pygame, serial, os, sys

# ------------------------------------------------------------------
# ‣ Hardware setup
# ------------------------------------------------------------------
button_pins = [17, 27, 22, 5, 6, 26, 16, 24]         # 8 buttons
buttons = [Button(p, pull_up=True) for p in button_pins]

try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    sleep(2)                                         # wait for Arduino reset
except serial.SerialException:
    print("ERROR: Arduino serial port not found.")
    sys.exit(1)

# if you still want a “spray” indicator on Pi side:
mist = LED(7)   # comment out if unused

# ------------------------------------------------------------------
# ‣ Thread-safe audio helpers
# ------------------------------------------------------------------
pygame.mixer.init()
_play_lock = threading.Lock()

def _play_sound(filename):
    """LOW-LEVEL: stop current music and play filename (blocking in this thread)."""
    with _play_lock:
        path = os.path.join("allure", filename)
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Audio error: {e}")

def play_sound_threaded(filename):
    """Launch non-blocking audio (previous track stops instantly)."""
    threading.Thread(target=_play_sound, args=(filename,), daemon=True).start()

def stop_audio():
    with _play_lock:
        pygame.mixer.music.stop()

# ------------------------------------------------------------------
# ‣ Arduino LED helpers
#   Protocol: send one ASCII char per LED action
#   '0'–'7'  → LED index ON      |  'A'–'H' → LED index OFF
# ------------------------------------------------------------------
def send_led(idx: int, state: bool):
    if 0 <= idx <= 7:
        char = chr(ord('0') + idx) if state else chr(ord('A') + idx)
        try:
            ser.write(char.encode())
        except serial.SerialException:
            print("Serial write failure.")

def flash_leds(indices, duration=0.3):
    for i in indices:
        send_led(i, True)
    sleep(duration)
    for i in indices:
        send_led(i, False)

# ------------------------------------------------------------------
# ‣ Utility
# ------------------------------------------------------------------
def get_pressed_indices():
    """Return list of button indices (0-7) currently pressed."""
    return [i for i, btn in enumerate(buttons) if btn.is_pressed]

# ------------------------------------------------------------------
# ‣ State 1 : Code State  (waiting for first “edge” press)
# ------------------------------------------------------------------
def code_state():
    print("CODE STATE  – waiting for first press")
    prev_pressed = any(btn.is_pressed for btn in buttons)

    while True:
        for i in range(8):                 # simple marquee animation
            send_led(i, True)
            sleep(0.15)
            send_led(i, False)

            cur_pressed = any(btn.is_pressed for btn in buttons)
            if cur_pressed and not prev_pressed:
                for j in range(8):
                    send_led(j, False)
                return
            prev_pressed = cur_pressed

# ------------------------------------------------------------------
# ‣ State 2 : Waiting State  (dynamic 2-second player count)
# ------------------------------------------------------------------
def waiting_state():
    global player_count
    total_cycles = 40          # 0.05 s × 40 ≈ 2 s
    poll_delay   = 0.05
    player_count = 1           # default

    for _ in range(total_cycles):
        pressed_now = get_pressed_indices()
        live = len(pressed_now) if pressed_now else 1
        if live != player_count:
            player_count = live
            for i in range(8):
                send_led(i, i < player_count)   # show current count
        sleep(poll_delay)

    # clear LEDs before next state
    for i in range(8):
        send_led(i, False)
    print(f"Players detected: {player_count}")

# ------------------------------------------------------------------
# ‣ State 3 : Generate sequence
# ------------------------------------------------------------------
def generate_state():
    global genarr, stepnum, step_size
    genarr = []
    if player_count > 5:
        stepnum, step_size = 3, 5
    else:
        stepnum, step_size = 8 - player_count, player_count

    for _ in range(stepnum):
        genarr.append(sample(range(8), step_size))

    print("Generated steps:")
    for idx, step in enumerate(genarr, 1):
        print(f"  Step {idx}: {[s+1 for s in step]}")

# ------------------------------------------------------------------
# ‣ State 4 : Water State (demo = flash LEDs)
# ------------------------------------------------------------------
def water_state():
    print("WATER STATE – demo flash")
    for idx, step in enumerate(genarr, 1):
        print(f"  Step {idx}: LEDs {[s+1 for s in step]}")
        flash_leds(step, duration=1)
        sleep(0.5)

# ------------------------------------------------------------------
# ‣ State 5 : Play State
# ------------------------------------------------------------------
def play_state():
    current_step = 0
    while current_step < stepnum:
        targets = genarr[current_step]
        triggered = [False]*8
        print(f"PLAY  Step {current_step+1} targets { [t+1 for t in targets] }")

        while True:
            pressed = get_pressed_indices()

            # Wrong press?
            wrong = [idx for idx in pressed if idx not in targets]
            if wrong:
                print(f"Wrong button {wrong[0]+1}")
                for _ in range(5):
                    flash_leds(wrong, 0.2)
                for i in range(8):
                    send_led(i, False)
                mist.off()
                stop_audio()
                return False

            # Handle correct presses
            for idx in targets:
                if idx in pressed and not triggered[idx]:
                    triggered[idx] = True
                    send_led(idx, True)
                    mist.on()

            # All target buttons pressed
            if all(triggered[idx] for idx in targets):
                print("Step complete")
                play_sound_threaded(f"p{current_step+1}.wav")
                sleep(0.4)                 # brief feedback gap
                for idx in targets:
                    send_led(idx, False)
                mist.off()
                current_step += 1
                break

            sleep(0.02)
    return True

# ------------------------------------------------------------------
# ‣ State 6 : Win State
# ------------------------------------------------------------------
def win_state():
    print("WIN STATE – celebration 10 s")
    play_sound_threaded("p8.wav")
    t0 = time()
    while time() - t0 < 10:
        for i in range(8):
            send_led(i, True)
            mist.on()
        sleep(0.5)
        for i in range(8):
            send_led(i, False)
            mist.off()
        sleep(0.5)
    stop_audio()
    print("Restarting…\n")

# ------------------------------------------------------------------
# ‣ Globals & Main loop
# ------------------------------------------------------------------
player_count = 1
genarr, stepnum, step_size = [], 0, 0

def main():
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
                print("Retry from water state")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting…")
        stop_audio()
        for i in range(8):
            send_led(i, False)
        mist.off()
        ser.close()
