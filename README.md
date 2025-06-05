# 😁**Hi, This is Group WHYYYYY@Design Engineering**
This is our HCDE(Human Centered Design Engineering) Project, and here's the description.

I am **Unico**, and I was responsible for the **entire prototyping process** of this project.  
All aspects of the system—including **hardware wiring, GPIO setup, physical assembly, interaction logic programming, modeling, 3D rendering, sound integration, manual fabrication, and part of visual refinement**—were completed by me and my groupmates.  
This prototype is built on a Raspberry Pi platform, combining **multistage interaction states, real-time button/LED control, audio feedback, and multiplayer coordination** to deliver a complete, immersive, and reusable interactive experience.

## 🤝 Team Contributions

While I was responsible for the full implementation of this prototype, I would like to acknowledge the valuable contributions of my teammates:

I cannot reveal their names unless they wish.

- Designed the overall game mechanics and core interaction logic.
- Independently created the physical form and aesthetic design of the Lo-Fi prototype.
- Assisted in the construction and detailing of both the Lo-Fi model and this interactive system.
- Helped test the Lo-Fi prototype and gathered user feedback for iterative improvement.
- Completed the production of the presentation PPT and Delivery Report.

---
# 💡 Magic Fountain

A playful, multi-user interactive installation powered by Raspberry Pi, designed to simulate a physical "water fountain challenge" using buttons, LEDs, and synchronized music.

This project allows multiple players to participate simultaneously in a memory-based button game. Each stage is visualized with LED lighting, accompanied by audio feedback and simulated water fountains (via print statements or real hardware in future upgrades).

---

## Project View Overview

### 1. **Code State**
- 8 LEDs light up one by one in a loop (button 1–8), indicating the system is waiting for players.
- When **any button is pressed**, the game proceeds to the next phase.

### 2. **Waiting State**
- Waits 2 seconds for players to stand on buttons.
- Number of pressed buttons determines the **player count** (default: 1).
- After detection, **all 9 LEDs flash twice** to confirm the setup.

### 3. **Generate State**
- Based on player count:
  - If players > 5 → `stepnum = 3`, each step includes 5 random buttons.
  - If players ≤ 5 → `stepnum = 8 - player count`, each step includes `player count` buttons.
- Generates a 2D list `genarr`, e.g.:
  ```python
  [
    [1, 2, 7],
    [1, 4, 5],
    [4, 8, 9]
  ]
  ```
- Each sublist represents the buttons to step on for that stage.

### 4. **Water State**
- Demonstrates each step's required buttons.
- **In demo mode**: flashes corresponding LEDs.
- **In normal mode**: prints button numbers simulating water pump spray.

### 5. **Play State**
- For each stage:
  - The **status LED stays on** as the signal to start.
  - Players step on the required buttons (simultaneously or gradually).
  - As each correct button is pressed, its LED lights up and water spray is printed.
  - Once all correct buttons are pressed:
    - That stage is completed.
    - A stage-specific music file (`p1.wav`, `p2.wav`, ..., `p7.wav`) is played from the `./allure/` folder.
  - ❌ **If a wrong button is pressed**:
    - That button’s LED **flashes 5 times**.
    - All LEDs turn off.
    - Current music is stopped.
    - The game replays the current fountain sequence (back to water state).

### 6. **Win State**
- After all stages are cleared:
  - Victory music `p8.wav` plays.
  - All LEDs flash together for 10 seconds.
  - After 10 seconds, music stops and the game resets to `code_state`.

---

## 🎵 Audio System

- Music files (`p1.wav` to `p8.wav`) must be placed in the `./allure/` directory.
- Each stage completion triggers playback of the corresponding `.wav` file.
- Music is **interrupted immediately** if the next stage is entered early.

---

## 📦 Hardware Setup

| Component        | Count | Notes                                   |
|------------------|-------|------------------------------------------|
| Buttons          | 9     | GPIO: `[26,14,15,18,23,24,25,8,7]`        |
| LEDs             | 9     | GPIO: `[2,3,4,17,27,22,10,9,11]`          |
| Status LED       | 1     | GPIO: `19`                                |
| Raspberry Pi     | 1     | Any model with ≥ 24 usable GPIO pins      |
| Optional Speaker | 1     | For playing `.wav` files via pygame       |

---

## ⚙️ Dependencies

- `gpiozero`
- `pygame` (for audio)

Install pygame:
```bash
sudo apt install python3-pygame
```
---
