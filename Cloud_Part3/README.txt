CLOUD COMPUTING — PHẦN 3
Ngày thuyết trình: November 27th 2026
8 slide (1 trang tiêu đề + 6 trang nội dung + 1 trang dẫn demo), tỉ lệ 16:9;
thời lượng gợi ý 9 phút (chưa tính demo).

MỞ NHANH
- cloud-part3.pdf: bản trình chiếu 16:9 sẵn sàng xem và thuyết trình.
- main.tex: điểm vào LaTeX Beamer; từng slide nằm trong slides/.
- KICH_BAN_THUYET_TRINH.txt: lời dẫn, mốc thời gian (9 phút), lưu ý kỹ thuật.
- build.ps1: script biên dịch trên Windows/MiKTeX (tương đồng với Cloud_Part1).
- assets/: nền nhận diện HCMUT (BK.png, Background.pdf, FrontBackground.pdf).

BIÊN DỊCH LATEX
Mở terminal tại thư mục Cloud_Part3, chạy hai lượt pdfLaTeX:
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
Lệnh trên tạo main.pdf. Trên Overleaf: tải main.tex, slides/ và assets/,
đặt compiler pdfLaTeX, chọn main.tex làm main document.

Quy trình biên dịch và render kiểm tra trên Windows/MiKTeX:
  powershell -ExecutionPolicy Bypass -File build.ps1 -Slide 8
Script tạo cloud-part3.pdf và render review/slide-08.png để kiểm tra nhanh.

Lưu ý về cloud-part3.pdf đi kèm: bản PDF đóng gói sẵn trong thư mục được
dựng với bố cục, bảng màu và nền nhận diện đồng bộ 16:9 để bạn có thể mở
xem hoặc trình chiếu ngay; khi biên dịch lại bằng pdfLaTeX (Overleaf hoặc
build.ps1 trên MiKTeX), cloud-part3.pdf sẽ được xuất trực tiếp từ main.tex.

THIẾT KẾ
Đồng bộ hoàn toàn với Cloud_Part1: tông xanh BK/Teal/Amber/Red, tỉ lệ 16:9,
nền Background.pdf từ mẫu HCMUT, font Latin Modern hỗ trợ tiếng Việt T5,
sơ đồ dựng bằng TikZ trong từng tệp slides/*.tex, không dùng overlay làm
tăng số trang.

PHẠM VI
Bám sát Người 3 trong Roles.txt:
- Phần A (2 phút): GPU Underutilization & 4 mục tiêu tối ưu (Slide 2).
- Phần B (5 phút): Time-Slicing, NVIDIA MPS, MIG, bảng so sánh & chọn
  workload phù hợp (Slide 3–6).
- Phần C (2 phút): Tổng hợp WHEN – WHERE – HOW & giới thiệu Demo tổng hợp
  AI Workload Scheduling with Kueue on Kubernetes (Slide 7–8).
Tổng 9 phút (chưa tính thời gian chạy Demo).

NGUỒN CHÍNH THỨC (đối chiếu ngày 24/11/2026)
1. Google Cloud — About GPU sharing strategies in GKE
   https://docs.cloud.google.com/kubernetes-engine/docs/concepts/timesharing-gpus
2. Google Cloud — Share GPUs across workloads with GPU time-sharing
   https://docs.cloud.google.com/kubernetes-engine/docs/how-to/timesharing-gpus
3. Google Cloud — Share GPUs with multiple workloads using NVIDIA MPS
   https://docs.cloud.google.com/kubernetes-engine/docs/how-to/nvidia-mps-gpus
4. Google Cloud — Running multi-instance GPUs (MIG) on GKE
   https://docs.cloud.google.com/kubernetes-engine/docs/how-to/gpus-multi
5. NVIDIA — Multi-Process Service (MPS) Documentation
   https://docs.nvidia.com/deploy/mps/index.html
6. NVIDIA — Multi-Instance GPU (MIG) User Guide
   https://docs.nvidia.com/datacenter/tesla/pdf/MIG_User_Guide.pdf
7. NVIDIA — Time-Slicing GPUs in Kubernetes (GPU Operator)
   https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html
8. Kueue — Topology-Aware Scheduling
   https://kueue.sigs.k8s.io/docs/concepts/topology_aware_scheduling/
