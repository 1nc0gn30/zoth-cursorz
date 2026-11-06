#!/usr/bin/env python3
# ==============================================================================
#  Zoth Action Recorder — Human Workflow & Action Sequence Trainer
#  Records mouse trajectory, clicks, typing, pauses, and takes automatic landmark
#  crops of what was clicked to create robust, self-verifying automation presets.
# ==============================================================================

import os
import sys
import time
import json
import threading
from training.vision_analyzer import VisionAnalyzer

PRESETS_DIR = os.path.expanduser("~/NullAITech/zoth-cursorz/training/presets")
SHARED_CURSOR_PATH = "/dev/shm/zoth_cursor.json"

class ActionRecorder:
    def __init__(self, preset_name="default_preset"):
        self.preset_name = preset_name
        self.preset_dir = os.path.join(PRESETS_DIR, preset_name)
        self.crops_dir = os.path.join(self.preset_dir, "crops")
        os.makedirs(self.crops_dir, exist_ok=True)

        self.vision = VisionAnalyzer()
        self.recording = False
        self.events = []
        self.start_time = 0.0
        self.last_pos = (960, 540)
        self.step_counter = 0

    def get_live_cursor_pos(self):
        try:
            if os.path.exists(SHARED_CURSOR_PATH):
                with open(SHARED_CURSOR_PATH, "r") as f:
                    data = json.load(f)
                    return float(data.get("x", 960)), float(data.get("y", 540))
        except Exception:
            pass
        return self.last_pos

    def start(self):
        self.recording = True
        self.events = []
        self.start_time = time.time()
        self.step_counter = 0
        sys.stdout.write(f"✦ [Recorder] Started training preset '{self.preset_name}'...\n")

        # Capture initial screen state
        init_snap = os.path.join(self.preset_dir, "baseline_screen.png")
        self.vision.capture_fullscreen(init_snap)

        # Background thread to record mouse trajectory every 40ms
        self.poll_thread = threading.Thread(target=self._trajectory_loop, daemon=True)
        self.poll_thread.start()

    def _trajectory_loop(self):
        last_recorded_pos = None
        while self.recording:
            x, y = self.get_live_cursor_pos()
            self.last_pos = (x, y)
            if last_recorded_pos != (x, y):
                last_recorded_pos = (x, y)
                t_offset = time.time() - self.start_time
                self.events.append({
                    "type": "move",
                    "t": round(t_offset, 3),
                    "x": x,
                    "y": y
                })
            time.sleep(0.04)

    def record_click(self, button="left", double=False):
        if not self.recording:
            return
        t_offset = time.time() - self.start_time
        x, y = self.get_live_cursor_pos()
        self.step_counter += 1

        # Capture landmark of what was clicked
        snap_path = f"/tmp/zoth_click_{self.step_counter}.png"
        self.vision.capture_fullscreen(snap_path)

        crop_filename = f"step_{self.step_counter:03d}_{button}.png"
        crop_path = os.path.join(self.crops_dir, crop_filename)

        landmark = self.vision.extract_landmark_crop(snap_path, x, y, save_crop_path=crop_path)
        if os.path.exists(snap_path):
            os.remove(snap_path)

        event = {
            "type": "click",
            "step_id": self.step_counter,
            "t": round(t_offset, 3),
            "button": button,
            "double": double,
            "x": x,
            "y": y,
            "landmark": landmark
        }
        self.events.append(event)
        sys.stdout.write(f"  [Action] Recorded click {button} at ({x}, {y}) | Landmark OCR: '{landmark.get('ocr_text', '')[:24]}'\n")

    def record_type(self, text):
        if not self.recording:
            return
        t_offset = time.time() - self.start_time
        self.step_counter += 1
        event = {
            "type": "type",
            "step_id": self.step_counter,
            "t": round(t_offset, 3),
            "text": text
        }
        self.events.append(event)
        sys.stdout.write(f"  [Action] Recorded type '{text}'\n")

    def record_key(self, key):
        if not self.recording:
            return
        t_offset = time.time() - self.start_time
        self.step_counter += 1
        event = {
            "type": "key",
            "step_id": self.step_counter,
            "t": round(t_offset, 3),
            "key": key
        }
        self.events.append(event)
        sys.stdout.write(f"  [Action] Recorded key '{key}'\n")

    def stop(self):
        self.recording = False
        duration = time.time() - self.start_time

        preset_data = {
            "preset_name": self.preset_name,
            "created_at": time.time(),
            "duration_sec": round(duration, 2),
            "total_steps": self.step_counter,
            "events_count": len(self.events),
            "events": self.events
        }

        preset_file = os.path.join(self.preset_dir, "preset.json")
        with open(preset_file, "w") as f:
            json.dump(preset_data, f, indent=2)

        sys.stdout.write(f"✦ [Recorder] Saved preset '{self.preset_name}' with {len(self.events)} events to {preset_file}\n")
        return preset_file
