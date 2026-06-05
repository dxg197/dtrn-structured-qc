from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


SCHEMA = "gg_llm_dtrn_replacement_scout_v0_4_3"

QUALITY_FIELDS = ["quality_score", "long_context_score"]
LATENCY_FIELDS = ["p95_latency_ms", "time_to_first_token_ms", "inter_token_latency_ms", "failure_rate"]
THROUGHPUT_FIELDS = ["tokens_per_second", "output_tokens_per_second"]


@dataclass
class DTRNReplacementDecision:
    module_path: str
    module_type: str
    candidate_type: str
    baseline_params: int
    candidate_params: int
    parameter_reduction_pct: float
    baseline_quality_score: Optional[float]
    candidate_quality_score: Optional[float]
    baseline_long_context_score: Optional[float]
    candidate_long_context_score: Optional[float]
    baseline_p95_latency_ms: Optional[float]
    candidate_p95_latency_ms: Optional[float]
    baseline_tokens_per_second: Optional[float]
    candidate_tokens_per_second: Optional[float]
    baseline_failure_rate: Optional[float]
    candidate_failure_rate: Optional[float]
    decision: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _num(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _candidate_rows(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [dict(x) for x in data]
    if isinstance(data, dict):
        for key in ["candidates", "records", "modules", "dtrn_candidates"]:
            value = data.get(key)
            if isinstance(value, list):
                return [dict(x) for x in value]
        return [dict(data)]
    return []


def _metric(row: Dict[str, Any], explicit: str, nested: str) -> Optional[float]:
    if explicit in row:
        return _num(row.get(explicit))
    metrics = row.get("metrics")
    if isinstance(metrics, dict):
        return _num(metrics.get(nested))
    return None


def _passes_no_regression(row: Dict[str, Any], tolerance: float) -> (bool, List[str]):
    reasons: List[str] = []

    for field in QUALITY_FIELDS:
        base = _metric(row, "baseline_" + field, field)
        cand = _metric(row, "candidate_" + field, field)
        if base is not None and cand is not None and cand + tolerance < base:
            reasons.append("{} degraded: candidate {} < baseline {}".format(field, cand, base))

    for field in LATENCY_FIELDS:
        base = _metric(row, "baseline_" + field, field)
        cand = _metric(row, "candidate_" + field, field)
        if base is not None and cand is not None and cand > base + tolerance:
            reasons.append("{} regressed: candidate {} > baseline {}".format(field, cand, base))

    for field in THROUGHPUT_FIELDS:
        base = _metric(row, "baseline_" + field, field)
        cand = _metric(row, "candidate_" + field, field)
        if base is not None and cand is not None and cand + tolerance < base:
            reasons.append("{} regressed: candidate {} < baseline {}".format(field, cand, base))

    return (len(reasons) == 0, reasons)


def score_dtrn_candidate(row: Dict[str, Any], min_param_reduction_pct: float = 10.0, tolerance: float = 0.0) -> DTRNReplacementDecision:
    baseline_params = _int(row.get("baseline_params") or row.get("dense_params") or row.get("original_params"))
    candidate_params = _int(row.get("candidate_params") or row.get("dtrn_params") or row.get("replacement_params"))
    if baseline_params > 0:
        reduction = 100.0 * (baseline_params - candidate_params) / float(baseline_params)
    else:
        reduction = 0.0

    no_regression, regression_reasons = _passes_no_regression(row, tolerance)
    if reduction < min_param_reduction_pct:
        decision = "reject"
        reason = "parameter reduction {:.3f}% is below required {:.3f}%".format(reduction, min_param_reduction_pct)
    elif not no_regression:
        decision = "reject"
        reason = "; ".join(regression_reasons)
    else:
        # Accept only when at least one quality, latency, throughput, or failure metric is present.
        observed_metrics = []
        for prefix in ["baseline_", "candidate_"]:
            for field in QUALITY_FIELDS + LATENCY_FIELDS + THROUGHPUT_FIELDS:
                if _metric(row, prefix + field, field) is not None:
                    observed_metrics.append(prefix + field)
        if not observed_metrics:
            decision = "needs_ablation"
            reason = "parameter goal passed, but no performance metrics were supplied for no-regression validation"
        else:
            decision = "accept"
            reason = "meets parameter reduction target and no-regression gates"

    return DTRNReplacementDecision(
        module_path=str(row.get("module_path") or row.get("name") or "unknown"),
        module_type=str(row.get("module_type") or row.get("layer_type") or "unknown"),
        candidate_type=str(row.get("candidate_type") or row.get("replacement_type") or "dtrn"),
        baseline_params=baseline_params,
        candidate_params=candidate_params,
        parameter_reduction_pct=round(reduction, 6),
        baseline_quality_score=_metric(row, "baseline_quality_score", "quality_score"),
        candidate_quality_score=_metric(row, "candidate_quality_score", "quality_score"),
        baseline_long_context_score=_metric(row, "baseline_long_context_score", "long_context_score"),
        candidate_long_context_score=_metric(row, "candidate_long_context_score", "long_context_score"),
        baseline_p95_latency_ms=_metric(row, "baseline_p95_latency_ms", "p95_latency_ms"),
        candidate_p95_latency_ms=_metric(row, "candidate_p95_latency_ms", "p95_latency_ms"),
        baseline_tokens_per_second=_metric(row, "baseline_tokens_per_second", "tokens_per_second"),
        candidate_tokens_per_second=_metric(row, "candidate_tokens_per_second", "tokens_per_second"),
        baseline_failure_rate=_metric(row, "baseline_failure_rate", "failure_rate"),
        candidate_failure_rate=_metric(row, "candidate_failure_rate", "failure_rate"),
        decision=decision,
        reason=reason,
    )


def build_dtrn_replacement_report(candidates_path: str, min_param_reduction_pct: float = 10.0, tolerance: float = 0.0) -> Dict[str, Any]:
    rows = _candidate_rows(_load_json(candidates_path))
    decisions = [score_dtrn_candidate(row, min_param_reduction_pct=min_param_reduction_pct, tolerance=tolerance) for row in rows]
    accepted = [d for d in decisions if d.decision == "accept"]
    rejected = [d for d in decisions if d.decision == "reject"]
    needs_ablation = [d for d in decisions if d.decision == "needs_ablation"]
    best = sorted(accepted, key=lambda d: d.parameter_reduction_pct, reverse=True)
    return {
        "schema": SCHEMA,
        "source": candidates_path,
        "min_param_reduction_pct": min_param_reduction_pct,
        "tolerance": tolerance,
        "candidate_count": len(decisions),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "needs_ablation_count": len(needs_ablation),
        "best_accept": best[0].to_dict() if best else None,
        "decisions": [d.to_dict() for d in decisions],
    }


def write_dtrn_replacement_report(report: Dict[str, Any], out_json: str, out_md: str) -> None:
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# GG LLM Optimizer DTRN Replacement Scout v0.4.3",
        "",
        "This report identifies places where DTRN variants may replace conventional neural-network modules while reducing parameters by at least {:.3f}% with no measured performance regression.".format(report.get("min_param_reduction_pct", 10.0)),
        "",
        "| Module | Type | Candidate | Baseline params | Candidate params | Reduction % | Decision | Reason |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for d in report.get("decisions", []):
        lines.append(
            "| {module_path} | {module_type} | {candidate_type} | {baseline_params} | {candidate_params} | {parameter_reduction_pct:.3f} | {decision} | {reason} |".format(**d)
        )
    lines.extend([
        "",
        "## Acceptance gates",
        "",
        "A DTRN replacement is accepted only when parameter reduction is at least the configured threshold and quality, long-context score, latency, throughput, and failure-rate metrics do not regress relative to the dense baseline.",
    ])
    Path(out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
