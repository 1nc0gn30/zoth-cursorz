#!/usr/bin/env python3
# ==============================================================================
#  Zoth Workflow Trainer — Action & Layout Sequence Recorder
#  Records user/agent interactions, timings, key strokes, and auto-generates
#  visual landmark micro-crops and OCR context tags for pre-flight replay safety.
#  Dual-stack support: Linux Desktop (spectacle/grim) & Android (ADB screencap)
# ==============================================================================

import os
import sys
import time
import json
from vision_analyzer import VisionAnalyzer

class ActionRecorder:
    def __init__(self, preset_name="default_preset", presets_dir="/home/zoth/NullAITech/zoth-cursorz/training/presets", platform="linux"):
        self.preset_name = preset_name
        self.presets_dir = presets_dir
        self.preset_path = os.path.join(presets_dir, preset_name)
        self.landmarks_dir = os.path.join(self.preset_path, "landmarks")
        self.platform = platform
        
        os.makedirs(self.landmarks_dir, exist_ok=True)
        self.vision = VisionAnalyzer(crop_radius=52)
        self.steps = []
        self.start_time = None

    def begin_session(self):
        self.start_time = time.time()
        self.steps = []
        return {
            "status": "recording",
            "preset": self.preset_name,
            "platform": self.platform,
            "start_time": self.start_time
        }

    def record_click(self, x, y, button="left", double=False, intent_note=""):
        step_idx = len(self.steps) + 1
        timestamp = time.time() - (self.start_time or time.time())
        
        # 1. Capture current screen state
        screen_tmp = f"/tmp/zoth_rec_snap_{step_idx}_{os.getpid()}.png"
        captured = self.vision.capture_fullscreen(screen_tmp, platform=self.platform)
        
        landmark_data = None
        if captured and os.path.exists(captured):
            crop_filename = f"step_{step_idx:03d}_{button}_landmark.png"
            crop_path = os.path.join(self.landmarks_dir, crop_filename)
            landmark_data = self.vision.extract_landmark_crop(captured, x, y, save_crop_path=crop_path)
            if os.path.exists(screen_tmp):
                try: os.remove(screen_tmp)
                except Exception: pass

        step_record = {
            "step": step_idx,
            "type": "click",
            "button": button,
            "double": double,
            "x": int(x),
            "y": int(y),
            "time_offset_s": round(timestamp, 3),
            "intent": intent_note or f"Click {button} on target element",
            "landmark": landmark_data
        }
        self.steps.append(step_record)
        return step_record

    def record_swipe(self, x1, y1, x2, y2, duration_ms=250, intent_note=""):
        step_idx = len(self.steps) + 1
        timestamp = time.time() - (self.start_time or time.time())

        step_record = {
            "step": step_idx,
            "type": "swipe",
            "x1": int(x1), "y1": int(y1),
            "x2": int(x2), "y2": int(y2),
            "duration_ms": duration_ms,
            "time_offset_s": round(timestamp, 3),
            "intent": intent_note or "Gesture swipe"
        }
        self.steps.append(step_record)
        return step_record

    def record_type(self, text, intent_note=""):
        step_idx = len(self.steps) + 1
        timestamp = time.time() - (self.start_time or time.time())

        step_record = {
            "step": step_idx,
            "type": "type",
            "text": text,
            "time_offset_s": round(timestamp, 3),
            "intent": intent_note or f"Type text buffer ({len(text)} chars)"
        }
        self.steps.append(step_record)
        return step_record

    def record_key(self, key_name, intent_note=""):
        step_idx = len(self.steps) + 1
        timestamp = time.time() - (self.start_time or time.time())

        step_record = {
            "step": step_idx,
            "type": "key",
            "key": key_name,
            "time_offset_s": round(timestamp, 3),
            "intent": intent_note or f"Press key: {key_name}"
        }
        self.steps.append(step_record)
        return step_record

    def finalize_preset(self, description="Automated recorded preset"):
        metadata = {
            "preset_name": self.preset_name,
            "created_at": time.time(),
            "description": description,
            "platform": self.platform,
            "total_steps": len(self.steps),
            "total_duration_s": round(time.time() - (self.start_time or time.time()), 2),
            "steps": self.steps
        }

        output_json = os.path.join(self.preset_path, "preset.json")
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return output_json
