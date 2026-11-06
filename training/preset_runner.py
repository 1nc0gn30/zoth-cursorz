#!/usr/bin/env python3
# ==============================================================================
#  Zoth Preset Runner — Pre-Flight Layout Inspector & Multi-Agent Replayer
#  Loads recorded workflow presets, executes pre-flight vision checks at each step,
#  auto-aligns minor layout shifts, or triggers the Side-by-Side Review UI when
#  discrepancies are discovered to prevent erroneous actions.
#  Dual-stack Linux Desktop & Android ADB execution.
# ==============================================================================

import os
import sys
import time
import json
import subprocess
from vision_analyzer import VisionAnalyzer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from daemon.input_engine import InputEngine

class PresetRunner:
    def __init__(self, preset_path, input_engine=None, auto_align_threshold_px=60, platform="auto"):
        self.preset_path = preset_path
        self.input_engine = input_engine or InputEngine(target_platform=platform)
        self.vision = VisionAnalyzer()
        self.auto_align_threshold_px = auto_align_threshold_px
        self.platform = platform

        with open(os.path.join(preset_path, "preset.json"), "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def run(self, safe_mode=True):
        print(f"✦ [PresetRunner] Executing workflow: {self.metadata.get('preset_name')}")
        steps = self.metadata.get("steps", [])

        for s in steps:
            step_num = s.get("step")
            action_type = s.get("type")
            intent = s.get("intent", "")
            landmark = s.get("landmark")

            print(f"\n--- [Step {step_num}] {action_type.upper()}: {intent} ---")

            target_x = s.get("x")
            target_y = s.get("y")

            # 1. Pre-Flight Visual Landmark Inspection (if landmark exists)
            if safe_mode and landmark and landmark.get("crop_path"):
                crop_path = os.path.join(self.preset_path, "landmarks", os.path.basename(landmark.get("crop_path")))
                
                # Capture current live screen
                screen_tmp = f"/tmp/zoth_preflight_{step_num}_{os.getpid()}.png"
                captured = self.vision.capture_fullscreen(screen_tmp, platform=self.platform)

                if captured and os.path.exists(crop_path):
                    match_result = self.vision.verify_landmark_match(
                        current_screen_path=captured,
                        landmark_crop_path=crop_path,
                        expected_x=target_x,
                        expected_y=target_y
                    )

                    print(f"  [Pre-Flight Check] Match Score: {match_result.get('score')} | Drift: {match_result.get('drift_px')}px")

                    if not match_result.get("match"):
                        print(f"  ⚠ [DISCREPANCY DETECTED] Page layout changed or element missing!")
                        self._trigger_review_ui(
                            step_data=s,
                            expected_crop=crop_path,
                            current_screen=captured,
                            match_info=match_result
                        )
                        return False

                    # If minor drift detected, auto-align coordinates!
                    drift = match_result.get("drift_px", 0)
                    if 0 < drift <= self.auto_align_threshold_px:
                        print(f"  ⚡ [Auto-Aligned] Correcting drift from ({target_x}, {target_y}) -> ({match_result['found_x']}, {match_result['found_y']})")
                        target_x = match_result["found_x"]
                        target_y = match_result["found_y"]

                if os.path.exists(screen_tmp):
                    try: os.remove(screen_tmp)
                    except Exception: pass

            # 2. Execute Action via Low-Level Injection
            if action_type == "click":
                self.input_engine.mouse_move(target_x, target_y, platform=self.platform)
                time.sleep(0.04)
                self.input_engine.mouse_click(button=s.get("button", "left"), double=s.get("double", False), x=target_x, y=target_y, platform=self.platform)

            elif action_type == "swipe":
                self.input_engine.swipe(s.get("x1"), s.get("y1"), s.get("x2"), s.get("y2"), s.get("duration_ms", 250), platform=self.platform)

            elif action_type == "type":
                self.input_engine.type_text(s.get("text", ""), platform=self.platform)

            elif action_type == "key":
                self.input_engine.key_press(s.get("key", ""), platform=self.platform)

            time.sleep(0.2)

        print("\n✔ [PresetRunner] Workflow preset completed successfully!")
        return True

    def _trigger_review_ui(self, step_data, expected_crop, current_screen, match_info):
        """Dispatches Electron Side-by-Side Review UI."""
        payload = {
            "step": step_data.get("step"),
            "intent": step_data.get("intent"),
            "expected_x": step_data.get("x"),
            "expected_y": step_data.get("y"),
            "expected_crop": expected_crop,
            "current_screen": current_screen,
            "score": match_info.get("score"),
            "reason": match_info.get("reason", "Structural mismatch under threshold")
        }

        payload_path = "/tmp/zoth_review_discrepancy.json"
        with open(payload_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        review_launcher = "/home/zoth/NullAITech/zoth-cursorz/review_ui/launch_review.sh"
        if os.path.exists(review_launcher):
            subprocess.run(["bash", review_launcher, payload_path])
