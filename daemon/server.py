#!/usr/bin/env python3
# ==============================================================================
#  Zoth Cursorz & Computer Use Daemon Server (Port :9990)
#  Fast, zero-dependency HTTP & WebSocket server for multi-agent cursor coordination
# ==============================================================================

import json
import os
import sys
import time
import http.server
import threading
from urllib.parse import urlparse, parse_qs

# Ensure daemon package path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from daemon.config import DAEMON_HOST, DAEMON_PORT, SHARED_MEM_PATH
from daemon.cursor_manager import CursorManager
from daemon.input_engine import InputEngine

cursor_mgr = CursorManager()
input_eng = InputEngine()

# Seed default resident agents
cursor_mgr.spawn("1nc0gn30", name="1nc0gn30", color="#39d353", icon="reticle", x=1400, y=420)
cursor_mgr.spawn("zoth", name="Zoth", color="#f5b82e", icon="arrow", x=960, y=540)
cursor_mgr.spawn("sentinel", name="Sentinel", color="#ef4444", icon="target", x=520, y=360)

class CursorAPIHandler(http.server.BaseHTTPRequestHandler):
    def send_cors_json(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health" or path == "/api/health":
            self.send_cors_json(200, {
                "status": "online",
                "service": "zoth-cursorz-daemon",
                "cursors_active": len(cursor_mgr.cursors),
                "timestamp": time.time()
            })
            return

        if path == "/api/cursors":
            self.send_cors_json(200, {
                "count": len(cursor_mgr.cursors),
                "cursors": cursor_mgr.list_all()
            })
            return

        if path.startswith("/api/cursors/"):
            agent_id = path.split("/")[-1]
            cur = cursor_mgr.get(agent_id)
            if cur:
                self.send_cors_json(200, cur.to_dict())
            else:
                self.send_cors_json(404, {"error": "Cursor not found"})
            return

        if path == "/api/screenshot":
            shot = input_eng.capture_screenshot()
            if shot and os.path.exists(shot):
                self.send_cors_json(200, {"success": True, "path": shot})
            else:
                self.send_cors_json(500, {"error": "Failed to capture screenshot"})
            return

        self.send_cors_json(404, {"error": "Not Found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}

        # 1. Spawn a new virtual agent cursor
        if path == "/api/cursors/spawn":
            agent_id = data.get("agent_id") or f"agent_{int(time.time()*1000)%10000}"
            cur = cursor_mgr.spawn(
                agent_id=agent_id,
                name=data.get("name"),
                color=data.get("color"),
                icon=data.get("icon"),
                x=data.get("x", 960),
                y=data.get("y", 540)
            )
            self.send_cors_json(201, {"success": True, "cursor": cur.to_dict()})
            return

        # 2. Move virtual cursor
        if path == "/api/cursors/move":
            agent_id = data.get("agent_id", "zoth")
            x = data.get("x", 960)
            y = data.get("y", 540)
            state = data.get("state", "moving")
            action_text = data.get("action_text", "")
            cur = cursor_mgr.update_position(agent_id, x, y, state, action_text)
            
            # If physical execution requested
            if data.get("execute_hardware", False):
                input_eng.mouse_move(x, y)

            self.send_cors_json(200, {"success": True, "cursor": cur.to_dict()})
            return

        # 3. Click action
        if path == "/api/cursors/click":
            agent_id = data.get("agent_id", "zoth")
            click_type = data.get("click_type", "left")
            double = data.get("double", False)
            cur = cursor_mgr.update_click(agent_id, click_type)

            if data.get("execute_hardware", False):
                input_eng.mouse_click(button=click_type, double=double)

            self.send_cors_json(200, {"success": True, "cursor": cur.to_dict() if cur else None})
            return

        # 4. Computer-Use Action Dispatch (Human-Like Execution)
        if path == "/api/action":
            action = data.get("action", "")
            agent_id = data.get("agent_id", "1nc0gn30")

            if action == "move":
                x, y = data.get("x", 960), data.get("y", 540)
                cur = cursor_mgr.update_position(agent_id, x, y, state="moving", action_text=data.get("text", "Moving"))
                input_eng.mouse_move(x, y)
                self.send_cors_json(200, {"success": True, "cursor": cur.to_dict()})
                return

            elif action == "click":
                x, y = data.get("x"), data.get("y")
                btn = data.get("button", "left")
                dbl = data.get("double", False)
                if x is not None and y is not None:
                    cursor_mgr.update_position(agent_id, x, y, state="clicking", action_text=f"Click {btn}")
                    input_eng.mouse_move(x, y)
                    time.sleep(0.04)
                cursor_mgr.update_click(agent_id, btn)
                input_eng.mouse_click(button=btn, double=dbl)
                self.send_cors_json(200, {"success": True, "action": "click", "agent": agent_id})
                return

            elif action == "type":
                text = data.get("text", "")
                cursor_mgr.update_position(agent_id, cursor_mgr.get(agent_id).x if cursor_mgr.get(agent_id) else 960, 
                                           cursor_mgr.get(agent_id).y if cursor_mgr.get(agent_id) else 540,
                                           state="typing", action_text=f"Type: {text[:16]}")
                input_eng.type_text(text)
                self.send_cors_json(200, {"success": True, "action": "type", "typed": text})
                return

            elif action == "key":
                key = data.get("key", "")
                input_eng.key_press(key)
                self.send_cors_json(200, {"success": True, "action": "key", "key": key})
                return

            self.send_cors_json(400, {"error": f"Unknown action: {action}"})
            return

        self.send_cors_json(404, {"error": "Not Found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/cursors/"):
            agent_id = path.split("/")[-1]
            ok = cursor_mgr.remove(agent_id)
            if ok:
                self.send_cors_json(200, {"success": True, "removed": agent_id})
            else:
                self.send_cors_json(404, {"error": "Cursor not found"})
            return
        self.send_cors_json(404, {"error": "Not Found"})

    def log_message(self, format, *args):
        pass

def main():
    server = http.server.ThreadingHTTPServer((DAEMON_HOST, DAEMON_PORT), CursorAPIHandler)
    sys.stdout.write(f"✦ [zoth-cursorz-daemon] Sovereign Multi-Agent Cursor Server live on http://{DAEMON_HOST}:{DAEMON_PORT}\n")
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stdout.write("\nShutting down zoth-cursorz-daemon...\n")
        server.server_close()

if __name__ == "__main__":
    main()
