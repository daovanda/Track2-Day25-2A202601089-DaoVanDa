# NimbusAI — GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cleanest region: europe-north1

## Technical analysis

- **GPU-Util lie:** `gpu-h100-4, gpu-a10g-1` reports high clock activity but low MFU; memory stalls, synchronization, or kernel-launch overhead can keep the SMs busy without delivering proportional FLOPs. The direct response is profiling and right-sizing, not trusting `nvidia-smi` utilization alone.
- **Cache economics:** caching is enabled because the estimated 4.0 reads/prefix exceeds the 1.11 read break-even. This contributes to the optimized $8.48/day inference bill.
- **Reasoning budget:** reasoning is 8.4% of requests but $1.40/day (16.5% of optimized inference spend) and 29,788 Wh/day. Route it only for low-confidence or high-complexity tasks; keep ordinary traffic on the small model.
- **Priority actions:** (1) purchase spot/reserved capacity (10,040 USD/month saved), (2) fix idle and util-lie GPUs (1,255 USD/month), then (3) enforce inference routing/cache/batch policies (1,212 USD/month).
- **Sustainability:** each non-reasoning median query uses 0.24 Wh, costs about $0.00003 in electricity, and emits 0.091 gCO2e in us-east-1. Moving flexible work to europe-north1 reduces grid carbon intensity from 380 to 30 gCO2/kWh, subject to latency and data-residency constraints.

_Figures are June-2026 as-of snapshots; re-baseline before acting._