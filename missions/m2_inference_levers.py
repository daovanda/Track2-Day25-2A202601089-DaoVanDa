"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing
from finops import sustainability

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}
CACHE_AVG_READS = 4.0
CACHE_WRITE_COST_PER_M = 1.0


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = opt_cost = 0.0
    reasoning_cost = non_reasoning_cost = 0.0
    reasoning_wh = non_reasoning_wh = 0.0
    reasoning_requests = 0
    total_tokens = 0
    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        is_reasoning = bool(int(num(r["is_reasoning"])))
        # Cache economics is an explicit gate: only apply cached-read pricing
        # when the expected repeated reads recover the write cost.
        if not pricing.cache_is_worth_it(CACHE_AVG_READS, CACHE_WRITE_COST_PER_M):
            cached = 0
        total_tokens += inp + out
        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)
        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        row_cost = pricing.request_cost(inp, out, pin, pout, cached_in=cached, batch=is_batch)
        opt_cost += row_cost
        row_wh = sustainability.wh_per_query(inp + out, is_reasoning=is_reasoning)
        if is_reasoning:
            reasoning_requests += 1
            reasoning_cost += row_cost
            reasoning_wh += row_wh
        else:
            non_reasoning_cost += row_cost
            non_reasoning_wh += row_wh

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")
        print(f"cache gate: avg_reads={CACHE_AVG_READS:.1f}, break-even=1.11 -> {pricing.cache_is_worth_it(CACHE_AVG_READS, CACHE_WRITE_COST_PER_M)}")
        print(f"reasoning : {reasoning_requests/len(rows):.1%} of requests, ${reasoning_cost:,.2f}, {reasoning_wh:,.0f} Wh (80x energy multiplier)")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "cache_gate": pricing.cache_is_worth_it(CACHE_AVG_READS, CACHE_WRITE_COST_PER_M),
        "cache_break_even_reads": round(CACHE_WRITE_COST_PER_M / (1 - 0.10), 3),
        "reasoning_requests": reasoning_requests,
        "reasoning_traffic_pct": round(reasoning_requests / len(rows) * 100, 1) if rows else 0.0,
        "reasoning_cost": round(reasoning_cost, 2),
        "non_reasoning_cost": round(non_reasoning_cost, 2),
        "reasoning_wh": round(reasoning_wh, 2),
        "non_reasoning_wh": round(non_reasoning_wh, 2),
        "reasoning_energy_multiplier": round(reasoning_wh / non_reasoning_wh * (len(rows) - reasoning_requests) / reasoning_requests, 1) if reasoning_requests and non_reasoning_wh else 0.0,
    }


if __name__ == "__main__":
    run()
