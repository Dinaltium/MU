"""
models/cusum.py

WHY CUSUM (Cumulative Sum Control Chart):
  Standard threshold alerts ("score < 50 → alert") fire on a single
  bad data point and produce excessive noise. Doctors stop reading
  alerts if they're flooded.

  CUSUM detects SUSTAINED deterioration: it accumulates deviation
  from the expected recovery trajectory. A single bad check-in
  contributes a small amount to the sum. Only if the patient fails
  to improve over multiple check-ins does the sum exceed the threshold
  and fire an alert.

  Clinical benefit: fewer false alarms, more actionable signals.

MATHEMATICAL BASIS:
  For each check-in score s_t:
    deviation = target - s_t - slack
    cusum_t = max(0, cusum_{t-1} + deviation)

  Alert fires when cusum_t > threshold.

  Parameters (default):
    target    = 70  → expected recovery score on track
    slack     = 5   → allowable natural variation (5 points either way)
    threshold = 10  → cumulative slack before alert fires

SECURITY NOTE:
  • This model has no external dependencies — it's pure Python math.
    There are no file I/O or network calls to attack.
  • Input (scores) is a list of floats from the database. Database CHECK
    constraints ensure they are in [0, 100]. We still clamp defensively.
"""

import logging

logger = logging.getLogger(__name__)


class CUSUMMonitor:
    def __init__(
        self,
        target:    float = 70.0,
        slack:     float = 5.0,
        threshold: float = 10.0,
    ) -> None:
        self.target    = target
        self.slack     = slack
        self.threshold = threshold

    def update(self, scores: list[float]) -> dict:
        """
        Compute CUSUM on the full history of recovery scores.

        Returns:
            cusum_value : final accumulated sum
            alert       : True if threshold exceeded
            trend       : 'improving' | 'stable' | 'declining'
            message     : human-readable status string
        """
        if len(scores) < 2:
            return {
                "cusum_value": 0.0,
                "alert":       False,
                "trend":       "stable",
                "message":     "Insufficient data — at least 2 check-ins required",
            }

        cusum = 0.0
        for score in scores:
            score = max(0.0, min(score, 100.0))  # defensive clamp
            deviation = self.target - score - self.slack
            cusum     = max(0.0, cusum + deviation)

        alert = cusum > self.threshold

        # Trend from last 3 data points
        recent = scores[-3:] if len(scores) >= 3 else scores
        delta  = recent[-1] - recent[0]

        if delta > 5:
            trend = "improving"
        elif delta < -5:
            trend = "declining"
        else:
            trend = "stable"

        message = (
            "Recovery significantly below expected trajectory — "
            "consider reviewing treatment plan"
            if alert
            else f"Recovery on track (trend: {trend})"
        )

        return {
            "cusum_value": round(cusum, 2),
            "alert":       alert,
            "trend":       trend,
            "message":     message,
        }
