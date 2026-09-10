"""Deterministic, auditable explanations for fused scan decisions."""


COMPONENTS = (
    "activity_score",
    "prediction_score",
    "periodicity_score",
    "uncertainty",
    "information_gain",
    "drift_score",
)


class DecisionExplainer:
    def __init__(self, precision=2):
        if not isinstance(precision, int) or precision < 0:
            raise ValueError("precision must be a non-negative integer")
        self.precision = precision

    def explain(self, decision):
        """Return a structured explanation generated solely from decision numbers."""
        if not isinstance(decision, dict):
            raise ValueError("decision must be a dictionary")
        required = {"band", "dwell", *COMPONENTS}
        missing = required - set(decision)
        if missing:
            raise ValueError(f"decision is missing fields: {sorted(missing)}")
        if not isinstance(decision["band"], int) or decision["band"] < 0:
            raise ValueError("decision band must be a non-negative integer")
        if not isinstance(decision["dwell"], (int, float)) or decision["dwell"] < 0:
            raise ValueError("decision dwell must be non-negative")
        for component in COMPONENTS:
            value = decision[component]
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                raise ValueError(f"{component} must be between 0 and 1")

        scores = {component: round(decision[component], self.precision)
                  for component in COMPONENTS}
        strongest_component = max(COMPONENTS, key=lambda component: decision[component])
        return {
            "selected_band": decision["band"],
            "dwell": decision["dwell"],
            "components": scores,
            "reason": (
                f"Band {decision['band']} had the highest fused cognitive score; "
                f"the strongest supplied factor was {strongest_component}."
            ),
        }

    def format_explanation(self, decision):
        """Return a compact human-readable explanation for a single decision."""
        explanation = self.explain(decision)
        lines = [
            f"Selected Band: B{explanation['selected_band']}",
            f"Dwell: {explanation['dwell']} ms",
            "",
            "Reason:",
        ]
        for component, value in explanation["components"].items():
            lines.append(f"  {component}: {value:.{self.precision}f}")
        lines.extend(["", f"Decision: {explanation['reason']}"])
        return "\n".join(lines)
