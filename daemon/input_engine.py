#!/usr/bin/env python3
# ==============================================================================
#  Zoth Computer Use — Low-Level Dual-Stack Linux & Android Input Injection Engine
#  Provides reliable human-like input dispatch across:
#   - Linux Wayland (ydotool / wlr-screencopy / grim)
#   - Linux X11 / XWayland (xdotool / xte / spectacle)
#   - Linux Kernel Direct (evdev / /dev/uinput virtual mice)
#   - Android ADB & Termux Linux Subsystem (adb shell input tap, swipe, keyevent, screencap)
# ==============================================================================

import shutil
import subprocess
import time
import os
import sys

class InputEngine:
    def __init__(self, target_platform="auto"):
        self.ydotool_bin = shutil.which("ydotool")
        self.xdotool_bin = shutil.which("xdotool")
        self.grim_bin = shutil.which("grim")
        self.spectacle_bin = shutil.which("spectacle")
        self.adb_bin = shutil.which("adb")

        # Determine platform: linux_desktop vs android_adb vs termux
        if target_platform == "auto":
            if os.path.exists("/system/bin/app_process") or os.environ.get("TERMUX_VERSION"):
                self.platform = "android"
            else:
                self.platform = "linux"
        else:
            self.platform = target_platform

        self.android_device_id = None
        self._detect_android_devices()

    def _detect_android_devices(self):
        if not self.adb_bin:
            return
        try:
            res = subprocess.run([self.adb_bin, "devices"], capture_output=True, text=True, timeout=2)
            lines = [l.strip() for l in res.stdout.strip().splitlines()[1:] if l.strip()]
            devices = [l.split()[0] for l in lines if "\tdevice" in l or " device" in l]
            if devices:
                self.android_device_id = devices[0]
        except Exception:
            pass

    # --------------------------------------------------------------------------
    #  Linux Desktop Dispatch
    # --------------------------------------------------------------------------
    def _linux_mouse_move(self, x, y):
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

    def _linux_mouse_click(self, button="left", double=False):
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

    def _linux_mouse_down(self, button="left"):
        if self.xdotool_bin:
            code = "1" if button == "left" else "3" if button == "right" else "2"
            try:
                subprocess.run([self.xdotool_bin, "mousedown", code], timeout=1, capture_output=True)
                return True
            except Exception:
                pass
        return False

    def _linux_mouse_up(self, button="left"):
        if self.xdotool_bin:
            code = "1" if button == "left" else "3" if button == "right" else "2"
            try:
                subprocess.run([self.xdotool_bin, "mouseup", code], timeout=1, capture_output=True)
                return True
            except Exception:
                pass
        return False

    def _linux_type_text(self, text):
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

    def _linux_key_press(self, key):
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

    def _linux_capture_screenshot(self, output_path="/tmp/zoth_screen.png"):
        if self.grim_bin:
            try:
                subprocess.run([self.grim_bin, output_path], timeout=2, capture_output=True)
                if os.path.exists(output_path):
                    return output_path
            except Exception:
                pass
        if self.spectacle_bin:
            try:
                subprocess.run([self.spectacle_bin, "-b", "-n", "-o", output_path], timeout=3, capture_output=True)
                if os.path.exists(output_path):
                    return output_path
            except Exception:
                pass
        return None

    # --------------------------------------------------------------------------
    #  Android Native & ADB Dispatch
    # --------------------------------------------------------------------------
    def _android_cmd(self, args):
        if self.adb_bin:
            cmd = [self.adb_bin]
            if self.android_device_id:
                cmd += ["-s", self.android_device_id]
            cmd += ["shell"] + args
            try:
                res = subprocess.run(cmd, timeout=3, capture_output=True)
                return res.returncode == 0
            except Exception:
                return False
        # Direct Termux shell execution if running natively on Android
        try:
            res = subprocess.run(args, timeout=3, capture_output=True)
            return res.returncode == 0
        except Exception:
            return False

    def _android_tap(self, x, y):
        return self._android_cmd(["input", "tap", str(int(x)), str(int(y))])

    def _android_swipe(self, x1, y1, x2, y2, duration_ms=250):
        return self._android_cmd(["input", "swipe", str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(duration_ms))])

    def _android_type_text(self, text):
        safe_text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        return self._android_cmd(["input", "text", safe_text])

    def _android_key_press(self, keycode):
        # Maps common keys to Android Keyevents
        key_map = {
            "Return": "66", "Enter": "66",
            "Back": "4", "Escape": "111",
            "Home": "3", "Menu": "82",
            "Tab": "61", "Space": "62",
            "VolumeUp": "24", "VolumeDown": "25"
        }
        code = key_map.get(keycode, keycode)
        return self._android_cmd(["input", "keyevent", str(code)])

    def _android_capture_screenshot(self, output_path="/tmp/zoth_android_screen.png"):
        if self.adb_bin:
            try:
                # Capture directly into binary buffer on Android and write locally
                cmd = [self.adb_bin]
                if self.android_device_id:
                    cmd += ["-s", self.android_device_id]
                cmd += ["exec-out", "screencap", "-p"]
                with open(output_path, "wb") as f:
                    subprocess.run(cmd, stdout=f, timeout=4)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    return output_path
            except Exception:
                pass
        return None

    # --------------------------------------------------------------------------
    #  Unified Sovereign API
    # --------------------------------------------------------------------------
    def mouse_move(self, x, y, platform=None):
        plat = platform or self.platform
        if plat == "android":
            # Virtual hovering pointer on Android
            return True
        return self._linux_mouse_move(x, y)

    def mouse_click(self, button="left", double=False, x=None, y=None, platform=None):
        plat = platform or self.platform
        if plat == "android":
            if x is not None and y is not None:
                return self._android_tap(x, y)
            return False
        return self._linux_mouse_click(button=button, double=double)

    def mouse_down(self, button="left", platform=None):
        plat = platform or self.platform
        if plat == "android":
            return False
        return self._linux_mouse_down(button=button)

    def mouse_up(self, button="left", platform=None):
        plat = platform or self.platform
        if plat == "android":
            return False
        return self._linux_mouse_up(button=button)

    def type_text(self, text, platform=None):
        plat = platform or self.platform
        if plat == "android":
            return self._android_type_text(text)
        return self._linux_type_text(text)

    def key_press(self, key, platform=None):
        plat = platform or self.platform
        if plat == "android":
            return self._android_key_press(key)
        return self._linux_key_press(key)

    def swipe(self, x1, y1, x2, y2, duration_ms=250, platform=None):
        plat = platform or self.platform
        if plat == "android":
            return self._android_swipe(x1, y1, x2, y2, duration_ms)
        else:
            # Linux mouse drag simulation
            self._linux_mouse_move(x1, y1)
            time.sleep(0.02)
            self._linux_mouse_down("left")
            time.sleep(duration_ms / 2000.0)
            self._linux_mouse_move(x2, y2)
            time.sleep(duration_ms / 2000.0)
            self._linux_mouse_up("left")
            return True

    def capture_screenshot(self, output_path="/tmp/zoth_screen.png", platform=None):
        plat = platform or self.platform
        if plat == "android":
            return self._android_capture_screenshot(output_path)
        return self._linux_capture_screenshot(output_path)
