"""KPI threshold configuration for the NIAT Copilot."""

THRESHOLDS = {
    "lecture_delivery_pct":              {"good": 75, "warning": 50, "label": "Lecture Delivery %"},
    "practice_delivery_pct":             {"good": 75, "warning": 50, "label": "Practice Delivery %"},
    "exam_delivery_pct":                 {"good": 75, "warning": 50, "label": "Exam Delivery %"},
    "avg_delivery_pct":                  {"good": 75, "warning": 50, "label": "Avg Delivery %"},
    "module_quiz_conduction_pct":        {"good": 75, "warning": 50, "label": "Module Quiz Conduction %"},
    "module_quiz_participation_pct":     {"good": 70, "warning": 50, "label": "Module Quiz Participation %"},
    "module_quiz_pass_pct":              {"good": 70, "warning": 50, "label": "Module Quiz Pass %"},
    "skill_assessment_conduction_pct":   {"good": 60, "warning": 40, "label": "Skill Assessment Conduction %"},
    "skill_assessment_participation_pct":{"good": 70, "warning": 50, "label": "Skill Assessment Participation %"},
    "skill_assessment_pass_pct":         {"good": 70, "warning": 50, "label": "Skill Assessment Pass %"},
    "quiz_pass_pct":                     {"good": 70, "warning": 50, "label": "Classroom Quiz Pass %"},
    "quiz_attempt_pct":                  {"good": 70, "warning": 50, "label": "Classroom Quiz Attempt %"},
    "academic_attempt_pct":              {"good": 70, "warning": 50, "label": "Academic Assessment Attempt %"},
    "academic_pass_pct":                 {"good": 70, "warning": 50, "label": "Academic Assessment Pass %"},
    "deviation_pct": {
        "good": -10,     # ≥ -10% is on-track
        "warning": -25,  # ≥ -25% is a warning
        "label": "Schedule Deviation %",
        "inverted": True  # lower is worse
    },
}


def evaluate_metric(metric_key: str, value: float) -> dict:
    """Return severity and label for a single metric value."""
    cfg = THRESHOLDS.get(metric_key)
    if cfg is None:
        return {"status": "unknown", "label": metric_key, "value": value}

    inverted = cfg.get("inverted", False)
    good_threshold = cfg["good"]
    warn_threshold = cfg["warning"]

    if inverted:
        # Lower is worse (e.g. deviation %)
        if value >= good_threshold:
            status = "good"
        elif value >= warn_threshold:
            status = "warning"
        else:
            status = "critical"
    else:
        if value >= good_threshold:
            status = "good"
        elif value >= warn_threshold:
            status = "warning"
        else:
            status = "critical"

    return {
        "status": status,
        "label": cfg["label"],
        "value": round(value, 1),
        "threshold_good": good_threshold,
        "threshold_warning": warn_threshold,
    }


def check_metrics(metrics: dict, university: str = "") -> dict:
    """
    Evaluate a dict of {metric_key: value} against thresholds.
    Returns a structured report with per-metric status and overall severity.
    """
    results = {}
    warnings = []
    criticals = []

    for key, value in metrics.items():
        if value is None:
            continue
        try:
            val = float(value)
        except (TypeError, ValueError):
            continue
        eval_result = evaluate_metric(key, val)
        results[key] = eval_result
        if eval_result["status"] == "warning":
            warnings.append(eval_result["label"])
        elif eval_result["status"] == "critical":
            criticals.append(eval_result["label"])

    overall = "good"
    if warnings:
        overall = "warning"
    if criticals:
        overall = "critical"

    return {
        "university": university,
        "overall_status": overall,
        "critical_metrics": criticals,
        "warning_metrics": warnings,
        "metric_details": results,
        "needs_escalation": overall in ("warning", "critical"),
        "summary": _build_summary(university, overall, criticals, warnings),
    }


def _build_summary(university: str, overall: str, criticals: list, warnings: list) -> str:
    parts = []
    if university:
        parts.append(f"University: {university}")
    parts.append(f"Overall Status: {overall.upper()}")
    if criticals:
        parts.append(f"CRITICAL: {', '.join(criticals)}")
    if warnings:
        parts.append(f"WARNING: {', '.join(warnings)}")
    if not criticals and not warnings:
        parts.append("All metrics within acceptable range.")
    return " | ".join(parts)
