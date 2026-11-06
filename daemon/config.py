# ==============================================================================
#  Zoth Cursorz & Sovereign Computer-Use Daemon
#  Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform
# ==============================================================================

DAEMON_HOST = "127.0.0.1"
DAEMON_PORT = 9990
WS_PORT = 9991
SHARED_MEM_PATH = "/dev/shm/zoth_cursorz.json"
MAX_CURSORS = 16

DEFAULT_AGENT_STYLES = {
    "1nc0gn30": {
        "color": "#39d353",
        "label": "1nc0gn30",
        "symbol": "⣿",
        "icon": "reticle",
        "glow": "rgba(57, 211, 83, 0.45)"
    },
    "zoth": {
        "color": "#f5b82e",
        "label": "Zoth",
        "symbol": "⬡",
        "icon": "arrow",
        "glow": "rgba(245, 184, 46, 0.45)"
    },
    "sentinel": {
        "color": "#ef4444",
        "label": "Sentinel",
        "symbol": "◈",
        "icon": "target",
        "glow": "rgba(239, 68, 68, 0.45)"
    },
    "foundry": {
        "color": "#38bdf8",
        "label": "Foundry",
        "symbol": "⚙",
        "icon": "crosshair",
        "glow": "rgba(56, 189, 248, 0.45)"
    },
    "default": {
        "color": "#d4af37",
        "label": "Agent",
        "symbol": "✦",
        "icon": "arrow",
        "glow": "rgba(212, 175, 55, 0.45)"
    }
}
