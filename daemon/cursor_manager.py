#!/usr/bin/env python3
# ==============================================================================
#  Zoth Cursorz — Virtual Pointer State Manager
#  Tracks multiple concurrent agent cursors with trajectory trails & clicks
# ==============================================================================

import time
import json
import os
from daemon.config import SHARED_MEM_PATH, DEFAULT_AGENT_STYLES, MAX_CURSORS

class VirtualCursor:
    def __init__(self, agent_id, name=None, color=None, icon=None, x=960, y=540):
        self.agent_id = agent_id
        preset = DEFAULT_AGENT_STYLES.get(agent_id, DEFAULT_AGENT_STYLES["default"])
        self.name = name or preset.get("label", agent_id)
        self.color = color or preset.get("color", "#d4af37")
        self.symbol = preset.get("symbol", "✦")
        self.icon = icon or preset.get("icon", "arrow")
        self.x = float(x)
        self.y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.state = "idle"  # idle, moving, clicking, typing, dragging
        self.action_text = ""
        self.last_click = 0.0
        self.click_type = None  # left, right, middle, double
        self.last_updated = time.time()
        self.trail = []  # list of [x, y, timestamp]

    def move_to(self, x, y, state="moving", action_text=""):
        now = time.time()
        self.target_x = float(x)
        self.target_y = float(y)
        self.state = state
        if action_text:
            self.action_text = action_text
        self.trail.append([self.x, self.y, now])
        if len(self.trail) > 12:
            self.trail.pop(0)
        self.x = float(x)
        self.y = float(y)
        self.last_updated = now

    def trigger_click(self, click_type="left"):
        now = time.time()
        self.last_click = now
        self.click_type = click_type
        self.state = "clicking"
        self.last_updated = now

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "color": self.color,
            "symbol": self.symbol,
            "icon": self.icon,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "state": self.state,
            "action_text": self.action_text,
            "last_click": self.last_click,
            "click_type": self.click_type,
            "last_updated": self.last_updated,
            "trail": self.trail
        }

class CursorManager:
    def __init__(self):
        self.cursors = {}

    def spawn(self, agent_id, name=None, color=None, icon=None, x=960, y=540):
        if len(self.cursors) >= MAX_CURSORS and agent_id not in self.cursors:
            return None
        cur = VirtualCursor(agent_id, name, color, icon, x, y)
        self.cursors[agent_id] = cur
        self.persist()
        return cur

    def get(self, agent_id):
        return self.cursors.get(agent_id)

    def remove(self, agent_id):
        if agent_id in self.cursors:
            del self.cursors[agent_id]
            self.persist()
            return True
        return False

    def update_position(self, agent_id, x, y, state="moving", action_text=""):
        cur = self.cursors.get(agent_id)
        if not cur:
            cur = self.spawn(agent_id, x=x, y=y)
        cur.move_to(x, y, state, action_text)
        self.persist()
        return cur

    def update_click(self, agent_id, click_type="left"):
        cur = self.cursors.get(agent_id)
        if cur:
            cur.trigger_click(click_type)
            self.persist()
            return cur
        return None

    def list_all(self):
        return [c.to_dict() for c in self.cursors.values()]

    def persist(self):
        payload = {
            "timestamp": time.time(),
            "count": len(self.cursors),
            "cursors": self.list_all()
        }
        try:
            tmp_path = f"{SHARED_MEM_PATH}.tmp"
            with open(tmp_path, "w") as f:
                json.dump(payload, f)
            os.replace(tmp_path, SHARED_MEM_PATH)
        except Exception:
            pass
