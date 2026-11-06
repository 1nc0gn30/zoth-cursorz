#!/usr/bin/env python3
# ==============================================================================
#  Zoth Vision Analyzer — Multi-Platform CV2 + OCR Visual Landmark Matcher
#  Extracts visual context crops around click coordinates and performs pre-flight
#  page layout analysis with Structural Similarity (SSIM) and template matching.
#  Platforms: Linux Desktop (Wayland/X11) & Android (ADB screencap)
# ==============================================================================

import os
import cv2
import numpy as np
import subprocess
from PIL import Image

class VisionAnalyzer:
    def __init__(self, crop_radius=48):
        self.crop_radius = crop_radius

    def capture_fullscreen(self, output_path="/tmp/zoth_vision_snap.png", platform="linux"):
        """Captures full screen on Linux Wayland/X11 or Android."""
        if platform == "android":
            adb_bin = "/usr/bin/adb"
            if os.path.exists(adb_bin):
                try:
                    with open(output_path, "wb") as f:
                        subprocess.run([adb_bin, "exec-out", "screencap", "-p"], stdout=f, timeout=4)
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        return output_path
                except Exception:
                    pass

        # Linux Desktop Fallbacks
        grim_bin = "/usr/bin/grim"
        spectacle_bin = "/usr/bin/spectacle"

        if os.path.exists(grim_bin):
            try:
                res = subprocess.run([grim_bin, output_path], timeout=2, capture_output=True)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path
            except Exception:
                pass

        if os.path.exists(spectacle_bin):
            try:
                res = subprocess.run([spectacle_bin, "-b", "-n", "-o", output_path], timeout=3, capture_output=True)
                if res.returncode == 0 and os.path.exists(output_path):
                    return output_path
            except Exception:
                pass

        return None

    def extract_landmark_crop(self, image_path, x, y, save_crop_path=None):
        if not os.path.exists(image_path):
            return None

        img = cv2.imread(image_path)
        if img is None:
            return None

        h, w, _ = img.shape
        x, y = int(x), int(y)

        x1 = max(0, x - self.crop_radius)
        y1 = max(0, y - self.crop_radius)
        x2 = min(w, x + self.crop_radius)
        y2 = min(h, y + self.crop_radius)

        crop = img[y1:y2, x1:x2]

        # Extract OCR text if tesseract available
        ocr_text = ""
        try:
            crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            pil_crop = Image.fromarray(crop_rgb)
            tmp_ocr_crop = f"/tmp/zoth_ocr_crop_{os.getpid()}.png"
            pil_crop.save(tmp_ocr_crop)
            res = subprocess.run(["tesseract", tmp_ocr_crop, "stdout", "--psm", "6"],
                                 capture_output=True, text=True, timeout=2)
            ocr_text = res.stdout.strip()
            if os.path.exists(tmp_ocr_crop):
                os.remove(tmp_ocr_crop)
        except Exception:
            pass

        # Calculate edge density of landmark
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.mean(edges) / 255.0)

        # Average color
        avg_color = [int(c) for c in np.mean(crop, axis=(0, 1))]

        if save_crop_path:
            os.makedirs(os.path.dirname(os.path.abspath(save_crop_path)), exist_ok=True)
            cv2.imwrite(save_crop_path, crop)

        return {
            "rel_x": x,
            "rel_y": y,
            "box": [x1, y1, x2, y2],
            "ocr_text": ocr_text,
            "edge_density": round(edge_density, 3),
            "avg_color": avg_color,
            "crop_path": save_crop_path
        }

    def verify_landmark_match(self, current_screen_path, landmark_crop_path, expected_x, expected_y, search_margin=120):
        if not os.path.exists(current_screen_path) or not os.path.exists(landmark_crop_path):
            return {"match": False, "score": 0.0, "reason": "File missing"}

        screen = cv2.imread(current_screen_path)
        template = cv2.imread(landmark_crop_path)
        if screen is None or template is None:
            return {"match": False, "score": 0.0, "reason": "Image load error"}

        sh, sw, _ = screen.shape
        th, tw, _ = template.shape

        sx1 = max(0, expected_x - search_margin - tw // 2)
        sy1 = max(0, expected_y - search_margin - th // 2)
        sx2 = min(sw, expected_x + search_margin + tw // 2)
        sy2 = min(sh, expected_y + search_margin + th // 2)

        search_roi = screen[sy1:sy2, sx1:sx2]
        if search_roi.shape[0] < th or search_roi.shape[1] < tw:
            return {"match": False, "score": 0.0, "reason": "ROI smaller than template"}

        res = cv2.matchTemplate(search_roi, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        score = float(max_val)
        best_x = sx1 + max_loc[0] + tw // 2
        best_y = sy1 + max_loc[1] + th // 2

        drift = float(np.hypot(best_x - expected_x, best_y - expected_y))
        is_match = score >= 0.65

        return {
            "match": is_match,
            "score": round(score, 3),
            "found_x": best_x,
            "found_y": best_y,
            "drift_px": round(drift, 1),
            "threshold": 0.65
        }
