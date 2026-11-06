#!/usr/bin/env python3
# ==============================================================================
#  Zoth Computer Use — Low-Level Input Injection Engine
#  Provides reliable human-like input dispatch across Wayland (ydotool) and X11 (xdotool)
# ==============================================================================

import shutil
import subprocess
import time
import os

class InputEngine:
    def __init__(self):
        self.ydotool_bin = shutil.which("ydotool")
        self.xdotool_bin = shutil.which("xdotool")
        self.has_uinput = os.access("/dev/uinput", os.W_OK)

    def mouse_move(self, x, y):
        # Prefer ydotool under Wayland, fallback to xdotool
        if self.ydotool_bin:
            try:
                subprocess.run([self.ydotool_bin, "mousemove", "-a", str(int(x)), str(int(y))], timeout=1, capture_output=True)
                return True
            except Exception:
                pass
        if self.xdotool_bin:
            try:
                subprocess.run([self.xdotool_bin, "mousemove", str(int(x)), str(int(y))], timeout=1, capture_output=True)
                return True
            except Exception:
                pass
        return False

    def mouse_click(self, button="left", double=False):
        btn_map_ydo = {"left": "0x110", "right": "0x111", "middle": "0x112"}
        btn_map_xdo = {"left": "1", "right": "3", "middle": "2"}
        
        click_count = 2 if double else 1

        for _ in range(click_count):
            if self.ydotool_bin:
                code = btn_map_ydo.get(button, "0x110")
                try:
                    subprocess.run([self.ydotool_bin, "click", code], timeout=1, capture_output=True)
                    time.sleep(0.05)
                    continue
                except Exception:
                    pass
            if self.xdotool_bin:
                code = btn_map_xdo.get(button, "1")
                try:
                    subprocess.run([self.xdotool_bin, "click", code], timeout=1, capture_output=True)
                    time.sleep(0.05)
                except Exception:
                    pass
        return True

    def mouse_down(self, button="left"):
        if self.xdotool_bin:
            code = "1" if button == "left" else "3" if button == "right" else "2"
            try:
                subprocess.run([self.xdotool_bin, "mousedown", code], timeout=1, capture_output=True)
                return True
            except Exception:
                pass
        return False

    def mouse_up(self, button="left"):
        if self.xdotool_bin:
            code = "1" if button == "left" else "3" if button == "right" else "2"
            try:
                subprocess.run([self.xdotool_bin, "mouseup", code], timeout=1, capture_output=True)
                return True
            except Exception:
                pass
        return False

    def type_text(self, text):
        if self.ydotool_bin:
            try:
                subprocess.run([self.ydotool_bin, "type", "--", text], timeout=3, capture_output=True)
                return True
            except Exception:
                pass
        if self.xdotool_bin:
            try:
                subprocess.run([self.xdotool_bin, "type", "--", text], timeout=3, capture_output=True)
                return True
            except Exception:
                pass
        return False

    def key_press(self, key):
        if self.xdotool_bin:
            try:
                subprocess.run([self.xdotool_bin, "key", key], timeout=1, capture_output=True)
                return True
            except Exception:
                pass
        if self.ydotool_bin:
            try:
                subprocess.run([self.ydotool_bin, "key", key], timeout=1, capture_output=True)
                return True
            except Exception:
                pass
        return False

    def capture_screenshot(self, output_path="/tmp/zoth_screen.png"):
        # Wayland spectacle or grim
        grim_bin = shutil.which("grim")
        if grim_bin:
            try:
                subprocess.run([grim_bin, output_path], timeout=2, capture_output=True)
                if os.path.exists(output_path):
                    return output_path
            except Exception:
                pass
        spectacle_bin = shutil.which("spectacle")
        if spectacle_bin:
            try:
                subprocess.run([spectacle_bin, "-b", "-n", "-o", output_path], timeout=3, capture_output=True)
                if os.path.exists(output_path):
                    return output_path
            except Exception:
                pass
        return None
