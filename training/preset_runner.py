#!/usr/bin/env python3
# ==============================================================================
#  Zoth Preset Runner & Pre-Analysis Verification Engine
#  Runs a recorded action preset with pre-flight layout analysis.
#  If an unexpected layout or drifted button is found, suspends execution and
#  prompts the operator via the Review UI to review what changed or abort safely.
# ==============================================================================

import os
import sys
import time
import json
import urllib.request
from training.vision_analyzer import VisionAnalyzer

PRESETS_DIR = os.path.expanduser("~/NullAITech/zoth-cursorz/training/presets")
DAEMON_URL = "http://127.0.0.1:9990"

class PresetRunner:
    def __init__(self, preset_name, agent_id="1nc0gn30", strict_layout_check=True):
        self.preset_name = preset_name
        self.agent_id = agent_id
        self.strict_layout_check = strict_layout_check
        self.preset_dir = os.path.join(PRESETS_DIR, preset_name)
        self.preset_file = os.path.join(self.preset_dir, "preset.json")
        self.vision = VisionAnalyzer()

        if not os.path.exists(self.preset_file):
            raise FileNotFoundError(f"Preset file not found: {self.preset_file}")

        with open(self.preset_file, "r") as f:
            self.data = json.load(f)

    def dispatch_api(self, endpoint, payload):
        try:
            req = urllib.request.Request(
                f"{DAEMON_URL}{endpoint}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def pre_analyze_step(self, event, current_screen_path):
        """
        Pre-analyzes screen before executing a click to ensure the intended
        button or input field actually exists at the expected coordinates.
        """
        landmark = event.get("landmark")
        if not landmark:
            return {"ok": True}

        crop_path = landmark.get("crop_path")
        if not crop_path or not os.path.exists(crop_path):
            return {"ok": True}

        expected_x = int(event.get("x", 960))
        expected_y = int(event.get("y", 540))

        match_result = self.vision.verify_landmark_match(
            current_screen_path=current_screen_path,
            landmark_crop_path=crop_path,
            expected_x=expected_x,
            expected_y=expected_y
        )

        return match_result

    def trigger_review_modal(self, discrepancy_info):
        """
        Launches review prompt for the operator when a layout change is detected.
        """
        diff_file = "/tmp/zoth_layout_discrepancy.json"
        with open(diff_file, "w") as f:
            json.dump(discrepancy_info, f, indent=2)

        # Notify via CLI and GUI
        sys.stderr.write("\n⚠️  [Zoth Pre-Analysis Alert] Layout Discrepancy Detected!\n")
        sys.stderr.write(f"   Target: Step #{discrepancy_info.get('step_id')} ({discrepancy_info.get('action')})\n")
        sys.stderr.write(f"   Match Score: {discrepancy_info.get('score')} (Threshold: {discrepancy_info.get('threshold')})\n")
        sys.stderr.write(f"   Drift: {discrepancy_info.get('drift_px')}px\n")
        sys.stderr.write("   Suspending action. Launching Review UI window...\n")

        # Open Electron review window if installed
        try:
            review_bin = os.path.expanduser("~/NullAITech/zoth-cursorz/review_ui/launch_review.sh")
            if os.path.exists(review_bin):
                os.system(f"{review_bin} &")
        except Exception:
            pass

    def run(self, speed_multiplier=1.0):
        events = self.data.get("events", [])
        sys.stdout.write(f"✦ [PresetRunner] Running preset '{self.preset_name}' with {len(events)} events (Agent: {self.agent_id})...\n")

        start_time = time.time()
        last_event_t = 0.0

        for i, ev in enumerate(events):
            event_t = ev.get("t", 0.0)
            delay = (event_t - last_event_t) / max(0.1, speed_multiplier)
            if delay > 0.005:
                time.sleep(min(delay, 2.5))
            last_event_t = event_t

            ev_type = ev.get("type")

            if ev_type == "move":
                x = ev.get("x")
                y = ev.get("y")
                self.dispatch_api("/api/action", {
                    "action": "move",
                    "x": x,
                    "y": y,
                    "agent_id": self.agent_id,
                    "text": "Preset playback"
                })

            elif ev_type == "click":
                step_id = ev.get("step_id", i)
                x = ev.get("x")
                y = ev.get("y")
                btn = ev.get("button", "left")

                # Pre-Analysis Check
                if self.strict_layout_check and ev.get("landmark"):
                    current_screen = "/tmp/zoth_runner_preflight.png"
                    self.vision.capture_fullscreen(current_screen)
                    check = self.pre_analyze_step(ev, current_screen)

                    if not check.get("match", True):
                        discrepancy_info = {
                            "preset_name": self.preset_name,
                            "step_id": step_id,
                            "action": f"click {btn}",
                            "expected_coords": [x, y],
                            "score": check.get("score", 0.0),
                            "threshold": check.get("threshold", 0.65),
                            "drift_px": check.get("drift_px", 0.0),
                            "reason": check.get("reason", "Visual landmark not found at expected location"),
                            "landmark_crop": ev.get("landmark", {}).get("crop_path"),
                            "current_screen": current_screen
                        }
                        self.trigger_review_modal(discrepancy_info)
                        return False

                    # If small drift within threshold, snap to detected coordinate
                    if check.get("drift_px", 0) > 4 and check.get("drift_px", 0) < 60:
                        x = check["found_x"]
                        y = check["found_y"]
                        sys.stdout.write(f"  [Auto-Align] Snapped click to detected element at ({x}, {y})\n")

                self.dispatch_api("/api/action", {
                    "action": "click",
                    "x": x,
                    "y": y,
                    "button": btn,
                    "agent_id": self.agent_id
                })
                sys.stdout.write(f"  [Step #{step_id}] Executed click {btn} at ({x}, {y})\n")

            elif ev_type == "type":
                text = ev.get("text", "")
                self.dispatch_api("/api/action", {
                    "action": "type",
                    "text": text,
                    "agent_id": self.agent_id
                })
                sys.stdout.write(f"  [Step #{ev.get('step_id')}] Typed: '{text}'\n")

            elif ev_type == "key":
                key = ev.get("key", "")
                self.dispatch_api("/api/action", {
                    "action": "key",
                    "key": key,
                    "agent_id": self.agent_id
                })
                sys.stdout.write(f"  [Step #{ev.get('step_id')}] Key: '{key}'\n")

        sys.stdout.write(f"✦ [PresetRunner] Completed preset playback in {round(time.time() - start_time, 2)}s.\n")
        return True
