from dataclasses import dataclass
from typing import Iterable

@dataclass
class ReconciliationResult:
    status: str
    min_value: float
    max_value: float
    difference: float
    difference_rate: float
    details: list[dict]


def reconcile(values: Iterable[tuple[str, float]], tolerance: float = 0.0) -> ReconciliationResult:
    vals = list(values)
    if len(vals) < 2:
        raise ValueError("at least two values required")
    nums = [v for _, v in vals]
    lo, hi = min(nums), max(nums)
    diff = hi - lo
    rate = 0.0 if hi == 0 else diff / abs(hi)
    status = "within_tolerance" if diff <= tolerance else "unresolved_difference"
    return ReconciliationResult(status, lo, hi, diff, rate, [{"source": s, "value": v} for s, v in vals])
