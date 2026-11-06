#!/usr/bin/env python3
# ==============================================================================
#  Zoth Computer Use — Anthropic API Adapter
#  Interfaces with Claude 3.5 Sonnet / Opus Computer Use API schema.
# ==============================================================================

import os
import json
import base64
import requests

class ClaudeComputerUseAdapter:
    def __init__(self, api_key=None, model="claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.endpoint = "https://api.anthropic.com/v1/messages"

    def format_screenshot(self, image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def execute_step(self, instruction, screenshot_path, screen_width=1920, screen_height=1080):
        """
        Sends screenshot + prompt to Anthropic Computer Use tool API format.
        Returns mapped cursor actions.
        """
        if not self.api_key:
            return {
                "action": "click",
                "x": 960,
                "y": 540,
                "thought": "No ANTHROPIC_API_KEY set; using default center anchor"
            }

        img_b64 = self.format_screenshot(screenshot_path)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "computer-use-2024-10-22",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "tools": [
                {
                    "type": "computer_20241022",
                    "name": "computer",
                    "display_width_px": screen_width,
                    "display_height_px": screen_height,
                    "display_number": 1
                }
            ],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": instruction
                        }
                    ]
                }
            ]
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for c in data.get("content", []):
                    if c.get("type") == "tool_use" and c.get("name") == "computer":
                        inp = c.get("input", {})
                        action = inp.get("action")
                        coords = inp.get("coordinate", [960, 540])
                        return {
                            "action": "click" if "click" in action else "type" if action == "type" else "move",
                            "x": coords[0],
                            "y": coords[1],
                            "text": inp.get("text", ""),
                            "thought": f"Claude tool call: {action}"
                        }
        except Exception as e:
            pass

        return {
            "action": "click",
            "x": 960,
            "y": 540,
            "thought": "Fallback center anchor"
        }
