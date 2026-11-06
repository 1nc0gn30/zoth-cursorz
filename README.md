# Zoth Cursorz — Multi-Agent Virtual Cursor Engine & Sovereign Computer-Use Daemon

<div align="center">
  <img src="https://raw.githubusercontent.com/1nc0gn30/zoth-os/main/assets/banner.png" alt="Zoth Cursorz Banner" width="100%" onerror="this.style.display='none'"/>
  <br />
  <p><strong>Parallel Multi-Agent Computer Use & Workflow Training Engine for ZothOS</strong></p>
  <p><em>Engineered by Neal Frazier Tech (<a href="https://github.com/1nc0gn30">@1nc0gn30</a>) • NullAI Platform Hub</em></p>
</div>

<br />

<div align="center">
  <a href="https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X"><img src="https://img.shields.io/badge/Support-Buy_Us_a_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Us a Coffee" /></a>
  <a href="https://nullai.tech"><img src="https://img.shields.io/badge/Security-100%25_Zero--Egress-10B981?style=for-the-badge&logo=shield&logoColor=black" alt="Zero Egress" /></a>
  <img src="https://img.shields.io/badge/License-GPL--3.0-D4AF37?style=for-the-badge" alt="GPL-3.0" />
</div>

---

## 1. Why Zoth Cursorz?

Every existing desktop automation framework—including Anthropic Computer Use, Bytebot, Agent-S, and UI-TARS—suffers from **agent serialization**:
- They rely on a **single global operating system cursor**.
- If Agent A is clicking a button, the user's real mouse is stolen.
- Agent B and Agent C cannot perform tasks simultaneously without colliding or requiring separate virtual machines.

**Zoth Cursorz breaks this bottleneck** with a **two-plane architecture**:
1. **Plane A (Visual Layer)**: A 60 FPS transparent, click-through multi-monitor overlay. Each autonomous agent (`1nc0gn30`, `Zoth`, `Sentinel`, `Foundry`) gets their own color-coded pointer with smooth motion trails, telemetry status badges, and click ripples. Human mouse clicks pass directly through.
2. **Plane B (Execution Layer)**: An autonomous computer-use daemon running on port `:9990` with sub-millisecond shared memory (`/dev/shm/zoth_cursorz.json`), low-level Wayland (`ydotool`) and X11 (`xdotool`) input injection, and vision-action planning.

---

## 2. Core Features

### ✦ Visual Multi-Agent Overlay (`overlay/`)
- **Independent Agent Pointers**:
  - `1nc0gn30`: Matrix Emerald (`#39d353`) cyber reticle & crosshair (`⣿ 1nc0gn30`).
  - `Zoth`: 24K Liquid Gold (`#f5b82e`) astrolabe arrow (`⬡ Zoth`).
  - `Sentinel`: Crimson Alert (`#ef4444`) target diamond (`◈ Sentinel`).
  - `Foundry`: Cyan Precision (`#38bdf8`) crosshair (`⚙ Foundry`).
- **Telemetry Badges**: Live action status displayed beside each cursor (e.g. `Refactoring code`, `Typing...`, `Clicking`).
- **Click-Through Transparency**: `setIgnoreMouseEvents(true, { forward: true })` ensures your physical keyboard and mouse remain 100% uninterrupted.

### ✦ Human Workflow Recording & Training (`training/`)
- **Record Once, Perfect Always**: Record manual workflows (mouse paths, click timings, typing sequences, key combinations) using `zoth-cursorz train start <preset_name>`.
- **Automatic Visual Landmark Crops**: Every click captures a micro-crop of the exact UI button/field, extracts OCR text (Tesseract), and computes color and edge density.
- **Saved Presets**: Stored as self-contained bundles in `training/presets/<name>/preset.json`.

