"""
Unit tests for Benchmarking and SlideDeck (Week 9 & 10).
"""

import unittest
import time
import numpy as np

from src.processing.benchmarking import PipelineLatencyTracker, BenchmarkSuite
from src.presentation.slides import SlideDeck


class TestBenchmarkingAndSlides(unittest.TestCase):
    """Test suite for performance profiler and built-in slide deck renderer."""

    def test_pipeline_latency_tracker(self):
        """Test stage latency measurements and rolling statistics."""
        tracker = PipelineLatencyTracker(history_size=10)

        # Record 5 simulated frames
        for _ in range(5):
            tracker.start_frame()
            time.sleep(0.002)
            tracker.mark_stage("detection")
            time.sleep(0.001)
            tracker.mark_stage("gesture")
            time.sleep(0.001)
            tracker.mark_stage("render")
            total = tracker.end_frame()
            self.assertGreater(total, 0.0)

        summary = tracker.get_summary()
        self.assertEqual(summary["sample_count"], 5)
        self.assertGreater(summary["mean_ms"], 0.0)
        self.assertGreater(summary["fps"], 0.0)

    def test_benchmark_suite_runner(self):
        """Test running a mini synthetic benchmark pass."""
        results = BenchmarkSuite.run_benchmark(iterations=5, frame_shape=(240, 320, 3))
        self.assertEqual(results["iterations"], 5)
        self.assertIn("latency", results)
        self.assertIn("total_mean_ms", results["latency"])
        self.assertGreater(results["effective_throughput_fps"], 0.0)

        report = BenchmarkSuite.format_report(results)
        self.assertIn("BENCHMARK REPORT", report)
        self.assertIn("Throughput", report)

    def test_slide_deck_renderer(self):
        """Test slide deck generation and frame shape."""
        count = SlideDeck.get_slide_count()
        self.assertGreaterEqual(count, 5)

        for i in range(1, count + 1):
            slide_frame = SlideDeck.render_slide(i, width=640, height=360)
            self.assertEqual(slide_frame.shape, (360, 640, 3))
            self.assertEqual(slide_frame.dtype, np.uint8)


if __name__ == "__main__":
    unittest.main()
