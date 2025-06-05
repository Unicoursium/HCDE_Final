from gpiozero import Button
from time import sleep, time
from random import sample
import pygame
import os
import serial

# === GPIO Setup ===
button_pins = [17, 27, 22, 5, 6, 26, 16, 24]

# === Serial Setup ===
# Make sure the serial port and baud rate match the Arduino sketch
arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

# === Initialize hardware ===
buttons = [Button(pin, pull_up=True) for pin in button_pins]

# === Initialize audio ===
pygame.mixer.init()

def play_sound(filename):
    path = os.path.join("allure", filename)
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Failed to play {filename}: {e}")

# === Arduino Communication ===
def send_command(cmd):
    try:
        arduino.write((cmd + '\n').encode())
        sleep(0.01)
    except Exception as e:
        print(f"Failed to send command '{cmd}': {e}")

def turn_on_led(i):
    send_command(f"LED_ON {i}")

def turn_off_led(i):
    send_command(f"LED_OFF {i}")

def turn_on_pump(i):
    send_command(f"PUMP_ON {i}")

def turn_off_pump(i):
    send_command(f"PUMP_OFF {i}")

def get_pressed_indices():
    return [i for i, btn in enumerate(buttons) if btn.is_pressed]

# === Game State ===
genarr = []
player_count = 1
stepnum = 0
step_size = 0
current_step = 0

# === States ===
def code_state():
    print("\nEntering CODE STATE: Waiting for any button press...")
    while True:
        for i in range(8):
            turn_on_led(i)
            sleep(0.15)
            turn_off_led(i)
            if any(btn.is_pressed for btn in buttons):
                for i in range(8):
                    turn_off_led(i)
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
            turn_on_led(i)
        sleep(0.3)
        for i in range(8):
            turn_off_led(i)
        sleep(0.3)

def generate_state():
    global genarr, stepnum, step_size
    genarr.clear()
    if player_count > 5:
        stepnum = 3
        step_size = 5
    else:
        stepnum = 8 - player_count
        step_size = player_count
    print(f"\nGENERATE STATE: stepnum = {stepnum}, step_size = {step_size}")
    for i in range(stepnum):
        step = sample(range(8), step_size)
        genarr.append(step)
    print("Generated sequence:")
    for idx, step in enumerate(genarr):
        print(f"  Step {idx+1}: {[s+1 for s in step]}")

def water_state():
    print("\nWATER STATE: Activating pumps for each step...")
    for idx, step in enumerate(genarr):
        print(f"  Step {idx+1}: Activating pumps for {[s+1 for s in step]}")
        for i in step:
            turn_on_pump(i)
        sleep(1)
        for i in step:
            turn_off_pump(i)
        sleep(0.5)
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
                        turn_on_led(idx)
                        sleep(0.2)
                        turn_off_led(idx)
                        sleep(0.2)
                    for i in range(8):
                        turn_off_led(i)
                        turn_off_pump(i)
                    return False

            for i in step_targets:
                if i in pressed and not triggered[i]:
                    turn_on_led(i)
                    turn_on_pump(i)
                    print(f"Water spraying at {i+1}")
                    triggered[i] = True

            if all(triggered[i] for i in step_targets):
                print(f"Step {current_step+1} complete!")
                play_sound(f"p{current_step+1}.wav")
                sleep(1)
                for i in step_targets:
                    turn_off_led(i)
                    turn_off_pump(i)
                current_step += 1
                break

            sleep(0.05)

    return True

def win_state():
    print("\nWIN STATE: All steps completed! Celebration begins...")
    play_sound("p8.wav")

    start_time = time()
    while time() - start_time < 10:
        for i in range(8):
            turn_on_led(i)
            turn_on_pump(i)
        print("ALL water pumps spraying!")
        sleep(0.5)
        for i in range(8):
            turn_off_led(i)
            turn_off_pump(i)
        sleep(0.5)

    pygame.mixer.music.stop()
    print("Resetting game...\n")

# === Main Loop ===
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
