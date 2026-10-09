"""Unit tests for Sequencer HTTP server and API endpoints."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from wled_sequencer.models import SequenceData, SequenceRepository, SequenceStep
from wled_sequencer.server import SequencerAppServer


class TestSequencerServer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.sequences_dir = self.temp_dir / "sequences"
        self.sequences_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir = Path(__file__).resolve().parent.parent / "src" / "wled_sequencer" / "static"

        self.app = SequencerAppServer(
            host="127.0.0.1",
            port=0,
            sequences_dir=self.sequences_dir,
            static_dir=self.static_dir,
        )

    def tearDown(self) -> None:
        if self.app.is_running:
            self.app.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_app_lifecycle(self) -> None:
        self.assertFalse(self.app.is_running)
        self.app.start()
        self.assertTrue(self.app.is_running)
        self.assertGreater(self.app.port, 0)
        self.app.stop()
        self.assertFalse(self.app.is_running)

    def test_static_files_exist(self) -> None:
        index_html = self.static_dir / "index.html"
        self.assertTrue(index_html.is_file())

        css_files = ["win95_base.css", "win95_controls.css", "sequencer.css"]
        for f in css_files:
            self.assertTrue((self.static_dir / "css" / f).is_file())

        js_files = [
            "app.js", "state.js", "player.js", "engine_client.js",
            "ui_steps.js", "ui_inspector.js", "ui_transport.js",
            "ui_global.js", "ui_dialogs.js"
        ]
        for f in js_files:
            self.assertTrue((self.static_dir / "js" / f).is_file())

    def test_load_demo_sequences(self) -> None:
        proj_root = Path(__file__).resolve().parent.parent
        sequences_dir = proj_root / "sequences"
        repo = SequenceRepository(sequences_dir)
        summaries = repo.list_sequences()
        self.assertGreaterEqual(len(summaries), 3)

        filenames = [s["filename"] for s in summaries]
        self.assertIn("garage_light_show.json", filenames)
        self.assertIn("cyberpunk_rave.json", filenames)
        self.assertIn("campfire_ambience.json", filenames)

        # Verify garage sequence has sections and overlapping concurrent layers
        garage = repo.load_sequence("garage_light_show.json")
        self.assertIsNotNone(garage)
        self.assertGreater(garage.total_duration, 0)
        sections = {s.section for s in garage.steps}
        self.assertIn("Intro", sections)
        self.assertIn("Main Drive", sections)
        self.assertIn("Outro", sections)

        # Check overlapping cues: Step 1 (0..16) and Step 2 (2..8) overlap
        s1 = garage.steps[0]
        s2 = garage.steps[1]
        self.assertEqual(s1.start_time_sec, 0.0)
        self.assertEqual(s1.duration_sec, 16.0)
        self.assertEqual(s1.stop_time_sec, 16.0)
        self.assertEqual(s2.start_time_sec, 2.0)
        self.assertEqual(s2.stop_time_sec, 8.0)
        self.assertNotEqual(s1.target_layer, s2.target_layer)
        # Verify temporal concurrency
        self.assertTrue(s2.start_time_sec < s1.stop_time_sec)


if __name__ == "__main__":
    unittest.main()
