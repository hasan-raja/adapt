#!/usr/bin/env python3
"""
Run ADAPT eval prompts against a live backend.

Usage:
    python scripts/run_eval.py
    python scripts/run_eval.py --base-url http://localhost:8000 --output eval_results.json
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPTS_PATH = ROOT / "eval_prompts.json"


def post_json(url: str, payload: dict, timeout: int) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode("utf-8"))
        except Exception:
            data = {"error": str(e)}
        return e.code, data
    except Exception as e:
        return 0, {"error": str(e)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ADAPT eval prompt set.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--prompts", default=str(PROMPTS_PATH))
    parser.add_argument("--output", default=None)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    prompts_path = Path(args.prompts)
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))

    rows = []
    passed = 0

    print(f"Running {len(prompts)} eval prompts against {args.base_url}")
    print("-" * 108)
    print(
        f"{'ID':<20} {'Tier':<5} {'Task':<13} {'Compression':<12} "
        f"{'Tokens':>6} {'Cost':>7} {'Cache':<6} {'Latency':>8} Result"
    )
    print("-" * 108)

    for item in prompts:
        payload = {
            "session_id": f"eval-{item['id']}",
            "message": item["prompt"],
            "force_tier": item["tier"],
        }

        start = time.perf_counter()
        status, data = post_json(f"{args.base_url}/adapt", payload, args.timeout)
        latency = time.perf_counter() - start

        ok = status == 200 and bool(data.get("response"))
        passed += int(ok)

        row = {
            "id": item["id"],
            "category": item.get("category"),
            "language": item.get("language"),
            "expected_tier": item["tier"],
            "status": status,
            "ok": ok,
            "latency_sec": round(latency, 3),
            "tier_used": data.get("tier_used"),
            "task_type": data.get("task_type"),
            "model_used": data.get("model_used"),
            "compression_level": data.get("compression_level"),
            "tokens_used": data.get("tokens_used"),
            "cost_rs": data.get("cost_rs"),
            "cache_hit": data.get("cache_hit"),
            "cache_skipped_reason": data.get("cache_skipped_reason"),
            "trace": data.get("trace", []),
            "error": data.get("error") or data.get("detail"),
        }
        rows.append(row)

        result = "OK" if ok else "FAIL"
        print(
            f"{item['id']:<20} "
            f"{str(row['tier_used'] or '-'): <5} "
            f"{str(row['task_type'] or '-'): <13} "
            f"{str(row['compression_level'] or '-'): <12} "
            f"{str(row['tokens_used'] or '-'): >6} "
            f"{float(row['cost_rs'] or 0): >7.3f} "
            f"{str(row['cache_hit']): <6} "
            f"{row['latency_sec']: >7.2f}s "
            f"{result}"
        )

    score = (passed / len(prompts)) * 100 if prompts else 0
    print("-" * 108)
    print(f"Eval score: {passed}/{len(prompts)} = {score:.0f}%")

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Saved results to {output_path}")

    return 0 if passed == len(prompts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
