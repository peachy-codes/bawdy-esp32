"""Unit tests for Pattern Sequencer models and repository."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from wled_sequencer.models import SequenceData, SequenceRepository, SequenceStep


class TestSequencerModels(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo = SequenceRepository(self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_step_validation(self) -> None:
        step = SequenceStep(
            id="s1",
            name="Valid Step",
            section="Intro",
            target_layer=0,
            pattern_id="rainbow",
            start_time_sec=2.0,
            duration_sec=3.0,
            transition_sec=1.0,
            fade_out_sec=0.5,
        )
        self.assertEqual(step.target_layer, 0)
        self.assertEqual(step.section, "Intro")
        self.assertEqual(step.start_time_sec, 2.0)
        self.assertEqual(step.duration_sec, 3.0)
        self.assertEqual(step.stop_time_sec, 5.0)

        # Invalid layer index > 9
        with self.assertRaises(ValueError):
            SequenceStep(id="s2", target_layer=10)

        # Invalid layer index < 0
        with self.assertRaises(ValueError):
            SequenceStep(id="s3", target_layer=-1)

        # Negative start time
        with self.assertRaises(ValueError):
            SequenceStep(id="s4", start_time_sec=-1.0)

        # Negative duration
        with self.assertRaises(ValueError):
            SequenceStep(id="s5", duration_sec=-2.0)

    def test_legacy_dict_migration(self) -> None:
        raw_dict = {
            "name": "Legacy Show",
            "steps": [
                {"id": "s1", "name": "Step 1", "hold_duration_sec": 4.0},
                {"id": "s2", "name": "Step 2", "hold_duration_sec": 6.0},
            ]
        }
        seq = SequenceData.from_dict(raw_dict)
        self.assertEqual(len(seq.steps), 2)
        self.assertEqual(seq.steps[0].start_time_sec, 0.0)
        self.assertEqual(seq.steps[0].duration_sec, 4.0)
        self.assertEqual(seq.steps[0].stop_time_sec, 4.0)
        self.assertEqual(seq.steps[1].start_time_sec, 4.0)
        self.assertEqual(seq.steps[1].duration_sec, 6.0)
        self.assertEqual(seq.steps[1].stop_time_sec, 10.0)
        self.assertEqual(seq.total_duration, 10.0)

    def test_sequence_serialization_roundtrip(self) -> None:
        step1 = SequenceStep(id="s1", name="Wave", target_layer=0, pattern_id="wave", speed=1.5)
        step2 = SequenceStep(id="s2", name="Chase", target_layer=1, pattern_id="chase", blend_mode="ADDITIVE", channels=[2])

        seq = SequenceData(
            name="My Test Show",
            description="Testing serialization",
            author="Tester",
            loop_mode="count",
            loop_count=3,
            time_dilation=1.5,
            steps=[step1, step2],
        )

        d = seq.to_dict()
        restored = SequenceData.from_dict(d)

        self.assertEqual(restored.name, "My Test Show")
        self.assertEqual(restored.loop_mode, "count")
        self.assertEqual(restored.loop_count, 3)
        self.assertEqual(restored.time_dilation, 1.5)
        self.assertEqual(len(restored.steps), 2)
        self.assertEqual(restored.steps[0].pattern_id, "wave")
        self.assertEqual(restored.steps[1].blend_mode, "ADDITIVE")
        self.assertEqual(restored.steps[1].channels, [2])

    def test_repository_save_load_list_delete(self) -> None:
        seq = SequenceData(
            name="Garage Test",
            steps=[SequenceStep(id="s1", name="Step 1")],
        )

        fname = self.repo.save_sequence(seq)
        self.assertTrue(fname.endswith(".json"))

        # List
        listed = self.repo.list_sequences()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["name"], "Garage Test")
        self.assertEqual(listed[0]["step_count"], 1)

        # Load
        loaded = self.repo.load_sequence(fname)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Garage Test")

        # Delete
        self.assertTrue(self.repo.delete_sequence(fname))
        self.assertEqual(len(self.repo.list_sequences()), 0)


if __name__ == "__main__":
    unittest.main()
