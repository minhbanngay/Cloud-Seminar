# DEMO CHẠY THẬT 8 DOCKER CONTAINERS + WEB UI TRỰC QUAN

## Yêu cầu duy nhất
- **Docker** (Docker Desktop đang bật) + **Python 3** (không cần `pip install`, không cần `kind`/`kubectl`).

## Chạy trong 1 lệnh
- **macOS / Linux:**
  ```bash
  chmod +x run_demo.sh && ./run_demo.sh
  ```

Mở trình duyệt tại **http://localhost:8090**, chọn **1 trong 4 kịch bản** (mỗi kịch bản đều chạy cùng **8 Docker containers** `P1`–`P8` trên cụm giả lập **4 GPU / 2 Rack**) để đối chiếu **1. Cách Mặc Định (K8s FIFO)** vs **2. Cách Đề Xuất (Kueue + TAS + MIG)**:
1. **Hỗn hợp chuẩn:** 3 Job nhỏ (`1/3 GPU`) + Fine-tune (`2 GPU`) + Sync-Train (`2 GPU`) + Eval (`1 GPU`). Cho thấy đầy đủ MIG + TAS + Kueue Backfill + tránh Deadlock.
2. **Bùng nổ 6 Inference:** 6 Microservice Inference nhỏ (`1/3 GPU`) + 1 Train (`2 GPU`). Đề xuất bật MIG trên cả GPU 0 & GPU 1 để chạy song song toàn bộ 8 containers, tiết kiệm 4 GPU.
3. **Tranh chấp 3 Job Lớn:** 2 Job nhỏ + 3 Job đa-GPU (`2 GPU` mỗi job). Đề xuất tránh bị rải Cross-Rack hàng loạt và giữ 100% NVLink nội bộ Rack.
4. **Chống đói Job Nhỏ:** 3 Job Training lớn đến trước + 2 Job nhỏ tương tác đến sau. Đề xuất giúp job nhỏ không bị bỏ đói tới cuối chu kỳ và ghép MIG ngay khi có GPU trống.

Có thể bấm **Tạm dừng / Tiếp tục** bất cứ lúc nào để đóng băng thật (`docker pause` / `docker unpause`) toàn bộ containers & đồng hồ đo khi thuyết trình.
