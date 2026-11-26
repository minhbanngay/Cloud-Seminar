#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="seminar-ai-worker:local"

echo "[1/2] Kiểm tra Docker và build image ${IMAGE_NAME}..."
docker info >/dev/null 2>&1 || { echo "Lỗi: Hãy mở Docker Desktop trước!"; exit 1; }
docker build -t "${IMAGE_NAME}" .

echo "[2/2] Khởi động Web UI Live Demo tại http://localhost:8090 ..."
python3 server.py
