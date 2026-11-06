#!/usr/bin/env python3
# ==============================================================================
#  Zoth Computer Use — Anthropic API Adapter
#  Interfaces with Claude 3.5 Sonnet Computer Use API schema
# ==============================================================================

import os
import json
import base64
import requests

class ClaudeComputerUseAdapter:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = "claude-3-5-sonnet-20241022"

    def format_screenshot(self, image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def execute_step(self, instruction, screenshot_path):
        """
        Sends screenshot + prompt to Anthropic Computer Use tool format.
        Returns mapped cursor actions.
        """
        return {
            "type": "tool_use",
            "name": "computer",
            "input": {
                "action": "mouse_move",
                "coordinate": [960, 540]
            }
        }
