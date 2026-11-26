#!/usr/bin/env python3
"""Real compute worker running inside each Docker container (pause-safe & signal-aware)."""

import math
import os
import socket
import sys
import time

JOB_NAME = os.environ.get("JOB_NAME", "worker")
ROLE = os.environ.get("ROLE", "small")
RACK = os.environ.get("RACK", "rack-a")
LINK_MODE = os.environ.get("LINK_MODE", "nvlink")  # nvlink | cross-rack | mig | whole-gpu
WAIT_SIGNAL = os.environ.get("WAIT_SIGNAL", "0") == "1"
SIGNAL_FILE = os.environ.get("SIGNAL_FILE", "/tmp/go")
STEPS = int(os.environ.get("STEPS", "8"))
STEP_PAUSE = float(os.environ.get("STEP_PAUSE", "1.5"))
HOST_ID = socket.gethostname()[:12]


def real_matrix_compute(iters: int) -> float:
    """Perform genuine floating-point math work to simulate kernel execution."""
    t0 = time.perf_counter()
    acc = 0.0
    for i in range(1, iters):
        acc += math.sin(i * 0.001) * math.cos(i * 0.002)
    return (time.perf_counter() - t0) * 1000.0


def pause_safe_sleep(seconds: float) -> None:
    """Sleep in fine 0.12s ticks so cgroup `docker pause` freezes progress accurately."""
    ticks = max(1, int(round(seconds / 0.12)))
    tick_len = seconds / ticks
    for _ in range(ticks):
        time.sleep(tick_len)


def wait_for_peer_signal() -> None:
    """Hold GPU at 0% progress until orchestrator creates SIGNAL_FILE via `docker exec`."""
    waited = 0
    while not os.path.exists(SIGNAL_FILE):
        print(
            f"[{HOST_ID}] BLOCKED (0%): Giữ cứng GPU chờ peer đang Pending... ({waited}s)",
            flush=True,
        )
        # 8 x 0.125s sub-ticks so docker pause freezes wait counter cleanly
        for _ in range(8):
            if os.path.exists(SIGNAL_FILE):
                break
            time.sleep(0.125)
        waited += 1
        if waited >= 120:
            print(f"[{HOST_ID}] TIMEOUT: Quá thời gian chờ peer — thoát.", flush=True)
            sys.exit(0)
    print(
        f"[{HOST_ID}] UNBLOCKED: Đã đủ peer -> bắt đầu chạy ({LINK_MODE})",
        flush=True,
    )


def main() -> None:
    print(f"[{HOST_ID}] START job={JOB_NAME} role={ROLE} rack={RACK} link={LINK_MODE}", flush=True)

    if WAIT_SIGNAL:
        wait_for_peer_signal()

    compute_iters = 45000 if ROLE == "small" else 95000
    t_start = time.perf_counter()

    for step in range(1, STEPS + 1):
        ms = real_matrix_compute(compute_iters)
        pause_safe_sleep(STEP_PAUSE)
        pct = int(step * 100 / STEPS)
        if ROLE in ("finetune", "train"):
            sync_ms = 60 if LINK_MODE == "nvlink" else 720
            print(
                f"[{HOST_ID}] Step {step}/{STEPS} ({pct}%) | compute={ms:.0f}ms | AllReduce({LINK_MODE})={sync_ms}ms",
                flush=True,
            )
        else:
            print(
                f"[{HOST_ID}] Step {step}/{STEPS} ({pct}%) | compute={ms:.0f}ms | mode={LINK_MODE}",
                flush=True,
            )

    total = time.perf_counter() - t_start
    print(f"[{HOST_ID}] DONE job={JOB_NAME} elapsed={total:.2f}s", flush=True)


if __name__ == "__main__":
    main()
