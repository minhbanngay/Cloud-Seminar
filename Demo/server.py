#!/usr/bin/env python3
"""Live Docker 8-Container GPU Scheduling Demo — Slow-Paced, Pauseable, Smooth Web UI."""

import datetime
import http.server
import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import uuid

PORT = 8090
IMAGE_NAME = "seminar-ai-worker:local"
LABEL_KEY = "seminar-demo=true"


def find_docker_bin():
    for candidate in (
        shutil.which("docker"),
        "/usr/local/bin/docker",
        "/opt/homebrew/bin/docker",
        "/Applications/Docker.app/Contents/Resources/bin/docker",
    ):
        if candidate and os.path.exists(candidate):
            return candidate
    return "docker"


DOCKER_BIN = find_docker_bin()

SCENARIOS = {
    "mixed": {
        "id": "mixed",
        "tab": "1. Hỗn hợp chuẩn",
        "title": "Hỗn hợp: 3 Job nhỏ (1/3 GPU) + Fine-tune (2G) + Sync-Train (2G) + Eval (1G)",
        "mig_gpus": [0],
        "mig_saved": 2,
        "specs": [
            {"pid": "P1", "slug": "p1-infer-img", "title": "Inference Ảnh", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 12},
            {"pid": "P2", "slug": "p2-infer-nlp", "title": "Inference NLP", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 12},
            {"pid": "P3", "slug": "p3-dev-nb", "title": "Dev Notebook", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 12},
            {"pid": "P4", "slug": "p4-finetune-1", "title": "Fine-tune W1", "job_group": "Fine-tune · 2 GPU", "role": "finetune", "req_label": "1 GPU (NVLink)", "need_pct": 92, "steps": 6},
            {"pid": "P5", "slug": "p5-finetune-2", "title": "Fine-tune W2", "job_group": "Fine-tune · 2 GPU", "role": "finetune", "req_label": "1 GPU (NVLink)", "need_pct": 92, "steps": 6},
            {"pid": "P6", "slug": "p6-train-1", "title": "Sync-Train W1", "job_group": "Sync-Train · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 6},
            {"pid": "P7", "slug": "p7-train-2", "title": "Sync-Train W2", "job_group": "Sync-Train · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 6},
            {"pid": "P8", "slug": "p8-batch-eval", "title": "Batch Eval", "job_group": "Eval · 1 GPU", "role": "eval", "req_label": "1 GPU", "need_pct": 90, "steps": 12},
        ],
    },
    "inference_burst": {
        "id": "inference_burst",
        "tab": "2. Bùng nổ 6 Inference",
        "title": "6 Microservice Inference nhỏ (1/3 GPU) + 1 Job Training (2 GPU)",
        "mig_gpus": [0, 1],
        "mig_saved": 4,
        "specs": [
            {"pid": "P1", "slug": "p1-inf-vision", "title": "Infer Vision", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 12},
            {"pid": "P2", "slug": "p2-inf-nlp", "title": "Infer NLP", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 12},
            {"pid": "P3", "slug": "p3-inf-asr", "title": "Infer Giọng nói", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 12},
            {"pid": "P4", "slug": "p4-inf-ocr", "title": "Infer OCR", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 12},
            {"pid": "P5", "slug": "p5-inf-embed", "title": "Embed Vector", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 12},
            {"pid": "P6", "slug": "p6-inf-rerank", "title": "Rerank API", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 12},
            {"pid": "P7", "slug": "p7-train-1", "title": "Model Train W1", "job_group": "Train · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 8},
            {"pid": "P8", "slug": "p8-train-2", "title": "Model Train W2", "job_group": "Train · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 8},
        ],
    },
    "gang_deadlock": {
        "id": "gang_deadlock",
        "tab": "3. Tranh chấp 3 Job Lớn",
        "title": "2 Job nhỏ (1/3 GPU) + 3 Job đa-GPU cạnh tranh Rack (3 × 2-GPU)",
        "mig_gpus": [0],
        "mig_saved": 1,
        "specs": [
            {"pid": "P1", "slug": "p1-dev-a", "title": "Dev Sandbox", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 7},
            {"pid": "P2", "slug": "p2-inf-b", "title": "Infer Monitor", "job_group": "Nhỏ · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 7},
            {"pid": "P3", "slug": "p3-ft-a1", "title": "Fine-tune A1", "job_group": "Job A · 2 GPU", "role": "finetune", "req_label": "1 GPU (NVLink)", "need_pct": 92, "steps": 6},
            {"pid": "P4", "slug": "p4-ft-a2", "title": "Fine-tune A2", "job_group": "Job A · 2 GPU", "role": "finetune", "req_label": "1 GPU (NVLink)", "need_pct": 92, "steps": 6},
            {"pid": "P5", "slug": "p5-pt-b1", "title": "Pre-train B1", "job_group": "Job B · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 6},
            {"pid": "P6", "slug": "p6-pt-b2", "title": "Pre-train B2", "job_group": "Job B · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 6},
            {"pid": "P7", "slug": "p7-rl-c1", "title": "RLHF Train C1", "job_group": "Job C · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 6},
            {"pid": "P8", "slug": "p8-rl-c2", "title": "RLHF Train C2", "job_group": "Job C · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 6},
        ],
    },
    "backfill_fair": {
        "id": "backfill_fair",
        "tab": "4. Chống đói Job Nhỏ",
        "title": "3 Job Training lớn (2 GPU) đến trước + 2 Job nhỏ tương tác đến sau",
        "mig_gpus": [],
        "mig_saved": 1,
        "specs": [
            {"pid": "P1", "slug": "p1-tr-a1", "title": "Train A1", "job_group": "Train A · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 9},
            {"pid": "P2", "slug": "p2-tr-a2", "title": "Train A2", "job_group": "Train A · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 9},
            {"pid": "P3", "slug": "p3-tr-b1", "title": "Train B1", "job_group": "Train B · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 9},
            {"pid": "P4", "slug": "p4-tr-b2", "title": "Train B2", "job_group": "Train B · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 9},
            {"pid": "P5", "slug": "p5-tr-c1", "title": "Train C1", "job_group": "Train C · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 8},
            {"pid": "P6", "slug": "p6-tr-c2", "title": "Train C2", "job_group": "Train C · 2 GPU", "role": "train", "req_label": "1 GPU (NVLink)", "need_pct": 94, "steps": 8},
            {"pid": "P7", "slug": "p7-live-1", "title": "Interactive UI 1", "job_group": "Tương tác · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 8},
            {"pid": "P8", "slug": "p8-live-2", "title": "Interactive UI 2", "job_group": "Tương tác · 1/3 GPU", "role": "small", "req_label": "1/3 GPU", "need_pct": 32, "steps": 8},
        ],
    },
}

STATE_LOCK = threading.Lock()
DOCKER_OP_LOCK = threading.Lock()
PAUSE_EVENT = threading.Event()
PAUSE_EVENT.set()  # Set = not paused

# Mock container states used ONLY if user explicitly starts simulation mode when Docker is offline
MOCK_WORKERS = {}

STATE = {
    "scenario": "mixed",      # mixed | inference_burst | gang_deadlock | backfill_fair
    "mode": "idle",           # idle | baseline | proposed
    "sim_mode": False,        # False = real Docker containers, True = local mock preview
    "running": False,
    "paused": False,
    "accumulated_s": 0.0,
    "last_resumed_at": None,
    "phase_banner": "Sẵn sàng: Chọn kịch bản và bấm nút 1 hoặc 2 để chạy 8 containers.",
    "gpus": [],               # 4 GPUs across 2 Racks (Rack A: 0,1 | Rack B: 2,3)
    "processes": [],          # Fixed 8 processes (P1..P8)
    "logs": [],
    "benchmarks": {
        k: {"baseline": None, "proposed": None}
        for k in SCENARIOS
    },
    "stats": {
        "util_sum": 0.0,
        "util_samples": 0,
        "peak_waiting": 0,
        "deadlock_events": 0,
        "cross_rack_jobs": 0,
        "mig_gpus_saved": 0,
    },
    "docker_ok": True,
    "docker_error": "",
    "run_id": 0,
}


def run_cmd(args, timeout=15):
    cmd = [DOCKER_BIN] + args[1:] if args and args[0] == "docker" else args
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except FileNotFoundError:
        return 127, "", "Không tìm thấy lệnh docker."
    except subprocess.TimeoutExpired:
        return 124, "", "Lệnh docker bị timeout."


def add_log(tag, msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    STATE["logs"].insert(0, {"time": ts, "tag": tag, "msg": msg})
    del STATE["logs"][40:]


def cleanup_containers():
    with DOCKER_OP_LOCK:
        with STATE_LOCK:
            MOCK_WORKERS.clear()
        rc, out, _ = run_cmd(["docker", "ps", "-aq", "--filter", f"label={LABEL_KEY}"], timeout=8)
        if rc == 0 and out:
            ids = out.split()
            run_cmd(["docker", "rm", "-f"] + ids, timeout=20)


def init_gpus(scenario_id, mode):
    mig_gpus = SCENARIOS.get(scenario_id, SCENARIOS["mixed"])["mig_gpus"]
    gpus = []
    for i in range(4):
        gpus.append({
            "id": i,
            "rack": "rack-a" if i < 2 else "rack-b",
            "node": f"Node-{i + 1}",
            "mig_mode": (mode == "proposed" and i in mig_gpus),
            "processes": [],
            "alloc_pct": 0,
            "used_pct": 0,
            "wasted_pct": 0,
            "blocked": False,
            "cross_rack": False,
        })
    return gpus


def init_processes(scenario_id, mode):
    specs = SCENARIOS.get(scenario_id, SCENARIOS["mixed"])["specs"]
    prefix = "base" if mode == "baseline" else ("prop" if mode == "proposed" else "demo")
    wait_msg = (
        "Đang chờ kube-scheduler cấp GPU"
        if mode == "baseline"
        else ("Đang xếp hàng trong Kueue Queue" if mode == "proposed" else "Sẵn sàng khởi chạy")
    )
    procs = []
    for spec in specs:
        procs.append({
            "pid": spec["pid"],
            "name": f"{prefix}-{spec['slug']}",
            "title": spec["title"],
            "job_group": spec["job_group"],
            "role": spec["role"],
            "req_label": spec["req_label"],
            "need_pct": spec["need_pct"],
            "steps": spec["steps"],
            "state": "waiting",       # waiting | pending | blocked | running | completed
            "wait_reason": wait_msg,
            "gpu_id": None,
            "rack": None,
            "mig_slice": None,
            "alloc_pct": 0,
            "used_pct": 0,
            "wasted_pct": 0,
            "cross_rack": False,
            "link_mode": "",
            "progress": 0,
            "cid": "",
            "last_line": wait_msg,
        })
    return procs


def is_run_active(run_id):
    with STATE_LOCK:
        return STATE["run_id"] == run_id


def get_elapsed_locked():
    total = STATE["accumulated_s"]
    if STATE["running"] and not STATE["paused"] and STATE["last_resumed_at"] is not None:
        total += max(0.0, time.time() - STATE["last_resumed_at"])
    return total


def smart_sleep(duration, run_id):
    """Sleep for `duration` active seconds while honoring Pause/Resume & run cancellation."""
    remaining = duration
    while remaining > 0:
        if not is_run_active(run_id):
            return False
        with STATE_LOCK:
            paused = STATE["paused"]
        if paused:
            PAUSE_EVENT.wait(timeout=0.2)
            continue
        chunk = min(0.12, remaining)
        time.sleep(chunk)
        remaining -= chunk
    return is_run_active(run_id)


def update_proc(pid, **kwargs):
    with STATE_LOCK:
        for p in STATE["processes"]:
            if p["pid"] == pid:
                p.update(kwargs)
                break


def get_proc_state(pid):
    with STATE_LOCK:
        for p in STATE["processes"]:
            if p["pid"] == pid:
                return p["state"]
    return None


def wait_until_completed(pids, run_id, mode="all"):
    """Wait cleanly until any or all specified pids complete, honoring pause."""
    while is_run_active(run_id):
        with STATE_LOCK:
            paused = STATE["paused"]
            states = [p["state"] for p in STATE["processes"] if p["pid"] in pids]
        if paused:
            PAUSE_EVENT.wait(timeout=0.2)
            continue
        done = all(s == "completed" for s in states) if mode == "all" else any(s == "completed" for s in states)
        if done:
            return True
        time.sleep(0.2)
    return False


def wait_any_completed_and_get(pids, run_id):
    """Wait until at least one of pids completes, return that process dict copy."""
    while is_run_active(run_id):
        with STATE_LOCK:
            paused = STATE["paused"]
            for p in STATE["processes"]:
                if p["pid"] in pids and p["state"] == "completed":
                    return dict(p)
        if paused:
            PAUSE_EVENT.wait(timeout=0.2)
            continue
        time.sleep(0.2)
    return None


def spawn_process_container(
    pid,
    gpu_id,
    rack,
    link_mode,
    step_pause,
    mig_slice=None,
    wait_signal=False,
    sim_mode=False,
    run_id=0,
):
    with STATE_LOCK:
        proc = next(p for p in STATE["processes"] if p["pid"] == pid)
        cname = proc["name"]
        role = proc["role"]
        steps = proc["steps"]
        need_pct = proc["need_pct"]

    if sim_mode:
        cid = uuid.uuid4().hex[:12]
        with STATE_LOCK:
            MOCK_WORKERS[cname] = {
                "step": 0,
                "steps": steps,
                "step_pause": step_pause,
                "blocked": wait_signal,
                "progress": 0,
                "done": False,
                "last_line": "BLOCKED (0%): Giữ cứng GPU chờ peer..." if wait_signal else "Đang khởi tạo container...",
                "last_tick": time.time(),
                "link_mode": link_mode,
                "role": role,
            }
    else:
        cmd = [
            "docker", "run", "-d",
            "--name", cname,
            "--label", LABEL_KEY,
            "--cpus", "0.25" if mig_slice is not None else "0.5",
            "--memory", "128m" if mig_slice is not None else "256m",
            "-e", f"JOB_NAME={cname}",
            "-e", f"ROLE={role}",
            "-e", f"RACK={rack}",
            "-e", f"LINK_MODE={link_mode}",
            "-e", f"WAIT_SIGNAL={'1' if wait_signal else '0'}",
            "-e", f"STEPS={steps}",
            "-e", f"STEP_PAUSE={step_pause}",
            IMAGE_NAME,
        ]
        rc, out, err = run_cmd(cmd, timeout=15)
        if rc != 0:
            with STATE_LOCK:
                add_log("ERR", f"Không khởi chạy được container {cname}: {err}")
            return False
        cid = out[:12]

        # If user clicked Pause right during `docker run`, freeze the container immediately
        with STATE_LOCK:
            should_pause = STATE["paused"] and STATE["run_id"] == run_id
        if should_pause:
            run_cmd(["docker", "pause", cname], timeout=8)

    alloc_pct = 33 if mig_slice is not None else 100
    if wait_signal:
        state_str = "blocked"
        used_pct = 0
        wasted_pct = 100
        wait_reason = f"Giữ cứng GPU {gpu_id} (0%) chờ peer đang Pending"
    else:
        state_str = "running"
        if mig_slice is not None:
            used_pct = need_pct
            wasted_pct = 0
        elif link_mode == "cross-rack":
            used_pct = 48
            wasted_pct = 0
        else:
            used_pct = need_pct
            wasted_pct = max(0, 100 - need_pct) if role == "small" else 0
        wait_reason = ""

    with STATE_LOCK:
        if STATE["run_id"] != run_id:
            return False
        for p in STATE["processes"]:
            if p["pid"] == pid:
                p["state"] = state_str
                p["wait_reason"] = wait_reason
                p["gpu_id"] = gpu_id
                p["rack"] = rack
                p["mig_slice"] = mig_slice
                p["alloc_pct"] = alloc_pct
                p["used_pct"] = used_pct
                p["wasted_pct"] = wasted_pct
                p["cross_rack"] = (link_mode == "cross-rack")
                p["link_mode"] = link_mode
                p["cid"] = cid
                p["progress"] = 0
                p["last_line"] = "Đang khởi tạo container..." if not wait_signal else wait_reason
                break
        slice_txt = f" · MIG Slice {mig_slice}/3" if mig_slice else ""
        tag = "MOCK" if sim_mode else "DOCKER"
        add_log(tag, f"{pid} ({cname} · {cid}) -> GPU {gpu_id} [{rack.upper()}{slice_txt} · {link_mode}]")
    return True


def unblock_process_container(pid, sim_mode=False):
    with STATE_LOCK:
        proc = next(p for p in STATE["processes"] if p["pid"] == pid)
        cname = proc["name"]
        gpu_id = proc["gpu_id"]

    if sim_mode:
        with STATE_LOCK:
            if cname in MOCK_WORKERS:
                MOCK_WORKERS[cname]["blocked"] = False
                MOCK_WORKERS[cname]["last_tick"] = time.time()
                MOCK_WORKERS[cname]["last_line"] = "UNBLOCKED: Peer đã sẵn sàng -> bắt đầu chạy (cross-rack)"
    else:
        run_cmd(["docker", "exec", cname, "touch", "/tmp/go"], timeout=8)

    with STATE_LOCK:
        for p in STATE["processes"]:
            if p["pid"] == pid:
                p["state"] = "running"
                p["wait_reason"] = ""
                p["used_pct"] = 48
                p["wasted_pct"] = 0
                p["cross_rack"] = True
                break
        add_log("EXEC", f"{pid} trên GPU {gpu_id} đã có peer -> mở khóa & chạy Cross-Rack (720ms)!")


def refresh_gpu_map_locked():
    mig_cfg = SCENARIOS.get(STATE["scenario"], SCENARIOS["mixed"])["mig_gpus"]
    for g in STATE["gpus"]:
        g["processes"] = []
        g["alloc_pct"] = 0
        g["used_pct"] = 0
        g["wasted_pct"] = 0
        g["blocked"] = False
        g["cross_rack"] = False
        g["mig_mode"] = (STATE["mode"] == "proposed" and g["id"] in mig_cfg)

    for p in STATE["processes"]:
        if p["state"] in ("running", "blocked") and p["gpu_id"] is not None:
            g = STATE["gpus"][p["gpu_id"]]
            g["processes"].append({
                "pid": p["pid"],
                "title": p["title"],
                "cid": p["cid"],
                "state": p["state"],
                "progress": p["progress"],
                "mig_slice": p["mig_slice"],
                "alloc_pct": p["alloc_pct"],
                "used_pct": p["used_pct"],
                "wasted_pct": p["wasted_pct"],
                "cross_rack": p["cross_rack"],
                "link_mode": p["link_mode"],
            })
            if p["state"] == "blocked":
                g["mig_mode"] = False
                g["blocked"] = True
                g["alloc_pct"] = 100
                g["used_pct"] = 0
                g["wasted_pct"] = 100
            elif p["mig_slice"] is not None:
                g["mig_mode"] = True
                g["alloc_pct"] = min(100, g["alloc_pct"] + 33)
                g["used_pct"] = min(98, g["used_pct"] + p["used_pct"])
                g["wasted_pct"] = 0
            else:
                g["mig_mode"] = False
                g["alloc_pct"] = 100
                g["used_pct"] = p["used_pct"]
                g["wasted_pct"] = p["wasted_pct"]
                if p["cross_rack"]:
                    g["cross_rack"] = True

    waiting_cnt = sum(1 for p in STATE["processes"] if p["state"] == "pending")
    if waiting_cnt > STATE["stats"]["peak_waiting"]:
        STATE["stats"]["peak_waiting"] = waiting_cnt


def mark_pending_locked(pids, reasons):
    for p in STATE["processes"]:
        if p["pid"] in pids:
            p["state"] = "pending"
            p["wait_reason"] = reasons.get(p["pid"], "Pending: Cụm đã hết GPU (4/4 bị chiếm)")


def run_mixed_scenario(mode, sim_mode, my_run):
    if mode == "baseline":
        with STATE_LOCK:
            STATE["phase_banner"] = "Cách mặc định (K8s): Cấp nguyên 1 GPU/Pod, rải đều qua Rack và không gom nhóm — theo dõi từng process!"
            add_log("K8S-DEF", "[Kịch bản Hỗn hợp] Nhận 8 containers vào hàng đợi FIFO.")
        if not smart_sleep(2.0, my_run):
            return

        for pid, gid, rack in [("P1", 0, "rack-a"), ("P2", 2, "rack-b"), ("P3", 1, "rack-a")]:
            if not spawn_process_container(pid, gid, rack, "whole-gpu", 1.6, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                STATE["phase_banner"] = f"{pid} chỉ cần 32% nhưng khóa nguyên GPU {gid} (68% GPU bị lãng phí!)."
                refresh_gpu_map_locked()
            if not smart_sleep(1.8, my_run):
                return

        if not spawn_process_container("P4", 3, "rack-b", "cross-rack", 2.9, wait_signal=True, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            STATE["stats"]["deadlock_events"] = 1
            mark_pending_locked(
                ("P5", "P6", "P7", "P8"),
                {"P5": "Pending: Hết GPU trống! Làm P4 khóa chết GPU 3 ở 0%"},
            )
            STATE["phase_banner"] = "Tắc nghẽn! 4/4 GPU đã kín: P4 giữ chết GPU 3 ở 0%, còn P5, P6, P7, P8 bị kẹt Pending!"
            add_log("WARN", "DEADLOCK: P4 giữ GPU 3 (0%) chờ P5 | P5..P8 kẹt Pending!")
            refresh_gpu_map_locked()

        if not wait_until_completed(["P1"], my_run):
            return
        if not smart_sleep(1.2, my_run):
            return
        if not spawn_process_container("P5", 0, "rack-a", "cross-rack", 2.9, sim_mode=sim_mode, run_id=my_run):
            return
        unblock_process_container("P4", sim_mode=sim_mode)
        with STATE_LOCK:
            STATE["stats"]["cross_rack_jobs"] += 1
            STATE["phase_banner"] = "GPU 0 trống -> P5 vào Rack A ghép với P4 ở Rack B: Fine-tune bị Cross-Rack (AllReduce 720ms)!"
            refresh_gpu_map_locked()

        if not wait_until_completed(["P2", "P3"], my_run, mode="all"):
            return
        if not smart_sleep(1.2, my_run):
            return
        if not spawn_process_container("P6", 1, "rack-a", "cross-rack", 2.9, sim_mode=sim_mode, run_id=my_run):
            return
        if not smart_sleep(1.4, my_run):
            return
        if not spawn_process_container("P7", 2, "rack-b", "cross-rack", 2.9, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            STATE["stats"]["cross_rack_jobs"] += 1
            STATE["phase_banner"] = "P6 (Rack A) & P7 (Rack B) cũng bị chia cắt Cross-Rack! P8 vẫn phải chờ lượt cuối."
            refresh_gpu_map_locked()

        freed = wait_any_completed_and_get(["P5", "P4", "P6", "P7"], my_run)
        if not freed:
            return
        if not smart_sleep(1.2, my_run):
            return
        if not spawn_process_container("P8", freed["gpu_id"], freed["rack"], "whole-gpu", 1.5, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            STATE["phase_banner"] = f"P8 (Batch Eval) cuối cùng mới vào được GPU {freed['gpu_id']} sau khi chờ rất lâu."
            refresh_gpu_map_locked()

    elif mode == "proposed":
        with STATE_LOCK:
            STATE["phase_banner"] = "Đề xuất (Kueue + TAS + MIG): Gom 3 job nhỏ vào MIG trên GPU 0, gom nhóm cùng Rack & không khóa GPU!"
            add_log("KUEUE", "[Kịch bản Hỗn hợp] Nhận 8 containers — bật MIG 3-Slice trên GPU 0 và TAS.")
        if not smart_sleep(2.0, my_run):
            return

        for slice_idx, pid in [(1, "P1"), (2, "P2"), (3, "P3")]:
            if not spawn_process_container(pid, 0, "rack-a", "mig", 1.7, mig_slice=slice_idx, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                STATE["phase_banner"] = f"{pid} vào GPU 0 · MIG Slice {slice_idx}/3 — dùng chung 1 GPU thay vì 3 GPU!"
                refresh_gpu_map_locked()
            if not smart_sleep(1.6, my_run):
                return

        for pid, gid in [("P4", 2), ("P5", 3)]:
            if not spawn_process_container(pid, gid, "rack-b", "nvlink", 1.4, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.4, my_run):
                return

        with STATE_LOCK:
            for p in STATE["processes"]:
                if p["pid"] in ("P6", "P7"):
                    p["wait_reason"] = "Kueue Queue: Chờ Rack B trống đủ 2 GPU (0 khóa GPU)"
            STATE["phase_banner"] = "TAS gom P4+P5 vào Rack B (NVLink 60ms). P6, P7 chờ gọn trong Queue (không khóa GPU)!"
            add_log("KUEUE", "Sync-Train (P6+P7) chờ Rack B đủ 2 GPU | Backfill P8 vào GPU 1 (Rack A).")
        if not smart_sleep(1.4, my_run):
            return
        if not spawn_process_container("P8", 1, "rack-a", "whole-gpu", 1.5, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            STATE["phase_banner"] = "Kueue Backfill đưa P8 vào GPU 1 — cả 4/4 GPU đạt ~94% hiệu suất thực, 0 GPU lãng phí!"
            refresh_gpu_map_locked()

        if not wait_until_completed(["P4", "P5"], my_run, mode="all"):
            return
        if not smart_sleep(1.2, my_run):
            return
        for pid, gid in [("P6", 2), ("P7", 3)]:
            if not spawn_process_container(pid, gid, "rack-b", "nvlink", 1.4, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.2, my_run):
                return
        with STATE_LOCK:
            STATE["phase_banner"] = "Rack B vừa trống -> Kueue đưa ngay P6 & P7 vào GPU 2, 3 (NVLink 60ms)!"


def run_inference_burst_scenario(mode, sim_mode, my_run):
    if mode == "baseline":
        with STATE_LOCK:
            STATE["phase_banner"] = "Cách mặc định: 6 service Inference nhỏ không có MIG -> chiếm kín hết cả 4/4 GPU!"
            add_log("K8S-DEF", "[Kịch bản Bùng nổ 6 Inference] 8 containers vào hàng đợi FIFO.")
        if not smart_sleep(2.0, my_run):
            return

        for pid, gid, rack in [("P1", 0, "rack-a"), ("P2", 2, "rack-b"), ("P3", 1, "rack-a"), ("P4", 3, "rack-b")]:
            if not spawn_process_container(pid, gid, rack, "whole-gpu", 1.6, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                STATE["phase_banner"] = f"{pid} chỉ dùng 32% nhưng chiếm trọn GPU {gid}!"
                refresh_gpu_map_locked()
            if not smart_sleep(1.5, my_run):
                return

        with STATE_LOCK:
            mark_pending_locked(("P5", "P6", "P7", "P8"), {})
            STATE["phase_banner"] = "4/4 GPU bị khóa bởi 4 job nhỏ (68% lãng phí mỗi GPU) — P5..P8 kẹt Pending!"
            add_log("WARN", "HẾT GPU: P5, P6 (Infer) và P7, P8 (Train) phải chờ Pending.")
            refresh_gpu_map_locked()

        if not wait_until_completed(["P1"], my_run):
            return
        if not smart_sleep(1.0, my_run):
            return
        if not spawn_process_container("P5", 0, "rack-a", "whole-gpu", 1.6, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            refresh_gpu_map_locked()

        if not wait_until_completed(["P2"], my_run):
            return
        if not smart_sleep(1.0, my_run):
            return
        if not spawn_process_container("P6", 2, "rack-b", "whole-gpu", 1.6, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            refresh_gpu_map_locked()

        if not wait_until_completed(["P3"], my_run):
            return
        if not smart_sleep(1.0, my_run):
            return
        if not spawn_process_container("P7", 1, "rack-a", "cross-rack", 2.8, wait_signal=True, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            STATE["stats"]["deadlock_events"] = 1
            STATE["phase_banner"] = "P7 (Train W1) vào GPU 1 (Rack A) và bị khóa 0% chờ P8!"
            refresh_gpu_map_locked()

        if not wait_until_completed(["P4"], my_run):
            return
        if not smart_sleep(1.0, my_run):
            return
        if not spawn_process_container("P8", 3, "rack-b", "cross-rack", 2.8, sim_mode=sim_mode, run_id=my_run):
            return
        unblock_process_container("P7", sim_mode=sim_mode)
        with STATE_LOCK:
            STATE["stats"]["cross_rack_jobs"] = 1
            STATE["phase_banner"] = "P8 vào GPU 3 (Rack B) -> Train bị rải Cross-Rack (720ms)!"
            refresh_gpu_map_locked()

    elif mode == "proposed":
        with STATE_LOCK:
            STATE["phase_banner"] = "Đề xuất (MIG Đa Phân Vùng + TAS): Gộp 6 Inference vào 2 GPU (GPU 0 & 1), Rack B chạy Train song song!"
            add_log("KUEUE", "[Kịch bản Bùng nổ 6 Inference] Bật MIG 3-Slice trên cả GPU 0 & GPU 1.")
        if not smart_sleep(2.0, my_run):
            return

        for gid, slice_idx, pid in [(0, 1, "P1"), (0, 2, "P2"), (0, 3, "P3"), (1, 1, "P4"), (1, 2, "P5"), (1, 3, "P6")]:
            if not spawn_process_container(pid, gid, "rack-a", "mig", 1.7, mig_slice=slice_idx, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                STATE["phase_banner"] = f"{pid} vào GPU {gid} · MIG Slice {slice_idx}/3 — Rack A gánh trọn 6/6 Inference!"
                refresh_gpu_map_locked()
            if not smart_sleep(1.2, my_run):
                return

        for pid, gid in [("P7", 2), ("P8", 3)]:
            if not spawn_process_container(pid, gid, "rack-b", "nvlink", 1.4, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.2, my_run):
                return
        with STATE_LOCK:
            STATE["phase_banner"] = "Cả 8/8 containers chạy đồng thời (~95% GPU): 0 Pending, 0 Cross-Rack, tiết kiệm 4 GPU!"


def run_gang_deadlock_scenario(mode, sim_mode, my_run):
    if mode == "baseline":
        with STATE_LOCK:
            STATE["phase_banner"] = "Cách mặc định: 2 job nhỏ rải 2 Rack làm 3 Job đa-GPU đều bị cắt Cross-Rack & khóa chết GPU!"
            add_log("K8S-DEF", "[Kịch bản Tranh chấp 3 Job Lớn] 8 containers vào hàng đợi FIFO.")
        if not smart_sleep(2.0, my_run):
            return

        for pid, gid, rack in [("P1", 0, "rack-a"), ("P2", 2, "rack-b")]:
            if not spawn_process_container(pid, gid, rack, "whole-gpu", 1.6, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.5, my_run):
                return

        for pid, gid, rack in [("P3", 1, "rack-a"), ("P4", 3, "rack-b")]:
            if not spawn_process_container(pid, gid, rack, "cross-rack", 2.9, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.4, my_run):
                return

        with STATE_LOCK:
            STATE["stats"]["cross_rack_jobs"] += 1
            mark_pending_locked(("P5", "P6", "P7", "P8"), {})
            STATE["phase_banner"] = "Job A (P3+P4) bị rải Cross-Rack! P5, P6 (Job B) & P7, P8 (Job C) kẹt Pending!"
            refresh_gpu_map_locked()

        if not wait_until_completed(["P1"], my_run):
            return
        if not smart_sleep(1.0, my_run):
            return
        if not spawn_process_container("P5", 0, "rack-a", "cross-rack", 2.9, wait_signal=True, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            STATE["stats"]["deadlock_events"] = 1
            STATE["phase_banner"] = "P5 (Pre-train B1) khóa cứng GPU 0 (0%) chờ P6 đang Pending!"
            refresh_gpu_map_locked()

        if not wait_until_completed(["P2"], my_run):
            return
        if not smart_sleep(1.0, my_run):
            return
        if not spawn_process_container("P6", 2, "rack-b", "cross-rack", 2.9, sim_mode=sim_mode, run_id=my_run):
            return
        unblock_process_container("P5", sim_mode=sim_mode)
        with STATE_LOCK:
            STATE["stats"]["cross_rack_jobs"] += 1
            STATE["phase_banner"] = "Job B (P5+P6) lại chạy Cross-Rack qua GPU 0 & GPU 2!"
            refresh_gpu_map_locked()

        if not wait_until_completed(["P3", "P4"], my_run, mode="all"):
            return
        if not smart_sleep(1.0, my_run):
            return
        if not spawn_process_container("P7", 1, "rack-a", "cross-rack", 2.9, sim_mode=sim_mode, run_id=my_run):
            return
        if not smart_sleep(1.2, my_run):
            return
        if not spawn_process_container("P8", 3, "rack-b", "cross-rack", 2.9, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            STATE["stats"]["cross_rack_jobs"] += 1
            STATE["phase_banner"] = "Cả 3/3 Job lớn (A, B, C) đều bị rải Cross-Rack chậm 720ms!"
            refresh_gpu_map_locked()

    elif mode == "proposed":
        with STATE_LOCK:
            STATE["phase_banner"] = "Đề xuất: MIG gom P1+P2 vào GPU 0 -> TAS giữ trọn từng Rack cho cả 3 Job lớn (100% NVLink)!"
            add_log("KUEUE", "[Kịch bản Tranh chấp 3 Job Lớn] Gom P1+P2 vào GPU 0, chạy 3 Job lớn theo chuẩn Rack.")
        if not smart_sleep(2.0, my_run):
            return

        for slice_idx, pid in [(1, "P1"), (2, "P2")]:
            if not spawn_process_container(pid, 0, "rack-a", "mig", 1.7, mig_slice=slice_idx, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.3, my_run):
                return

        for pid, gid in [("P3", 2), ("P4", 3)]:
            if not spawn_process_container(pid, gid, "rack-b", "nvlink", 1.4, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.2, my_run):
                return

        with STATE_LOCK:
            for p in STATE["processes"]:
                if p["pid"] in ("P5", "P6", "P7", "P8"):
                    p["wait_reason"] = "Kueue Queue: Chờ đủ 2 GPU cùng Rack (0 khóa GPU)"
            STATE["phase_banner"] = "Job A chạy NVLink trên Rack B! Job B & C chờ gọn trong Queue (0 khóa GPU)."

        if not wait_until_completed(["P3", "P4"], my_run, mode="all"):
            return
        if not smart_sleep(1.0, my_run):
            return
        for pid, gid in [("P5", 2), ("P6", 3)]:
            if not spawn_process_container(pid, gid, "rack-b", "nvlink", 1.4, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.0, my_run):
                return
        with STATE_LOCK:
            STATE["phase_banner"] = "Job B vào Rack B (NVLink 60ms)! Chờ GPU 0 xong MIG để Job C lấy trọn Rack A."

        if not wait_until_completed(["P1", "P2"], my_run, mode="all"):
            return
        if not smart_sleep(1.0, my_run):
            return
        for pid, gid in [("P7", 0), ("P8", 1)]:
            if not spawn_process_container(pid, gid, "rack-a", "nvlink", 1.4, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.0, my_run):
                return
        with STATE_LOCK:
            STATE["phase_banner"] = "Job B (Rack B) & Job C (Rack A) chạy song song 100% NVLink — 0 Cross-Rack!"


def run_backfill_fair_scenario(mode, sim_mode, my_run):
    if mode == "baseline":
        with STATE_LOCK:
            STATE["phase_banner"] = "Cách mặc định (FIFO): 3 Job lớn chen kín & rải Cross-Rack, 2 Job nhỏ tương tác bị bỏ đói tới cuối!"
            add_log("K8S-DEF", "[Kịch bản Chống đói Job Nhỏ] 3 Train lớn đến trước, 2 Job nhỏ đến sau.")
        if not smart_sleep(2.0, my_run):
            return

        for pid, gid, rack in [("P1", 0, "rack-a"), ("P2", 2, "rack-b"), ("P3", 1, "rack-a"), ("P4", 3, "rack-b")]:
            if not spawn_process_container(pid, gid, rack, "cross-rack", 2.7, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.3, my_run):
                return

        with STATE_LOCK:
            STATE["stats"]["cross_rack_jobs"] += 2
            mark_pending_locked(("P5", "P6", "P7", "P8"), {"P7": "Pending: Chết đói sau 3 Job lớn!", "P8": "Pending: Chết đói sau 3 Job lớn!"})
            STATE["phase_banner"] = "Train A & B đều bị Cross-Rack! Train C và 2 Job nhỏ (P7, P8) bị kẹt Pending."
            refresh_gpu_map_locked()

        if not wait_until_completed(["P1"], my_run):
            return
        if not smart_sleep(1.0, my_run):
            return
        if not spawn_process_container("P5", 0, "rack-a", "cross-rack", 2.7, wait_signal=True, sim_mode=sim_mode, run_id=my_run):
            return
        with STATE_LOCK:
            STATE["stats"]["deadlock_events"] = 1
            STATE["phase_banner"] = "P5 (Train C1) chiếm GPU 0 và khóa 0% chờ P6 — P7, P8 vẫn bị bỏ đói!"
            refresh_gpu_map_locked()

        if not wait_until_completed(["P2"], my_run):
            return
        if not smart_sleep(1.0, my_run):
            return
        if not spawn_process_container("P6", 2, "rack-b", "cross-rack", 2.7, sim_mode=sim_mode, run_id=my_run):
            return
        unblock_process_container("P5", sim_mode=sim_mode)
        with STATE_LOCK:
            STATE["stats"]["cross_rack_jobs"] += 1
            refresh_gpu_map_locked()

        if not wait_until_completed(["P3", "P4"], my_run, mode="all"):
            return
        if not smart_sleep(1.0, my_run):
            return
        for pid, gid, rack in [("P7", 1, "rack-a"), ("P8", 3, "rack-b")]:
            if not spawn_process_container(pid, gid, rack, "whole-gpu", 1.6, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.2, my_run):
                return
        with STATE_LOCK:
            STATE["phase_banner"] = "Đến tận lượt cuối P7 & P8 mới chạy được — và lại chiếm nguyên 2 GPU!"

    elif mode == "proposed":
        with STATE_LOCK:
            STATE["phase_banner"] = "Đề xuất (Kueue + TAS + MIG): Train A & B chạy NVLink nội Rack, Job nhỏ được ưu tiên vào MIG ngay khi Rack A trống!"
            add_log("KUEUE", "[Kịch bản Chống đói Job Nhỏ] Gom Train A (Rack A) & Train B (Rack B) 100% NVLink.")
        if not smart_sleep(2.0, my_run):
            return

        for pid, gid, rack in [("P1", 0, "rack-a"), ("P2", 1, "rack-a"), ("P3", 2, "rack-b"), ("P4", 3, "rack-b")]:
            if not spawn_process_container(pid, gid, rack, "nvlink", 1.4, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.2, my_run):
                return

        with STATE_LOCK:
            for p in STATE["processes"]:
                if p["pid"] in ("P5", "P6", "P7", "P8"):
                    p["wait_reason"] = "Kueue Queue: Chờ Rack trống (không giữ GPU dở dang)"
            STATE["phase_banner"] = "Train A (Rack A) & Train B (Rack B) chạy 100% NVLink 60ms (~94% GPU)!"

        if not wait_until_completed(["P1", "P2"], my_run, mode="all"):
            return
        if not smart_sleep(1.0, my_run):
            return
        for slice_idx, pid in [(1, "P7"), (2, "P8")]:
            if not spawn_process_container(pid, 0, "rack-a", "mig", 1.6, mig_slice=slice_idx, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.0, my_run):
                return
        with STATE_LOCK:
            STATE["phase_banner"] = "Rack A vừa trống -> Kueue đưa ngay 2 Job nhỏ P7 & P8 vào GPU 0 (MIG 2-Slice), không bị chết đói!"

        if not wait_until_completed(["P3", "P4"], my_run, mode="all"):
            return
        if not smart_sleep(1.0, my_run):
            return
        for pid, gid in [("P5", 2), ("P6", 3)]:
            if not spawn_process_container(pid, gid, "rack-b", "nvlink", 1.4, sim_mode=sim_mode, run_id=my_run):
                return
            with STATE_LOCK:
                refresh_gpu_map_locked()
            if not smart_sleep(1.0, my_run):
                return
        with STATE_LOCK:
            STATE["phase_banner"] = "Train C (P5+P6) vào Rack B (NVLink) đồng thời GPU 1 vẫn dư trống cho tác vụ mới!"


def start_scenario(mode, sim_mode=False, scenario_id=None):
    with STATE_LOCK:
        STATE["run_id"] += 1
        my_run = STATE["run_id"]
        if scenario_id and scenario_id in SCENARIOS:
            STATE["scenario"] = scenario_id
        active_sc = STATE["scenario"]
        STATE["paused"] = False
        PAUSE_EVENT.set()
        STATE["phase_banner"] = "Đang chuẩn bị 8 containers..."

    cleanup_containers()
    if not is_run_active(my_run):
        return

    if not sim_mode:
        rc, _, err = run_cmd(["docker", "info"], timeout=8)
        if rc != 0:
            with STATE_LOCK:
                if STATE["run_id"] == my_run:
                    STATE["docker_ok"] = False
                    STATE["docker_error"] = err or "Docker Desktop chưa chạy. Hãy bật Docker Desktop hoặc dùng chế độ Mô phỏng."
            return
        rc_img, _, _ = run_cmd(["docker", "image", "inspect", IMAGE_NAME], timeout=8)
        if rc_img != 0:
            with STATE_LOCK:
                if STATE["run_id"] == my_run:
                    STATE["phase_banner"] = f"Đang build Docker image {IMAGE_NAME} lần đầu..."
            rc_b, _, err_b = run_cmd(["docker", "build", "-t", IMAGE_NAME, "."], timeout=120)
            if rc_b != 0:
                with STATE_LOCK:
                    if STATE["run_id"] == my_run:
                        STATE["docker_ok"] = False
                        STATE["docker_error"] = f"Build image thất bại: {err_b}"
                return
        if not is_run_active(my_run):
            return

    sc_cfg = SCENARIOS[active_sc]
    with STATE_LOCK:
        if STATE["run_id"] != my_run:
            return
        STATE["docker_ok"] = True
        STATE["docker_error"] = ""
        STATE["mode"] = mode
        STATE["sim_mode"] = sim_mode
        STATE["running"] = True
        STATE["paused"] = False
        PAUSE_EVENT.set()
        STATE["accumulated_s"] = 0.0
        STATE["last_resumed_at"] = time.time()
        STATE["gpus"] = init_gpus(active_sc, mode)
        STATE["processes"] = init_processes(active_sc, mode)
        STATE["logs"] = []
        STATE["stats"] = {
            "util_sum": 0.0,
            "util_samples": 0,
            "peak_waiting": 0,
            "deadlock_events": 0,
            "cross_rack_jobs": 0,
            "mig_gpus_saved": sc_cfg["mig_saved"] if mode == "proposed" else 0,
        }

    if active_sc == "mixed":
        run_mixed_scenario(mode, sim_mode, my_run)
    elif active_sc == "inference_burst":
        run_inference_burst_scenario(mode, sim_mode, my_run)
    elif active_sc == "gang_deadlock":
        run_gang_deadlock_scenario(mode, sim_mode, my_run)
    elif active_sc == "backfill_fair":
        run_backfill_fair_scenario(mode, sim_mode, my_run)


def set_paused(want_pause):
    with STATE_LOCK:
        if not STATE["running"]:
            return {"running": False, "paused": False}
        if want_pause == STATE["paused"]:
            return {"running": STATE["running"], "paused": STATE["paused"]}
        sim_mode = STATE["sim_mode"]
        active_names = [
            p["name"] for p in STATE["processes"]
            if p["state"] in ("running", "blocked")
        ]
        if want_pause:
            STATE["accumulated_s"] = get_elapsed_locked()
            STATE["paused"] = True
            PAUSE_EVENT.clear()
            add_log("PAUSE", "Đã tạm dừng toàn bộ containers & bộ đếm thời gian.")

    if want_pause:
        if not sim_mode and active_names:
            run_cmd(["docker", "pause"] + active_names, timeout=10)
    else:
        if not sim_mode and active_names:
            run_cmd(["docker", "unpause"] + active_names, timeout=10)
        with STATE_LOCK:
            if STATE["running"]:
                now = time.time()
                if sim_mode:
                    for w in MOCK_WORKERS.values():
                        w["last_tick"] = now
                STATE["last_resumed_at"] = now
                STATE["paused"] = False
                PAUSE_EVENT.set()
                add_log("RESUME", "Tiếp tục thực thi từ trạng thái tạm dừng.")

    with STATE_LOCK:
        return {"running": STATE["running"], "paused": STATE["paused"]}


def poll_loop():
    """Background loop updating process progress from real Docker containers (or mock workers)."""
    pct_re = re.compile(r"\((\d+)%\)")
    while True:
        time.sleep(0.55)
        with STATE_LOCK:
            if not STATE["running"]:
                continue
            if STATE["paused"]:
                PAUSE_EVENT.wait(timeout=0.3)
                continue
            sim_mode = STATE["sim_mode"]
            run_id = STATE["run_id"]
            mode = STATE["mode"]
            active_procs = [dict(p) for p in STATE["processes"] if p["state"] in ("running", "blocked")]

        if sim_mode:
            now = time.time()
            updates = {}
            with STATE_LOCK:
                if STATE["run_id"] != run_id or STATE["paused"]:
                    continue
                for p in active_procs:
                    cname = p["name"]
                    w = MOCK_WORKERS.get(cname)
                    if not w:
                        continue
                    if w["blocked"]:
                        elapsed_b = int(now - w["last_tick"])
                        updates[cname] = ("blocked", 0, f"[{p['cid']}] BLOCKED (0%): Giữ cứng GPU chờ peer... ({elapsed_b}s)")
                    else:
                        if now - w["last_tick"] >= w["step_pause"]:
                            steps_adv = int((now - w["last_tick"]) / w["step_pause"])
                            w["last_tick"] += steps_adv * w["step_pause"]
                            w["step"] = min(w["steps"], w["step"] + steps_adv)
                            w["progress"] = min(100, int(w["step"] * 100 / w["steps"]))
                            sync_msg = (
                                f"AllReduce({w['link_mode']})={'60ms' if w['link_mode']=='nvlink' else '720ms'}"
                                if w["role"] in ("finetune", "train")
                                else f"mode={w['link_mode']}"
                            )
                            w["last_line"] = f"[{p['cid']}] Step {w['step']}/{w['steps']} ({w['progress']}%) | {sync_msg}"
                            if w["step"] >= w["steps"]:
                                w["done"] = True
                                w["last_line"] = f"[{p['cid']}] DONE job={cname}"
                        st_str = "completed" if w["done"] else "running"
                        updates[cname] = (st_str, w["progress"], w["last_line"])
        else:
            if not active_procs:
                updates = {}
            else:
                rc, ps_out, _ = run_cmd([
                    "docker", "ps", "-a",
                    "--filter", f"label={LABEL_KEY}",
                    "--format", "{{.Names}}|{{.State}}",
                ], timeout=8)
                state_map = {}
                if rc == 0 and ps_out:
                    for line in ps_out.splitlines():
                        if "|" in line:
                            n, st = line.split("|", 1)
                            state_map[n.strip()] = st.strip()

                updates = {}
                for p in active_procs:
                    cname = p["name"]
                    st = state_map.get(cname, "exited")
                    _, log_out, _ = run_cmd(["docker", "logs", "--tail", "1", cname], timeout=5)
                    last_line = log_out.splitlines()[-1] if log_out else p["last_line"]
                    prog = p["progress"]
                    m = pct_re.search(last_line)
                    if m:
                        prog = int(m.group(1))
                    if st == "paused":
                        continue
                    if st != "running":
                        st_str = "completed"
                        prog = 100
                    elif p["state"] == "blocked" and "UNBLOCKED" not in last_line and "Step " not in last_line:
                        st_str = "blocked"
                        prog = 0
                    else:
                        st_str = "running"
                    updates[cname] = (st_str, prog, last_line)

        with STATE_LOCK:
            if STATE["run_id"] != run_id or STATE["paused"] or not STATE["running"]:
                continue

            for p in STATE["processes"]:
                if p["name"] in updates:
                    st_str, prog, last_line = updates[p["name"]]
                    p["state"] = st_str
                    p["progress"] = prog
                    p["last_line"] = last_line
                    if st_str == "completed":
                        p["wait_reason"] = ""

            refresh_gpu_map_locked()

            # Sample average cluster utilization across all 4 GPUs once execution begins
            if any(p["state"] in ("running", "blocked", "completed") for p in STATE["processes"]):
                avg_gpu_now = sum(g["used_pct"] for g in STATE["gpus"]) / 4.0
                STATE["stats"]["util_sum"] += avg_gpu_now
                STATE["stats"]["util_samples"] += 1

            all_done = all(p["state"] == "completed" for p in STATE["processes"])
            if all_done:
                elapsed = round(get_elapsed_locked(), 1)
                STATE["accumulated_s"] = elapsed
                STATE["running"] = False
                STATE["paused"] = False
                samples = max(1, STATE["stats"]["util_samples"])
                avg_util = round(STATE["stats"]["util_sum"] / samples)
                sc_id = STATE["scenario"]
                STATE["phase_banner"] = (
                    f"Hoàn tất 8/8 containers ({'Cách mặc định' if mode == 'baseline' else 'Đề xuất Kueue + TAS + MIG'}) trong {elapsed:.1f}s · Hiệu suất GPU TB: {avg_util}%!"
                )
                STATE["benchmarks"][sc_id][mode] = {
                    "elapsed_s": elapsed,
                    "done_count": "8 / 8 Containers",
                    "avg_util": avg_util,
                    "peak_waiting": STATE["stats"]["peak_waiting"],
                    "deadlocks": STATE["stats"]["deadlock_events"],
                    "cross_rack": STATE["stats"]["cross_rack_jobs"],
                    "mig_saved": STATE["stats"]["mig_gpus_saved"],
                    "allreduce": "720ms (Liên Rack)" if mode == "baseline" else "60ms (NVLink nội bộ)",
                }
                add_log("BENCH", f"HOÀN TẤT [{sc_id}] {mode.upper()}: {elapsed:.1f}s | Hiệu suất GPU TB = {avg_util}% | Cross-Rack = {STATE['stats']['cross_rack_jobs']}")


HTML_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Live 8-Container GPU Scheduler Demo</title>
  <style>
    :root {
      --bg: #f4f7fb;
      --card: #ffffff;
      --ink: #0f172a;
      --muted: #64748b;
      --line: #e2e8f0;
      --teal: #0d9488;
      --teal-soft: #ccfbf1;
      --blue: #2563eb;
      --blue-soft: #dbeafe;
      --amber: #d97706;
      --amber-soft: #fef3c7;
      --rose: #e11d48;
      --rose-soft: #ffe4e6;
      --indigo: #4f46e5;
      --sky: #0284c7;
      --shadow: 0 4px 20px rgba(15, 23, 42, .05);
      --ease: cubic-bezier(0.22, 1, 0.36, 1);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--ink);
      -webkit-font-smoothing: antialiased;
    }

    /* Top Header */
    .topbar {
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 12px 24px;
      position: sticky;
      top: 0;
      z-index: 20;
      box-shadow: 0 2px 12px rgba(15, 23, 42, .04);
    }
    .topbar-in {
      max-width: 1280px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .brand h1 {
      margin: 0;
      font-size: 17px;
      font-weight: 800;
      letter-spacing: -.2px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .brand .sub {
      font-size: 12px;
      color: var(--muted);
      margin-top: 2px;
    }
    .mode-pill {
      font-size: 10.5px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 999px;
      background: #f1f5f9;
      color: #475569;
    }
    .mode-pill.sim { background: var(--amber-soft); color: #92400e; }
    .mode-pill.real { background: var(--teal-soft); color: #115e59; }

    .controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    button {
      border: 1px solid transparent;
      border-radius: 10px;
      padding: 9px 14px;
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: transform .15s var(--ease), opacity .15s ease, background-color .2s ease, box-shadow .2s ease;
    }
    button:active { transform: scale(.97); }
    button:disabled { opacity: .45; cursor: not-allowed; transform: none; }
    .btn-base { background: var(--rose); color: #fff; box-shadow: 0 2px 8px rgba(225,29,72,.22); }
    .btn-base:hover:not(:disabled) { background: #be123c; }
    .btn-prop { background: var(--teal); color: #fff; box-shadow: 0 2px 8px rgba(13,148,136,.24); }
    .btn-prop:hover:not(:disabled) { background: #0f766e; }
    .btn-pause { background: #f59e0b; color: #fff; }
    .btn-pause.is-paused { background: var(--blue); }
    .btn-reset { background: #f8fafc; color: #475569; border-color: var(--line); }
    .btn-reset:hover:not(:disabled) { background: #f1f5f9; }

    /* Container */
    .wrap {
      max-width: 1280px;
      margin: 16px auto 32px;
      padding: 0 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    /* Alert */
    .err-banner {
      display: none;
      background: #fff1f2;
      border: 1px solid #fecdd3;
      color: #9f1239;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 12.5px;
      font-weight: 600;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .err-banner.show { display: flex; }

    /* Status & KPI Strip */
    .status-strip {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 16px;
      box-shadow: var(--shadow);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
    }
    .status-left {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1 1 420px;
      min-width: 0;
    }
    .state-badge {
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .4px;
      white-space: nowrap;
      background: #f1f5f9;
      color: #475569;
    }
    .state-badge.run { background: var(--teal-soft); color: #0f766e; }
    .state-badge.run-base { background: var(--rose-soft); color: #be123c; }
    .state-badge.paused { background: var(--amber-soft); color: #b45309; }
    .state-badge.done { background: var(--blue-soft); color: #1d4ed8; }
    .banner-text {
      font-size: 13px;
      font-weight: 600;
      color: var(--ink);
      line-height: 1.35;
    }
    .mini-kpis {
      display: flex;
      flex-wrap: wrap;
      gap: 18px;
      align-items: center;
    }
    .mk { text-align: right; }
    .mk .l { font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--muted); letter-spacing: .4px; }
    .mk .v { font-size: 18px; font-weight: 800; font-variant-numeric: tabular-nums; margin-top: 1px; }

    /* Main 2-Column Stage */
    .stage {
      display: grid;
      grid-template-columns: 390px 1fr;
      gap: 14px;
      align-items: start;
    }
    @media (max-width: 1020px) { .stage { grid-template-columns: 1fr; } }

    .panel {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 15px;
      box-shadow: var(--shadow);
    }
    .panel-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 11px;
      gap: 8px;
    }
    .panel-head h2 {
      margin: 0;
      font-size: 12.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .5px;
      color: #334155;
    }
    .waiting-summary {
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 999px;
      background: #f1f5f9;
      color: var(--muted);
      transition: all .25s ease;
    }
    .waiting-summary.has-wait { background: var(--amber-soft); color: #b45309; }
    .waiting-summary.has-pend { background: var(--rose-soft); color: #be123c; }
    .waiting-summary.clear { background: var(--teal-soft); color: #0f766e; }

    /* Process Rows (Left Column) */
    .proc-list { display: flex; flex-direction: column; gap: 7px; }
    .proc-row {
      border: 1px solid var(--line);
      border-left: 4px solid #cbd5e1;
      border-radius: 11px;
      padding: 8px 10px;
      background: #f8fafc;
      transition: background-color .35s var(--ease), border-color .35s var(--ease), opacity .35s ease;
    }
    .proc-row.st-waiting { border-left-color: var(--amber); background: #fffbeb; }
    .proc-row.st-pending { border-left-color: var(--rose); background: #fff1f2; }
    .proc-row.st-blocked { border-left-color: var(--rose); background: #ffe4e6; }
    .proc-row.st-running { border-left-color: var(--teal); background: #f0fdfa; }
    .proc-row.st-completed { border-left-color: #94a3b8; background: #f8fafc; opacity: .78; }

    .proc-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 6px;
    }
    .proc-name {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12.5px;
      font-weight: 700;
      min-width: 0;
    }
    .pid-tag {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 26px;
      height: 20px;
      border-radius: 6px;
      font-size: 10.5px;
      font-weight: 800;
      background: #e2e8f0;
      color: #1e293b;
      flex-shrink: 0;
    }
    .st-running .pid-tag { background: var(--teal); color: #fff; }
    .st-waiting .pid-tag { background: var(--amber); color: #fff; }
    .st-pending .pid-tag, .st-blocked .pid-tag { background: var(--rose); color: #fff; }
    .st-completed .pid-tag { background: #64748b; color: #fff; }

    .proc-badge {
      font-size: 10.5px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 999px;
      white-space: nowrap;
      background: #e2e8f0;
      color: #334155;
    }
    .pb-wait { background: var(--amber-soft); color: #b45309; }
    .pb-pend, .pb-blk { background: var(--rose-soft); color: #be123c; }
    .pb-run { background: var(--teal-soft); color: #0f766e; }
    .pb-done { background: #e2e8f0; color: #475569; }

    .proc-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 6px;
      margin-top: 4px;
      font-size: 11px;
      color: var(--muted);
    }
    .proc-reason {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .pbar {
      height: 4px;
      background: rgba(148, 163, 184, .25);
      border-radius: 999px;
      overflow: hidden;
      margin-top: 5px;
    }
    .pbar-fill {
      height: 100%;
      width: 0%;
      background: var(--teal);
      border-radius: 999px;
      transition: width .55s var(--ease), background-color .3s ease;
    }
    .st-blocked .pbar-fill, .st-pending .pbar-fill { background: var(--rose); }
    .st-completed .pbar-fill { background: #64748b; }

    /* Right Column: 2 Racks & 4 GPUs */
    .cross-alert {
      display: none;
      margin-bottom: 10px;
      padding: 7px 11px;
      border-radius: 10px;
      background: #fff7ed;
      border: 1px dashed #fb923c;
      color: #c2410c;
      font-size: 11.5px;
      font-weight: 700;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .cross-alert.show { display: flex; }

    .racks {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    @media (max-width: 720px) { .racks { grid-template-columns: 1fr; } }

    .rack-box {
      border: 1.5px dashed #cbd5e1;
      border-radius: 14px;
      padding: 11px;
      background: #f8fafc;
    }
    .rack-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      font-size: 12px;
      font-weight: 800;
      color: #1e293b;
    }
    .nv-tag {
      font-size: 10px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--blue-soft);
      color: #1d4ed8;
    }
    .gpu-stack { display: flex; flex-direction: column; gap: 10px; }

    .gpu-card {
      background: #ffffff;
      border: 1.5px solid var(--line);
      border-radius: 12px;
      padding: 11px;
      min-height: 158px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 8px;
      transition: border-color .35s var(--ease), background-color .35s var(--ease), box-shadow .35s ease;
    }
    .gpu-card.g-active { border-color: var(--teal); box-shadow: 0 3px 12px rgba(13,148,136,.09); }
    .gpu-card.g-cross { border-color: #f97316; background: #fffbf7; }
    .gpu-card.g-blocked { border-color: var(--rose); background: #fff5f6; }
    .gpu-card.g-waste { border-color: #fca5a5; }

    .gpu-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 6px;
    }
    .gpu-title { font-size: 12.5px; font-weight: 800; color: var(--ink); display: flex; align-items: center; gap: 6px; }
    .mig-tag { font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 999px; background: #e0e7ff; color: #3730a3; }
    .gpu-pct { font-size: 12px; font-weight: 800; font-variant-numeric: tabular-nums; color: var(--muted); }

    /* Visual Partition Meter inside GPU Card */
    .part-meter {
      height: 12px;
      border-radius: 7px;
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      overflow: hidden;
      display: flex;
    }
    .pm-seg {
      height: 100%;
      width: 0%;
      transition: width .55s var(--ease);
    }
    .pm-s1 { background: var(--teal); }
    .pm-s2 { background: var(--indigo); }
    .pm-s3 { background: var(--sky); }
    .pm-cross { background: #f97316; }
    .pm-waste {
      background: repeating-linear-gradient(
        -45deg,
        #fecdd3,
        #fecdd3 5px,
        #ffe4e6 5px,
        #ffe4e6 10px
      );
    }

    /* Slot rows inside GPU Card */
    .gpu-slots {
      display: flex;
      flex-direction: column;
      gap: 5px;
      min-height: 76px;
      justify-content: center;
    }
    .slot-empty {
      border: 1px dashed #cbd5e1;
      border-radius: 8px;
      padding: 14px 8px;
      text-align: center;
      font-size: 11.5px;
      color: #94a3b8;
      font-weight: 600;
    }
    .slot-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 5px 8px;
      border-radius: 8px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      font-size: 11.5px;
      transition: all .3s var(--ease);
    }
    .slot-row.s1 { border-left: 4px solid var(--teal); background: #f0fdfa; }
    .slot-row.s2 { border-left: 4px solid var(--indigo); background: #eef2ff; }
    .slot-row.s3 { border-left: 4px solid var(--sky); background: #f0f9ff; }
    .slot-row.scross { border-left: 4px solid #f97316; background: #fff7ed; }
    .slot-row.sblk { border-left: 4px solid var(--rose); background: #ffe4e6; color: #9f1239; }
    .slot-row.swaste {
      border: 1px dashed #fda4af;
      background: repeating-linear-gradient(-45deg, #fff1f2, #fff1f2 6px, #ffe4e6 6px, #ffe4e6 12px);
      color: #be123c;
      font-weight: 600;
      font-size: 11px;
    }
    .slot-row.smig-free {
      border: 1px dashed #cbd5e1;
      background: #fafafa;
      color: #94a3b8;
      font-size: 11px;
    }
    .cid-mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 10px;
      color: var(--muted);
    }

    /* Comparison Section */
    .verdict {
      display: none;
      margin-bottom: 12px;
      padding: 11px 14px;
      border-radius: 12px;
      background: linear-gradient(135deg, #ecfdf5, #f0fdfa);
      border: 1px solid #99f6e4;
      color: #115e59;
      font-size: 13px;
      font-weight: 700;
    }
    .verdict.show { display: block; }

    table.cmp {
      width: 100%;
      border-collapse: collapse;
      font-size: 12.5px;
    }
    table.cmp th, table.cmp td {
      padding: 9px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
    }
    table.cmp th {
      font-size: 11.5px;
      text-transform: uppercase;
      letter-spacing: .3px;
      color: var(--muted);
      background: #f8fafc;
    }
    table.cmp tr:last-child td { border-bottom: 0; }
    .win-val { color: var(--teal); font-weight: 800; }
    .bad-val { color: var(--rose); font-weight: 700; }

    /* Collapsible Logs */
    details.log-drawer {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 10px 15px;
      box-shadow: var(--shadow);
    }
    details.log-drawer summary {
      cursor: pointer;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .4px;
      color: #475569;
      user-select: none;
    }
    .term {
      margin-top: 10px;
      background: #0f172a;
      color: #e2e8f0;
      border-radius: 10px;
      padding: 11px 13px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11.5px;
      height: 150px;
      overflow-y: auto;
      line-height: 1.5;
    }

    /* Scenario Selector Tabs */
    .sc-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 8px 12px;
      box-shadow: var(--shadow);
    }
    .sc-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .sc-tab {
      background: #f8fafc;
      color: #475569;
      border: 1px solid var(--line);
      border-radius: 9px;
      padding: 7px 12px;
      font-size: 12px;
      font-weight: 700;
    }
    .sc-tab:hover { background: #f1f5f9; }
    .sc-tab.active {
      background: #0f172a;
      color: #ffffff;
      border-color: #0f172a;
    }
    .sc-dot {
      display: inline-block;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #cbd5e1;
    }
    .sc-dot.both { background: var(--teal); }
    .sc-dot.one { background: var(--amber); }
    .sc-desc {
      font-size: 12px;
      color: var(--muted);
      font-weight: 600;
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-in">
      <div class="brand">
        <h1>
          GPU Resource Scheduler Demo
          <span id="execModePill" class="mode-pill">Docker 8 Containers</span>
        </h1>
        <div class="sub">So sánh trực quan 8 containers trên 4 GPU (2 Rack): Mặc định K8s vs Đề xuất (Kueue + TAS + MIG)</div>
      </div>
      <div class="controls">
        <button id="btnBase" class="btn-base" onclick="startRun('baseline')">▶ 1. Cách Mặc Định</button>
        <button id="btnProp" class="btn-prop" onclick="startRun('proposed')">▶ 2. Cách Đề Xuất</button>
        <button id="btnPause" class="btn-pause" onclick="togglePause()" disabled>⏸ Tạm dừng</button>
        <button id="btnReset" class="btn-reset" onclick="resetDemo()">↺ Đặt lại</button>
      </div>
    </div>
  </header>

  <main class="wrap">
    <div id="errBanner" class="err-banner">
      <span id="errText"></span>
      <button class="btn-prop" style="padding:6px 12px; font-size:11.5px;" onclick="startSimFallback()">Chạy thử Mô phỏng (Preview UI)</button>
    </div>

    <section class="sc-bar">
      <div id="scTabs" class="sc-tabs"></div>
      <div id="scDesc" class="sc-desc"></div>
    </section>

    <section class="status-strip">
      <div class="status-left">
        <span id="stateBadge" class="state-badge">Sẵn sàng</span>
        <div id="phaseBanner" class="banner-text">Bấm nút 1 hoặc 2 để quan sát chậm từng container vào chiếm phần GPU và hàng đợi.</div>
      </div>
      <div class="mini-kpis">
        <div class="mk"><div class="l">Hoàn thành</div><div class="v" id="kDone" style="color:var(--ink)">0 / 8</div></div>
        <div class="mk"><div class="l">Đang chờ</div><div class="v" id="kWait" style="color:var(--amber)">0</div></div>
        <div class="mk"><div class="l">Hiệu suất GPU</div><div class="v" id="kUtil" style="color:var(--teal)">0%</div></div>
        <div class="mk"><div class="l">Thời gian</div><div class="v" id="kTime" style="color:var(--blue)">0.0s</div></div>
      </div>
    </section>

    <section class="stage">
      <!-- Left: Fixed 8 Processes (Waiting vs Running vs Completed) -->
      <div class="panel">
        <div class="panel-head">
          <h2>1. Tiến trình 8 Containers</h2>
          <span id="waitingSummary" class="waiting-summary">Chờ khởi chạy</span>
        </div>
        <div id="procList" class="proc-list"></div>
      </div>

      <!-- Right: 2 Racks / 4 GPUs with proportional visual GPU occupancy -->
      <div class="panel">
        <div class="panel-head">
          <h2>2. Phân bổ GPU &amp; Phần GPU bị chiếm (2 Rack · 4 GPU)</h2>
          <span id="gpuSummary" class="waiting-summary">4 GPU sẵn sàng</span>
        </div>
        <div id="crossAlert" class="cross-alert">
          ⚡ Cảnh báo Cross-Rack: Container đang truyền AllReduce qua mạng giữa Rack A &amp; Rack B (chậm 720ms)
        </div>
        <div class="racks">
          <div class="rack-box">
            <div class="rack-head">
              <span>RACK A (GPU 0 &amp; GPU 1)</span>
              <span class="nv-tag">NVLink 60ms</span>
            </div>
            <div class="gpu-stack" id="rackACards"></div>
          </div>
          <div class="rack-box">
            <div class="rack-head">
              <span>RACK B (GPU 2 &amp; GPU 3)</span>
              <span class="nv-tag">NVLink 60ms</span>
            </div>
            <div class="gpu-stack" id="rackBCards"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- Comparison Table -->
    <section class="panel">
      <div class="panel-head" style="margin-bottom:8px;">
        <h2>3. Kết quả đối chiếu quản lý tài nguyên (8 Containers)</h2>
      </div>
      <div id="verdictBox" class="verdict"></div>
      <table class="cmp">
        <thead>
          <tr>
            <th>Chỉ số đánh giá (Đo thực tế trên cùng 8 containers)</th>
            <th style="color:var(--rose)">1. Cách mặc định (K8s FIFO)</th>
            <th style="color:var(--teal)">2. Cách đề xuất (Kueue + TAS + MIG)</th>
          </tr>
        </thead>
        <tbody id="benchBody">
          <tr><td><strong>Tổng thời gian hoàn tất 8/8 containers</strong></td><td id="bTime">—</td><td id="pTime">—</td></tr>
          <tr><td><strong>Hiệu suất sử dụng GPU trung bình</strong></td><td id="bUtil">—</td><td id="pUtil">—</td></tr>
          <tr><td><strong>Số GPU bị khóa chết 0% (Deadlock)</strong></td><td id="bDead">—</td><td id="pDead">—</td></tr>
          <tr><td><strong>Số container bị kẹt Pending (hết GPU)</strong></td><td id="bWait">—</td><td id="pWait">—</td></tr>
          <tr><td><strong>Số job đa-GPU bị rải Cross-Rack chậm</strong></td><td id="bCross">—</td><td id="pCross">—</td></tr>
          <tr><td><strong>Tiết kiệm GPU nhờ chia sẻ MIG</strong></td><td id="bMig">—</td><td id="pMig">—</td></tr>
        </tbody>
      </table>
    </section>

    <!-- Collapsible Docker Logs -->
    <details class="log-drawer">
      <summary>Nhật ký Docker &amp; Bộ lập lịch chi tiết (Bấm để mở/thu gọn)</summary>
      <div id="termBox" class="term">Sẵn sàng khởi chạy 8 containers...</div>
    </details>
  </main>

  <script>
    const PIDS = ['P1','P2','P3','P4','P5','P6','P7','P8'];
    let lastRequestedMode = 'proposed';
    let lastState = null;
    let clientClockBase = 0;
    let clientClockStamp = performance.now();

    function buildShells() {
      const procList = document.getElementById('procList');
      procList.innerHTML = PIDS.map(pid => `
        <div class="proc-row" id="proc-${pid}">
          <div class="proc-top">
            <div class="proc-name">
              <span class="pid-tag">${pid}</span>
              <span id="pname-${pid}">—</span>
            </div>
            <span class="proc-badge" id="pbadge-${pid}">Chờ</span>
          </div>
          <div class="proc-meta">
            <span class="proc-reason" id="preason-${pid}">Sẵn sàng</span>
            <span id="ppct-${pid}" style="font-weight:700; font-variant-numeric:tabular-nums;">0%</span>
          </div>
          <div class="pbar"><div class="pbar-fill" id="pbar-${pid}"></div></div>
        </div>
      `).join('');

      const gpuCardHtml = (id) => `
        <div class="gpu-card" id="gpu-${id}">
          <div class="gpu-head">
            <div class="gpu-title">
              <span>GPU ${id}</span>
              <span class="mig-tag" id="gmig-${id}" style="display:none;">MIG 3-Slice</span>
            </div>
            <span class="gpu-pct" id="gpct-${id}">0%</span>
          </div>
          <div class="part-meter" id="gmeter-${id}">
            <div class="pm-seg pm-s1" id="gm1-${id}"></div>
            <div class="pm-seg pm-s2" id="gm2-${id}"></div>
            <div class="pm-seg pm-s3" id="gm3-${id}"></div>
            <div class="pm-seg pm-waste" id="gmw-${id}"></div>
          </div>
          <div class="gpu-slots" id="gslots-${id}">
            <div class="slot-empty">Trống · Sẵn sàng</div>
          </div>
        </div>
      `;
      document.getElementById('rackACards').innerHTML = gpuCardHtml(0) + gpuCardHtml(1);
      document.getElementById('rackBCards').innerHTML = gpuCardHtml(2) + gpuCardHtml(3);
    }

    async function selectScenario(id) {
      await fetch('/api/scenario?id=' + encodeURIComponent(id), { method: 'POST' });
      poll();
    }

    async function startRun(mode, sim = 0) {
      lastRequestedMode = mode;
      const sc = lastState ? lastState.scenario : 'mixed';
      await fetch('/api/run?mode=' + encodeURIComponent(mode) + '&scenario=' + encodeURIComponent(sc) + '&sim=' + sim, { method: 'POST' });
      poll();
    }

    async function startSimFallback() {
      await startRun(lastRequestedMode, 1);
    }

    async function togglePause() {
      await fetch('/api/pause', { method: 'POST' });
      poll();
    }

    async function resetDemo() {
      await fetch('/api/run?mode=clean', { method: 'POST' });
      poll();
    }

    function updateProcessRow(p) {
      const row = document.getElementById('proc-' + p.pid);
      const nameEl = document.getElementById('pname-' + p.pid);
      const badgeEl = document.getElementById('pbadge-' + p.pid);
      const reasonEl = document.getElementById('preason-' + p.pid);
      const pctEl = document.getElementById('ppct-' + p.pid);
      const barEl = document.getElementById('pbar-' + p.pid);

      nameEl.textContent = p.title;
      row.className = 'proc-row st-' + p.state;

      if (p.state === 'waiting') {
        badgeEl.className = 'proc-badge pb-wait';
        badgeEl.textContent = 'Đang chờ (' + p.req_label + ')';
        reasonEl.textContent = p.wait_reason;
      } else if (p.state === 'pending') {
        badgeEl.className = 'proc-badge pb-pend';
        badgeEl.textContent = 'Kẹt Pending';
        reasonEl.textContent = p.wait_reason;
      } else if (p.state === 'blocked') {
        badgeEl.className = 'proc-badge pb-blk';
        badgeEl.textContent = 'Khóa GPU ' + p.gpu_id + ' (0%)';
        reasonEl.textContent = p.wait_reason;
      } else if (p.state === 'running') {
        badgeEl.className = 'proc-badge pb-run';
        badgeEl.textContent = p.mig_slice
          ? 'GPU ' + p.gpu_id + ' · MIG ' + p.mig_slice + '/3'
          : 'GPU ' + p.gpu_id + ' · ' + (p.cross_rack ? 'Cross-Rack' : 'Nguyên GPU');
        reasonEl.textContent = p.wasted_pct > 0
          ? 'Chỉ dùng ' + p.used_pct + '% (lãng phí ' + p.wasted_pct + '% GPU)'
          : p.last_line;
      } else {
        badgeEl.className = 'proc-badge pb-done';
        badgeEl.textContent = '✓ Hoàn tất';
        reasonEl.textContent = 'Đã xong trên GPU ' + p.gpu_id;
      }

      pctEl.textContent = p.progress + '%';
      barEl.style.width = p.progress + '%';
    }

    function updateGpuCard(g) {
      const card = document.getElementById('gpu-' + g.id);
      const migEl = document.getElementById('gmig-' + g.id);
      const pctEl = document.getElementById('gpct-' + g.id);
      const m1 = document.getElementById('gm1-' + g.id);
      const m2 = document.getElementById('gm2-' + g.id);
      const m3 = document.getElementById('gm3-' + g.id);
      const mw = document.getElementById('gmw-' + g.id);
      const slotsEl = document.getElementById('gslots-' + g.id);

      migEl.style.display = g.mig_mode ? 'inline-block' : 'none';

      let cls = 'gpu-card';
      if (g.blocked) cls += ' g-blocked';
      else if (g.cross_rack) cls += ' g-cross';
      else if (g.wasted_pct > 0) cls += ' g-waste';
      else if (g.processes.length > 0) cls += ' g-active';
      card.className = cls;

      pctEl.textContent = g.blocked
        ? '0% (Bị khóa)'
        : (g.processes.length ? g.used_pct + '% dùng' : '0% trống');

      // Update proportional capacity meter without recreating DOM!
      let w1 = 0, w2 = 0, w3 = 0, ww = 0;
      m1.className = 'pm-seg ' + (g.cross_rack ? 'pm-cross' : 'pm-s1');
      if (g.mig_mode) {
        for (const p of g.processes) {
          if (p.mig_slice === 1) w1 = p.used_pct;
          if (p.mig_slice === 2) w2 = p.used_pct;
          if (p.mig_slice === 3) w3 = p.used_pct;
        }
      } else if (g.processes.length > 0) {
        const p = g.processes[0];
        w1 = p.used_pct;
        ww = p.wasted_pct;
      }
      m1.style.width = w1 + '%';
      m2.style.width = w2 + '%';
      m3.style.width = w3 + '%';
      mw.style.width = ww + '%';

      // Build clean slot key to avoid unnecessary innerHTML churn
      let slotsHtml = '';
      if (g.mig_mode) {
        for (let s = 1; s <= 3; s++) {
          const p = g.processes.find(x => x.mig_slice === s);
          if (p) {
            slotsHtml += `
              <div class="slot-row s${s}">
                <span><strong>${p.pid}</strong> ${p.title} <span class="cid-mono">${p.cid}</span></span>
                <span><strong>Slice ${s}/3</strong> · ${p.progress}%</span>
              </div>`;
          } else {
            slotsHtml += `<div class="slot-row smig-free"><span>Slice ${s}/3 (33%)</span><span>Trống</span></div>`;
          }
        }
      } else if (g.processes.length === 0) {
        slotsHtml = '<div class="slot-empty">Trống · 100% sẵn sàng</div>';
      } else {
        const p = g.processes[0];
        if (p.state === 'blocked') {
          slotsHtml = `
            <div class="slot-row sblk">
              <span><strong>${p.pid}</strong> ${p.title} <span class="cid-mono">${p.cid}</span></span>
              <span><strong>Khóa 0%</strong></span>
            </div>
            <div class="slot-row swaste"><span>100% GPU bị khóa cứng chờ peer</span><span>0% hữu ích</span></div>`;
        } else {
          const sc = p.cross_rack ? 'scross' : 's1';
          const badgeTxt = p.cross_rack ? 'Cross-Rack 720ms' : (p.link_mode === 'nvlink' ? 'NVLink 60ms' : '100% cấp phát');
          slotsHtml = `
            <div class="slot-row ${sc}">
              <span><strong>${p.pid}</strong> ${p.title} <span class="cid-mono">${p.cid}</span></span>
              <span><strong>${p.progress}%</strong> · ${badgeTxt}</span>
            </div>`;
          if (p.wasted_pct > 0) {
            slotsHtml += `<div class="slot-row swaste"><span>Phần GPU dư bị khóa (không thể chia sẻ)</span><span>-${p.wasted_pct}% lãng phí</span></div>`;
          }
        }
      }
      if (slotsEl.dataset.prev !== slotsHtml) {
        slotsEl.innerHTML = slotsHtml;
        slotsEl.dataset.prev = slotsHtml;
      }
    }

    function updateBenchmarks(b, p) {
      const setCell = (id, html, cls = '') => {
        const el = document.getElementById(id);
        el.innerHTML = html;
        el.className = cls;
      };
      setCell('bTime', b ? b.elapsed_s + 's' : 'Chưa chạy', b ? 'bad-val' : '');
      setCell('pTime', p ? p.elapsed_s + 's' : 'Chưa chạy', p ? 'win-val' : '');
      setCell('bUtil', b ? b.avg_util + '%' : '—', b ? 'bad-val' : '');
      setCell('pUtil', p ? p.avg_util + '%' : '—', p ? 'win-val' : '');
      setCell('bDead', b ? b.deadlocks + ' GPU bị khóa chết' : '—', b ? 'bad-val' : '');
      setCell('pDead', p ? p.deadlocks + ' (Không khóa GPU)' : '—', p ? 'win-val' : '');
      setCell('bWait', b ? b.peak_waiting + ' containers (kẹt Pending)' : '—', b ? 'bad-val' : '');
      setCell('pWait', p ? p.peak_waiting + ' containers (0 kẹt · Queue lịch sự)' : '—', p ? 'win-val' : '');
      setCell('bCross', b ? b.cross_rack + ' job (AllReduce 720ms)' : '—', b ? 'bad-val' : '');
      setCell('pCross', p ? p.cross_rack + ' job (100% NVLink 60ms)' : '—', p ? 'win-val' : '');
      setCell('bMig', b ? '0 GPU (chiếm nguyên GPU)' : '—', b ? 'bad-val' : '');
      setCell('pMig', p ? 'Tiết kiệm ' + p.mig_saved + ' GPU nhờ MIG' : '—', p ? 'win-val' : '');

      const vBox = document.getElementById('verdictBox');
      if (b && p) {
        const speedup = (b.elapsed_s / Math.max(0.1, p.elapsed_s)).toFixed(2);
        vBox.className = 'verdict show';
        vBox.textContent = `Kết luận đo thực tế trên cùng 8 containers: Cách đề xuất nhanh hơn ${speedup}x (${p.elapsed_s}s vs ${b.elapsed_s}s), tăng hiệu suất GPU từ ${b.avg_util}% lên ${p.avg_util}%, loại bỏ hoàn toàn Deadlock & Cross-Rack!`;
      } else {
        vBox.className = 'verdict';
      }
    }

    async function poll() {
      try {
        const res = await fetch('/api/state');
        const d = await res.json();
        lastState = d;
        clientClockBase = d.elapsed_s || 0;
        clientClockStamp = performance.now();

        const errEl = document.getElementById('errBanner');
        if (!d.docker_ok) {
          document.getElementById('errText').textContent = 'Docker chưa sẵn sàng: ' + d.docker_error;
          errEl.className = 'err-banner show';
        } else {
          errEl.className = 'err-banner';
        }

        const pill = document.getElementById('execModePill');
        if (d.sim_mode) {
          pill.textContent = 'Mô phỏng UI · 8 Containers';
          pill.className = 'mode-pill sim';
        } else {
          pill.textContent = 'Docker Thật · 8 Containers';
          pill.className = 'mode-pill real';
        }

        const scList = d.scenarios || [];
        const scTabsEl = document.getElementById('scTabs');
        const tabsHtml = scList.map(s => {
          const dotCls = (s.done_base && s.done_prop) ? 'both' : ((s.done_base || s.done_prop) ? 'one' : '');
          const actCls = s.id === d.scenario ? 'active' : '';
          return `<button class="sc-tab ${actCls}" onclick="selectScenario('${s.id}')"><span class="sc-dot ${dotCls}"></span> ${s.tab}</button>`;
        }).join('');
        if (scTabsEl.dataset.prev !== tabsHtml) {
          scTabsEl.innerHTML = tabsHtml;
          scTabsEl.dataset.prev = tabsHtml;
        }
        const activeScObj = scList.find(s => s.id === d.scenario);
        document.getElementById('scDesc').textContent = activeScObj ? activeScObj.title : '';

        const sb = document.getElementById('stateBadge');
        if (d.paused) {
          sb.className = 'state-badge paused';
          sb.textContent = 'Đang tạm dừng';
        } else if (d.running) {
          sb.className = d.mode === 'baseline' ? 'state-badge run-base' : 'state-badge run';
          sb.textContent = d.mode === 'baseline' ? 'Đang chạy · Mặc định' : 'Đang chạy · Đề xuất';
        } else if (d.mode !== 'idle') {
          sb.className = 'state-badge done';
          sb.textContent = 'Hoàn tất';
        } else {
          sb.className = 'state-badge';
          sb.textContent = 'Sẵn sàng';
        }

        document.getElementById('phaseBanner').textContent = d.phase_banner || '';

        const btnPause = document.getElementById('btnPause');
        btnPause.disabled = !d.running;
        btnPause.className = d.paused ? 'btn-pause is-paused' : 'btn-pause';
        btnPause.textContent = d.paused ? '▶ Tiếp tục' : '⏸ Tạm dừng';

        const procs = d.processes || [];
        const doneCnt = procs.filter(p => p.state === 'completed').length;
        const waitingProcs = procs.filter(p => p.state === 'waiting' || p.state === 'pending');
        const gpus = d.gpus || [];
        const avgUtilNow = gpus.length ? Math.round(gpus.reduce((a, g) => a + g.used_pct, 0) / gpus.length) : 0;

        document.getElementById('kDone').textContent = doneCnt + ' / 8';
        document.getElementById('kWait').textContent = waitingProcs.length;
        document.getElementById('kUtil').textContent = avgUtilNow + '%';
        document.getElementById('kTime').textContent = clientClockBase.toFixed(1) + 's';

        const ws = document.getElementById('waitingSummary');
        if (procs.length === 0) {
          ws.className = 'waiting-summary';
          ws.textContent = 'Chờ khởi chạy';
        } else if (waitingProcs.length > 0) {
          const hasPend = waitingProcs.some(p => p.state === 'pending');
          ws.className = 'waiting-summary ' + (hasPend ? 'has-pend' : 'has-wait');
          ws.textContent = 'Đang chờ: ' + waitingProcs.map(p => p.pid).join(', ');
        } else {
          ws.className = 'waiting-summary clear';
          ws.textContent = '0 process đang chờ';
        }

        const activeGpus = gpus.filter(g => g.processes.length > 0).length;
        const gs = document.getElementById('gpuSummary');
        gs.className = 'waiting-summary ' + (activeGpus > 0 ? 'clear' : '');
        gs.textContent = activeGpus + '/4 GPU đang hoạt động';

        const hasCross = gpus.some(g => g.cross_rack);
        document.getElementById('crossAlert').className = hasCross ? 'cross-alert show' : 'cross-alert';

        if (procs.length === 8) {
          procs.forEach(updateProcessRow);
        } else {
          const idleSpecs = activeScObj ? activeScObj.specs : [];
          idleSpecs.forEach(s => updateProcessRow({
            ...s, state: 'waiting', wait_reason: 'Sẵn sàng · Bấm nút 1 hoặc 2 để chạy',
            progress: 0, gpu_id: null, mig_slice: null,
            used_pct: 0, wasted_pct: 0, cross_rack: false, last_line: ''
          }));
        }

        if (gpus.length === 4) {
          gpus.forEach(updateGpuCard);
        } else {
          [0, 1, 2, 3].forEach(id => updateGpuCard({
            id, mig_mode: false, processes: [], used_pct: 0, wasted_pct: 0, blocked: false, cross_rack: false
          }));
        }

        const b = (d.benchmarks || {}).baseline;
        const p = (d.benchmarks || {}).proposed;
        updateBenchmarks(b, p);

        const logs = d.logs || [];
        const term = document.getElementById('termBox');
        term.innerHTML = logs.length === 0
          ? 'Sẵn sàng khởi chạy 8 containers...'
          : logs.map(l => `<div><span style="color:#38bdf8">[${l.time}]</span> <strong style="color:${l.tag==='ERR'||l.tag==='WARN'?'#fda4af':'#5eead4'}">[${l.tag}]</strong> ${l.msg}</div>`).join('');
      } catch (e) {
        console.error(e);
      }
    }

    // Smooth 100ms client-side timer tick (freezes instantly on pause)
    setInterval(() => {
      if (lastState && lastState.running && !lastState.paused) {
        const dt = (performance.now() - clientClockStamp) / 1000.0;
        document.getElementById('kTime').textContent = (clientClockBase + dt).toFixed(1) + 's';
      }
    }, 100);

    buildShells();
    setInterval(poll, 450);
    poll();
  </script>
</body>
</html>
"""


class ReusableServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/state":
            with STATE_LOCK:
                sc_id = STATE["scenario"]
                payload = {
                    "scenario": sc_id,
                    "scenarios": [
                        {
                            "id": s["id"],
                            "tab": s["tab"],
                            "title": s["title"],
                            "specs": [{"pid": sp["pid"], "title": sp["title"], "req_label": sp["req_label"]} for sp in s["specs"]],
                            "done_base": bool(STATE["benchmarks"][s["id"]]["baseline"]),
                            "done_prop": bool(STATE["benchmarks"][s["id"]]["proposed"]),
                        }
                        for s in SCENARIOS.values()
                    ],
                    "mode": STATE["mode"],
                    "sim_mode": STATE["sim_mode"],
                    "running": STATE["running"],
                    "paused": STATE["paused"],
                    "phase_banner": STATE["phase_banner"],
                    "elapsed_s": get_elapsed_locked(),
                    "gpus": STATE["gpus"],
                    "processes": STATE["processes"],
                    "logs": STATE["logs"],
                    "benchmarks": STATE["benchmarks"][sc_id],
                    "docker_ok": STATE["docker_ok"],
                    "docker_error": STATE["docker_error"],
                }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/scenario":
            qs = urllib.parse.parse_qs(parsed.query)
            sc_id = qs.get("id", ["mixed"])[0]
            if sc_id in SCENARIOS:
                with STATE_LOCK:
                    STATE["run_id"] += 1
                    STATE["paused"] = False
                    PAUSE_EVENT.set()
                    STATE["scenario"] = sc_id
                    STATE["mode"] = "idle"
                    STATE["running"] = False
                    STATE["accumulated_s"] = 0.0
                    STATE["last_resumed_at"] = None
                    STATE["gpus"] = []
                    STATE["processes"] = []
                    STATE["phase_banner"] = f"Đã chọn kịch bản: {SCENARIOS[sc_id]['title']}. Bấm nút 1 hoặc 2 để chạy."
                threading.Thread(target=cleanup_containers, daemon=True).start()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        elif parsed.path == "/api/run":
            qs = urllib.parse.parse_qs(parsed.query)
            mode = qs.get("mode", ["clean"])[0]
            sim = qs.get("sim", ["0"])[0] == "1"
            sc_id = qs.get("scenario", [None])[0]
            if mode in ("baseline", "proposed"):
                threading.Thread(target=start_scenario, args=(mode, sim, sc_id), daemon=True).start()
            else:
                def do_clean():
                    with STATE_LOCK:
                        STATE["run_id"] += 1
                        STATE["paused"] = False
                        PAUSE_EVENT.set()
                    cleanup_containers()
                    with STATE_LOCK:
                        STATE["mode"] = "idle"
                        STATE["sim_mode"] = False
                        STATE["running"] = False
                        STATE["accumulated_s"] = 0.0
                        STATE["last_resumed_at"] = None
                        STATE["docker_ok"] = True
                        STATE["docker_error"] = ""
                        STATE["phase_banner"] = "Đã dọn sạch containers. Bấm nút 1 hoặc 2 để chạy lại."
                        STATE["gpus"] = []
                        STATE["processes"] = []
                        add_log("CLEAN", "Đã dừng và xóa toàn bộ Docker containers demo.")
                threading.Thread(target=do_clean, daemon=True).start()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        elif parsed.path == "/api/pause":
            with STATE_LOCK:
                want_pause = not STATE["paused"]
            res = set_paused(want_pause)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    cleanup_containers()
    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()
    print(f"Live Docker Demo Web UI đang chạy tại: http://localhost:{PORT}")
    print("Nhấn Ctrl+C để dừng và dọn container.")
    try:
        with ReusableServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang dọn containers demo...")
        cleanup_containers()