### ✦ Pre-Flight Page Analysis & Drift Protection (`training/preset_runner.py`)
- **Layout Verification**: Before an agent executes a click during preset playback, it captures the live screen and searches a bounding window around the target coordinates using OpenCV Normalized Cross-Correlation.
- **Auto-Alignment**: If a button moved slightly ($\le 60\text{px}$) due to responsive layouts or scroll position, the cursor automatically snaps to the new coordinate.
- **Safety Intercept Modal (`review_ui/`)**: If the target element is missing or the page layout changed (score $< 0.65$), the action **halts immediately** and launches the side-by-side Review window showing the recorded landmark vs. current desktop state. You can review what changed and choose to safely cancel or override.

---

## 3. Installation & Setup

```bash
# Clone or navigate to the repository
cd ~/NullAITech/zoth-cursorz

# Binaries are installed to both ~/.local/bin and /usr/local/bin:
which zoth-cursorz
which zoth-computer-use

# Ensure system dependencies are present (pre-installed on ZothOS):
sudo apt install -y ydotool xdotool tesseract-ocr python3-opencv python3-pil
```

---

## 4. CLI Reference

### 🎮 Multi-Cursor Management (`zoth-cursorz`)

```bash
# Check daemon status & active cursors
zoth-cursorz status

# List all active virtual agent cursors
zoth-cursorz list

# Spawn an agent cursor
zoth-cursorz spawn 1nc0gn30 '#39d353' 1400 420

# Move agent cursor with custom action badge
zoth-cursorz move 1nc0gn30 800 600 "Refactoring code"

# Trigger click animation
zoth-cursorz click 1nc0gn30 left

# Launch the visual transparent overlay
zoth-cursorz overlay

# Start the background daemon
zoth-cursorz daemon
```

### 🧠 Workflow Training & Presets

```bash
# 1. Start recording a workflow preset
zoth-cursorz train start deploy_flow

# 2. Perform actions (clicks and typing are recorded with vision landmarks)
zoth-cursorz train click left
zoth-cursorz train type "npm run build"
zoth-cursorz train key Return

# 3. Stop recording and save the verified preset
zoth-cursorz train stop

# 4. List all saved presets
zoth-cursorz presets

# 5. Play back preset with pre-analysis protection
zoth-cursorz run deploy_flow 1nc0gn30
```

### ⚡ Computer-Use Actions (`zoth-computer-use`)

```bash
# Move and click
zoth-computer-use move 960 540 1nc0gn30
zoth-computer-use click left 960 540 1nc0gn30

# Type text into active window
zoth-computer-use type "cargo test --release"

# Send special key combinations
zoth-computer-use key Return
zoth-computer-use key ctrl+c

# High-level autonomous VLM prompt (UI-TARS or Claude)
zoth-computer-use prompt "Click the submit button" 1nc0gn30 ui-tars
```

---

## 5. API Reference (Port :9990)

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/health` | `GET` | Daemon status & active cursor count |
| `/api/cursors` | `GET` | List all active agent cursors & positions |
| `/api/cursors/spawn` | `POST` | Spawn a virtual cursor (`{ agent_id, name, color, x, y }`) |
| `/api/cursors/move` | `POST` | Move cursor (`{ agent_id, x, y, state, action_text }`) |
| `/api/cursors/click` | `POST` | Trigger click ripple (`{ agent_id, click_type }`) |
| `/api/action` | `POST` | High-level computer-use dispatch (`move`, `click`, `type`, `key`) |
| `/api/screenshot` | `GET` | Capture full-resolution desktop screenshot |

---

## 6. Sovereignty & Open Access
Every line of **Zoth Cursorz** is **100% free, unlocked, and open-access**. Zero paywalls, zero license keys, zero telemetry tracking.

- **Stripe Tip**: `https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X`
- **Solana Wallet**: `GG2eQbVh8ut1BK6j1A2tz7pSySdLpD38BgyEhGcxdXoK`
- **GitHub**: [@1nc0gn30](https://github.com/1nc0gn30) • **NullAI Platform**: [nullai.tech](https://nullai.tech)
