# Bonus completion report

All three optional bonuses are implemented and smoke-tested.

## 1. LiteLLM-style cost tracker

Run from `bonus/litellm_tracker`:

```bash
python demo.py
```

Observed result: `team-chat` is hard-stopped after 10 requests at a projected
spend of `$0.0507` against the `$0.05` cap; final logged spend is `$0.0460`.
`team-eval` continues under its budget using the small model and batch discount.

## 2. Local model benchmark

Run from `bonus/local_model`:

```bash
python run_local.py
```

Measured on this machine with `sshleifer/tiny-gpt2`: **328.1 tok/s** and about
**$0.08/1M-token** at the configured CPU rate of `$0.10/hour`. The script has a
safe fallback when PyTorch/Transformers or model downloads are unavailable.

## 3. Prometheus + Grafana dashboard

The pure-Python exporter was checked through its HTTP `/metrics` endpoint:

- HTTP status: `200`
- MFU samples: `11` (one per synthetic GPU)
- `gpu-h100-4` is present with high GPU-Util and low MFU
- Wasted-cost metric: `gpu_wasted_cost_usd_per_hr`

The Grafana dashboard JSON parses successfully and contains panels for
GPU-Util, MFU, and wasted dollars per hour. The Compose configuration validates
with `docker compose config`. To launch the full stack:

```bash
cd bonus/docker
docker compose up
```

Grafana is available at `http://localhost:3000` and Prometheus at
`http://localhost:9090`.
