import unittest

from autoclicker.controller import AutomationController


class AutomationControllerTests(unittest.TestCase):
    def test_emit_runtime_metrics_reports_average_frequency(self) -> None:
        controller = AutomationController()
        action_counts: list[int] = []
        actual_rates: list[float] = []
        controller.action_count_changed.connect(action_counts.append)
        controller.actual_frequency_changed.connect(actual_rates.append)

        controller._action_count = 12
        controller._run_started_at = 4.0

        controller._emit_runtime_metrics(now=5.0)

        self.assertEqual(action_counts[-1], 12)
        self.assertAlmostEqual(actual_rates[-1], 12.0)

    def test_force_zero_runtime_metrics_preserves_count_and_clears_rate(self) -> None:
        controller = AutomationController()
        action_counts: list[int] = []
        actual_rates: list[float] = []
        controller.action_count_changed.connect(action_counts.append)
        controller.actual_frequency_changed.connect(actual_rates.append)

        controller._action_count = 7
        controller._run_started_at = 2.5

        controller._emit_runtime_metrics(force_zero=True)

        self.assertEqual(action_counts[-1], 7)
        self.assertEqual(actual_rates[-1], 0.0)
        self.assertIsNone(controller._run_started_at)


if __name__ == "__main__":
    unittest.main()
