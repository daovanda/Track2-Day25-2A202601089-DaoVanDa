# NimbusAI GPU FinOps — Short Analysis Write-up

## 1. Baseline vs. optimized

The baseline treats every inference request as a large-model, on-demand
request without caching or batching. It costs **$48.87/day**, equivalent to
**$6.488 per 1M tokens**. After applying cascade routing, prompt caching and
batch pricing, inference costs fall to **$8.48/day**, or **$1.126 per 1M
tokens**. This is an **82.6% inference saving**.

Combining inference optimization with purchasing, right-sizing and stopping
idle GPUs gives the following monthly view:

| Metric | Baseline | Optimized |
|---|---:|---:|
| Monthly spend | $27,133 | $14,626 |
| Monthly savings | — | $12,507 |
| Total savings | — | 46.1% |

The result exceeds the lab target of at least 40% while remaining below the
95% sanity limit in the rubric.

## 2. Analysis of each cost lever

| Lever | Monthly saving | Explanation |
|---|---:|---|
| Inference: cascade/cache/batch | $1,212 | Route easy requests to the small model, cache repeated prefixes and batch non-real-time evaluation traffic. |
| Purchasing: spot/reserved | $10,040 | Use spot for interruptible jobs with checkpoints and reserved capacity for steady high-duty-cycle jobs. |
| Right-size util-lies | $655 | Replace GPUs with high clock activity but low real compute efficiency by a cheaper suitable tier. |
| Kill idle GPUs | $600 | Stop GPUs that remain running while effectively idle, saving $20/day or $600/month. |

Purchasing is the largest lever because the workload inventory contains several
long-running jobs. The tier policy recommends spot for interruptible jobs and
reserved capacity once utilization reaches the 55% break-even point. Spot is
not free: checkpoint overhead and expected rework are included in the
calculation, so the saving is an effective rather than nominal spot discount.

## 3. The GPU-Util lie

The audit flags `gpu-h100-4` and `gpu-a10g-1`. Both show at least 90%
GPU-Util, but their MFU is below 30%. GPU-Util from `nvidia-smi` primarily
indicates that the device is active during the sampling interval; it does not
measure how many useful model FLOPs are completed. Memory stalls,
synchronization, small kernels or kernel-launch overhead can therefore make a
GPU look busy while delivering only a fraction of its peak compute.

This matters financially because the provider still bills the full GPU-hour.
For example, `gpu-h100-4` has approximately 98% utilization but only about
19% MFU. The correct response is to profile the workload, improve batching or
kernel efficiency where possible, and right-size the instance when the low
compute efficiency is structural. Blindly using GPU-Util as the optimization
metric would preserve the waste.

## 4. Extensions completed

### Cache economics

The new `cache_is_worth_it()` function compares the one-time cache-write cost
with the savings from discounted reads. With a 10% read price and normalized
write cost of 1.0, the break-even is **1.11 reads per cached prefix**. The
workload estimate is **4.0 reads**, so caching is enabled in M2. This makes the
cache decision explicit instead of assuming that every cached input is always
profitable.

### Reasoning budget

M2 now reports reasoning and non-reasoning traffic separately. Reasoning is
**8.4% of requests**, but costs about **$1.40/day** and consumes roughly
**29,788 Wh/day**. The large energy impact follows the lab's 80× reasoning
multiplier. The routing rule is to reserve reasoning for low-confidence or
high-complexity tasks and use the small model for ordinary requests. Since the
observed reasoning share is already below 10%, an immediate 10% cap would not
save additional traffic; the useful control is preventing future growth above
that limit.

## 5. Recommendations for NimbusAI

1. **Implement purchasing policy first.** Move checkpointable training and
   evaluation workloads to spot, and commit only stable workloads that clear
   the 55% reserved break-even utilization.
2. **Fix efficiency before scaling the fleet.** Investigate the two util-lie
   GPUs using MFU/MBU and roofline analysis, right-size them, and automatically
   shut down GPUs below the idle threshold.
3. **Govern inference routing and sustainability.** Enforce cascade, cache and
   batch policies; keep reasoning behind a confidence/complexity gate. For
   interruptible work, prefer the clean `europe-north1` grid when latency and
   data-residency constraints permit: its illustrative carbon intensity is 30
   gCO2/kWh versus 380 gCO2/kWh in `us-east-1`.

Overall, the analysis shows why FinOps must measure both dollars per token and
real workload efficiency. A lower GPU-hour price alone does not guarantee a
lower serving cost if the GPU is underutilized, idle, or serving too many
expensive reasoning tokens.
