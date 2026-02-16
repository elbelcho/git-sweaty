import json
import os
import re
import shutil
import subprocess
import unittest


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_JS_PATH = os.path.join(ROOT_DIR, "site", "app.js")


@unittest.skipUnless(shutil.which("node"), "node is required for JS unit tests")
class TooltipTouchZoomDismissTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open(APP_JS_PATH, "r", encoding="utf-8") as handle:
            app_js = handle.read()

        function_patterns = {
            "is_touch_viewport_zoomed": r"function isTouchViewportZoomed\(\)\s*{[\s\S]*?\n}\n",
            "get_scroll_dismiss_threshold": r"function getTouchViewportScrollDismissThresholdPx\(\)\s*{[\s\S]*?\n}\n",
            "should_preserve_passive_event": r"function shouldPreserveTouchTooltipOnPassiveViewportEvent\(cardScrollEvent, viewportMoved\)\s*{[\s\S]*?\n}\n",
        }
        extracted: dict[str, str] = {}
        for key, pattern in function_patterns.items():
            match = re.search(pattern, app_js)
            if not match:
                raise AssertionError(f"Could not find helper for {key} in site/app.js")
            extracted[key] = match.group(0)
        cls.sources = extracted

    def _run_js(self, payload: dict) -> object:
        script = (
            "const payload = JSON.parse(process.argv[1]);\n"
            "const window = {\n"
            "  visualViewport: payload.viewport_scale == null ? null : { scale: payload.viewport_scale },\n"
            "};\n"
            "const useTouchInteractions = Boolean(payload.use_touch_interactions);\n"
            "const TOUCH_TOOLTIP_TAP_MAX_SCROLL_PX = 2;\n"
            "const TOUCH_TOOLTIP_ZOOMED_VIEWPORT_SCALE_MIN = 1.05;\n"
            "const TOUCH_TOOLTIP_ZOOMED_VIEWPORT_DISMISS_MAX_SCROLL_PX = 12;\n"
            f"{self.sources['is_touch_viewport_zoomed']}\n"
            f"{self.sources['get_scroll_dismiss_threshold']}\n"
            f"{self.sources['should_preserve_passive_event']}\n"
            "const result = {\n"
            "  zoomed: isTouchViewportZoomed(),\n"
            "  threshold: getTouchViewportScrollDismissThresholdPx(),\n"
            "  preserve: shouldPreserveTouchTooltipOnPassiveViewportEvent(\n"
            "    Boolean(payload.card_scroll_event),\n"
            "    Boolean(payload.viewport_moved),\n"
            "  ),\n"
            "};\n"
            "process.stdout.write(JSON.stringify(result));\n"
        )
        completed = subprocess.run(
            ["node", "-e", script, json.dumps(payload)],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_non_zoomed_viewport_uses_default_dismiss_threshold(self) -> None:
        result = self._run_js(
            {
                "viewport_scale": 1.0,
                "use_touch_interactions": True,
                "card_scroll_event": False,
                "viewport_moved": False,
            }
        )
        self.assertFalse(result["zoomed"])
        self.assertEqual(result["threshold"], 2)
        self.assertFalse(result["preserve"])

    def test_zoomed_viewport_uses_relaxed_dismiss_threshold(self) -> None:
        result = self._run_js(
            {
                "viewport_scale": 2.4,
                "use_touch_interactions": True,
                "card_scroll_event": False,
                "viewport_moved": False,
            }
        )
        self.assertTrue(result["zoomed"])
        self.assertEqual(result["threshold"], 5)
        self.assertTrue(result["preserve"])

    def test_zoomed_threshold_is_capped(self) -> None:
        result = self._run_js(
            {
                "viewport_scale": 8.0,
                "use_touch_interactions": True,
                "card_scroll_event": False,
                "viewport_moved": False,
            }
        )
        self.assertEqual(result["threshold"], 12)

    def test_preserve_only_applies_to_passive_non_movement_events(self) -> None:
        moved = self._run_js(
            {
                "viewport_scale": 2.0,
                "use_touch_interactions": True,
                "card_scroll_event": False,
                "viewport_moved": True,
            }
        )
        self.assertFalse(moved["preserve"])

        card_scroll = self._run_js(
            {
                "viewport_scale": 2.0,
                "use_touch_interactions": True,
                "card_scroll_event": True,
                "viewport_moved": False,
            }
        )
        self.assertFalse(card_scroll["preserve"])

    def test_preserve_never_applies_without_touch_interactions(self) -> None:
        result = self._run_js(
            {
                "viewport_scale": 2.0,
                "use_touch_interactions": False,
                "card_scroll_event": False,
                "viewport_moved": False,
            }
        )
        self.assertFalse(result["preserve"])


if __name__ == "__main__":
    unittest.main()
