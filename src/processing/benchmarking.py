"""
Performance Profiling, Benchmarking, and Latency Optimization Engine.
Tracks per-stage pipeline latencies (Capture, MediaPipe Hand Inference, Gesture Classification,
Presentation Automation, Rendering), computes percentile statistics, and runs stress tests.
"""

import time
import statistics
import tracemalloc
from collections import deque
from typing import Dict, List, Optional, Tuple, Any
import cv2
import numpy as np


class PipelineLatencyTracker:
    """
    Lightweight, low-overhead rolling profiler for measuring pipeline latency stages.
    """

    def __init__(self, history_size: int = 120):
        self.history_size = history_size
        self._latencies_total: deque = deque(maxlen=history_size)
        self._latencies_detection: deque = deque(maxlen=history_size)
        self._latencies_gesture: deque = deque(maxlen=history_size)
        self._latencies_render: deque = deque(maxlen=history_size)

        self._current_frame_start = 0.0
        self._stage_timestamps: Dict[str, float] = {}

    def start_frame(self) -> None:
        """Record timestamp at start of frame processing cycle."""
        self._current_frame_start = time.perf_counter()
        self._stage_timestamps.clear()

    def mark_stage(self, stage_name: str) -> None:
        """Record completion timestamp for a pipeline stage."""
        self._stage_timestamps[stage_name] = time.perf_counter()

    def end_frame(self) -> float:
        """
        Record end of frame, calculate delta durations, and append to rolling queues.
        :return: Total frame latency in milliseconds.
        """
        now = time.perf_counter()
        total_ms = (now - self._current_frame_start) * 1000.0
        self._latencies_total.append(total_ms)

        # Stage specific deltas if markers present
        if "detection" in self._stage_timestamps:
            det_ms = (self._stage_timestamps["detection"] - self._current_frame_start) * 1000.0
            self._latencies_detection.append(det_ms)

        if "gesture" in self._stage_timestamps and "detection" in self._stage_timestamps:
            gest_ms = (self._stage_timestamps["gesture"] - self._stage_timestamps["detection"]) * 1000.0
            self._latencies_gesture.append(gest_ms)

        if "render" in self._stage_timestamps and "gesture" in self._stage_timestamps:
            rnd_ms = (self._stage_timestamps["render"] - self._stage_timestamps["gesture"]) * 1000.0
            self._latencies_render.append(rnd_ms)

        return total_ms

    def get_summary(self) -> Dict[str, float]:
        """
        Compute mean, P95, min, max, and FPS from rolling history.
        """
        if not self._latencies_total:
            return {
                "mean_ms": 0.0,
                "median_ms": 0.0,
                "p95_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "fps": 0.0,
                "sample_count": 0,
            }

        data = list(self._latencies_total)
        data_sorted = sorted(data)
        n = len(data_sorted)

        mean_val = statistics.mean(data)
        median_val = statistics.median(data)
        p95_idx = int(0.95 * n)
        p95_val = data_sorted[min(p95_idx, n - 1)]
        min_val = min(data)
        max_val = max(data)
        fps = 1000.0 / mean_val if mean_val > 0 else 0.0

        return {
            "mean_ms": round(mean_val, 2),
            "median_ms": round(median_val, 2),
            "p95_ms": round(p95_val, 2),
            "min_ms": round(min_val, 2),
            "max_ms": round(max_val, 2),
            "fps": round(fps, 1),
            "sample_count": n,
        }


