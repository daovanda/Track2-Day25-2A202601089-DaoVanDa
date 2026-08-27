"""Bonus — measure REAL tokens/sec on CPU and compare $/token to the sim.

Fully optional and guarded: if torch/transformers (or a model) are unavailable,
it prints setup instructions and exits 0 (never breaks the lab).
"""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def main() -> int:
    # This bonus is explicitly a PyTorch CPU benchmark.  Prevent an optional
    # TensorFlow/sklearn installation from being imported by transformers;
    # mixed NumPy ABI versions are common in teaching environments.
    os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
    os.environ.setdefault("USE_TF", "0")
    try:
        import torch  # noqa: F401
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as e:
        print("[skip] transformers/torch not installed — this bonus is optional.")
        print("       pip install torch transformers  (CPU wheels are fine)")
        print(f"       ({e})")
        return 0

    model_id = os.environ.get("LAB_MODEL", "sshleifer/tiny-gpt2")  # tiny, CPU-friendly
    try:
        tok = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id)
    except Exception as e:
        print(f"[skip] could not download '{model_id}' (offline?): {e}")
        return 0

    prompt = "GPU FinOps means measuring cost in dollars per million tokens, because"
    ids = tok(prompt, return_tensors="pt")
    t0 = time.time()
    out = model.generate(**ids, max_new_tokens=64, do_sample=False)
    dt = time.time() - t0
    new_tokens = out.shape[-1] - ids["input_ids"].shape[-1]
    tps = new_tokens / dt if dt > 0 else 0.0

    # crude $/token: a CPU box ~ $0.10/hr; cost = (time/3600)*rate / tokens
    rate_hr = float(os.environ.get("LAB_CPU_RATE_HR", "0.10"))
    cost_per_1m = (dt / 3600.0) * rate_hr / max(1, new_tokens) * 1e6

    print(f"model={model_id}  new_tokens={new_tokens}  time={dt:.2f}s")
    print(f"REAL throughput: {tps:.1f} tok/s on CPU")
    print(f"REAL ~${cost_per_1m:,.2f}/1M-token  (vs sim small-model ~$0.30/1M-token)")
    print("Takeaway: tok/s and utilization drive $/token far more than the sticker $/hr.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
