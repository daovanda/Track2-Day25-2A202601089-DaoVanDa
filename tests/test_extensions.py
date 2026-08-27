import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finops import pricing
from missions import m2_inference_levers


def test_cache_break_even_gate():
    assert pricing.cache_is_worth_it(2, 1, 0.10) is True
    assert pricing.cache_is_worth_it(1, 1, 0.10) is False


def test_reasoning_budget_is_measured():
    result = m2_inference_levers.run(verbose=False)
    assert result["reasoning_requests"] > 0
    assert result["reasoning_traffic_pct"] < 10
    assert result["reasoning_wh"] > result["non_reasoning_wh"]