class BenchmarkSuite:
    """
    Executes automated stress and latency tests across pipeline modules.
    """

    @staticmethod
    def run_benchmark(
        iterations: int = 60,
        frame_shape: Tuple[int, int, int] = (720, 1280, 3),
    ) -> Dict[str, Any]:
        """
        Execute end-to-end synthetic benchmark testing detector and gesture engine.

        :param iterations: Number of sample test iterations.
        :param frame_shape: Dimensions of benchmark test frames.
        :return: Detailed benchmark results dictionary.
        """
        from src.processing.hand_detector import HandDetector
        from src.processing.gesture_recognizer import GestureRecognizer, GestureType
        from src.presentation.controller import PresentationController, ControllerMode
        from src.presentation.laser_pointer import LaserPointer
        from src.presentation.annotator import SlideAnnotator

        # Start memory tracking
        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]

        detector = HandDetector(max_num_hands=1)
        recognizer = GestureRecognizer(smoothing_window=3)
        controller = PresentationController(mode=ControllerMode.SIMULATION)
        laser = LaserPointer()
        annotator = SlideAnnotator()

        latencies_det = []
        latencies_gest = []
        latencies_laser = []
        latencies_total = []

        # Synthetic test image
        dummy_frame = np.zeros(frame_shape, dtype=np.uint8)
        # Draw synthetic hand-like shapes to exercise vision pre-processing
        cv2.circle(dummy_frame, (640, 360), 80, (180, 180, 180), -1)

        t_bench_start = time.perf_counter()

        for _ in range(iterations):
            t0 = time.perf_counter()

            # 1. Hand Detector pass
            _, detected_hands = detector.find_hands(dummy_frame.copy(), draw=False)
            t1 = time.perf_counter()

            # 2. Gesture Recognizer pass (exercise heuristics)
            mock_hand = {
                "label": "Right",
                "confidence": 0.95,
                "landmarks": [(640, 360 + i * 10, 0.0) for i in range(21)],
                "bbox": (550, 250, 750, 500),
            }
            # Adjust index tip to simulate Point Right
            mock_hand["landmarks"][8] = (850, 360, 0.0)
            mock_hand["landmarks"][4] = (580, 420, 0.0)

            gesture_state = recognizer.recognize(mock_hand, use_smoothing=True)
            controller.handle_gesture(gesture_state)
            t2 = time.perf_counter()

            # 3. Laser Pointer and Annotator pass
            laser.update_position(640, 360, frame_shape[1], frame_shape[0])
            laser.render_overlay(dummy_frame.copy())
            annotator.start_drawing(640, 360)
            annotator.continue_drawing(645, 365)
            annotator.render(dummy_frame.copy())
            t3 = time.perf_counter()

            latencies_det.append((t1 - t0) * 1000.0)
            latencies_gest.append((t2 - t1) * 1000.0)
            latencies_laser.append((t3 - t2) * 1000.0)
            latencies_total.append((t3 - t0) * 1000.0)

        t_bench_end = time.perf_counter()
        total_bench_duration = t_bench_end - t_bench_start

        peak_memory = tracemalloc.get_traced_memory()[1] - start_memory
        tracemalloc.stop()

        detector.close()

        results = {
            "iterations": iterations,
            "resolution": f"{frame_shape[1]}x{frame_shape[0]}",
            "total_duration_sec": round(total_bench_duration, 3),
            "effective_throughput_fps": round(iterations / total_bench_duration, 1),
            "peak_memory_mb": round(peak_memory / (1024 * 1024), 2),
            "latency": {
                "total_mean_ms": round(statistics.mean(latencies_total), 2),
                "total_p95_ms": round(sorted(latencies_total)[int(0.95 * len(latencies_total))], 2),
                "total_min_ms": round(min(latencies_total), 2),
                "total_max_ms": round(max(latencies_total), 2),
                "detector_mean_ms": round(statistics.mean(latencies_det), 2),
                "gesture_mean_ms": round(statistics.mean(latencies_gest), 2),
                "laser_draw_mean_ms": round(statistics.mean(latencies_laser), 2),
            },
        }

        return results

    @staticmethod
    def format_report(results: Dict[str, Any]) -> str:
        """Format benchmark dictionary into a readable report."""
        lat = results["latency"]
        lines = [
            "============================================================",
            "  GESTURE-BASED PRESENTATION CONTROL - BENCHMARK REPORT",
            "============================================================",
            f"  Resolution Tested:         {results['resolution']}",
            f"  Total Iterations:          {results['iterations']} frames",
            f"  Benchmark Elapsed Time:    {results['total_duration_sec']} s",
            f"  Effective Throughput:      {results['effective_throughput_fps']} FPS",
            f"  Peak Memory Allocation:    {results['peak_memory_mb']} MB",
            "------------------------------------------------------------",
            "  Latency Profiling Breakdown:",
            f"    - Detection & Inference: {lat['detector_mean_ms']} ms",
            f"    - Gesture Classification: {lat['gesture_mean_ms']} ms",
            f"    - Laser & Draw Rendering: {lat['laser_draw_mean_ms']} ms",
            "------------------------------------------------------------",
            f"  Overall End-to-End Latency:",
            f"    - Mean:                  {lat['total_mean_ms']} ms",
            f"    - 95th Percentile (P95): {lat['total_p95_ms']} ms",
            f"    - Min / Max:             {lat['total_min_ms']} ms / {lat['total_max_ms']} ms",
            "============================================================",
        ]
        return "\n".join(lines)


if __name__ == "__main__":
    print("Running automated system benchmark (Week 9)...")
    res = BenchmarkSuite.run_benchmark(iterations=30)
    print(BenchmarkSuite.format_report(res))
