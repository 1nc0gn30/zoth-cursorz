# Zoth Cursorz — Multi-Agent Virtual Cursor Engine & Computer Use Daemon

<div align="center">
  <h3>Parallel Multi-Agent Computer Use for ZothOS</h3>
  <p>Eliminates the single-cursor bottleneck in AI desktop automation.</p>
</div>

---

## What It Does
**Zoth Cursorz** allows multiple autonomous agents (`1nc0gn30`, `Zoth`, `Sentinel`, `Foundry`) to visually and programmatically interact with the desktop simultaneously:
- **60 FPS Transparent Overlay (`overlay/`)**: Renders distinct, color-coded virtual cursors, smooth motion trails, telemetry badges, and click ripples across all monitors without blocking human mouse interaction.
- **Computer-Use Daemon (`daemon/server.py` :9990)**: Fast REST & shared memory API (`/dev/shm/zoth_cursorz.json`) to spawn, navigate, and dispatch actions for individual agent pointers.
- **Direct Input Injection (`daemon/input_engine.py`)**: Human-like mouse movements, clicks, typing, and key sequences via `ydotool` (Wayland) and `xdotool` (X11).
- **VLM & API Adapters (`adapters/`)**: Adapters for open-source **UI-TARS** coordinate grounding and Anthropic **Computer Use API**.

---

## Agent Visual Styles

| Agent | Symbol | Style | Icon | Color |
| :--- | :---: | :--- | :--- | :--- |
| **`1nc0gn30`** | `⣿` | Matrix Emerald | Reticle & Crosshair | `#39d353` |
| **`Zoth`** | `⬡` | 24K Liquid Gold | Astrolabe Arrow | `#f5b82e` |
| **`Sentinel`** | `◈` | Crimson Alert | Target Diamond | `#ef4444` |
| **`Foundry`** | `⚙` | Cyan Precision | Crosshair | `#38bdf8` |

---

## CLI Commands

### 1. Multi-Cursor Management (`zoth-cursorz`)
```bash
# Check status
zoth-cursorz status

# List active virtual cursors
zoth-cursorz list

# Spawn a new cursor for an agent
zoth-cursorz spawn 1nc0gn30 '#39d353' 1400 420

# Move an agent cursor with status badge
zoth-cursorz move 1nc0gn30 800 600 "Refactoring code"

# Trigger a click animation
zoth-cursorz click 1nc0gn30 left
```

### 2. Autonomous Computer Use (`zoth-computer-use`)
```bash
# Move and execute
zoth-computer-use move 960 540 1nc0gn30

# Click
zoth-computer-use click left 960 540 1nc0gn30

# Type text
zoth-computer-use type "cargo build --release"

# Send keystroke
zoth-computer-use key Return
```

---

## Attribution & Sovereignty
Engineered by **Neal Frazier Tech** ([@1nc0gn30](https://github.com/1nc0gn30)) • **NullAI Platform**. 100% Free & Open-Access.
