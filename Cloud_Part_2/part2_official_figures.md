# Part 2 - Hình nguồn đã chèn vào PDF

Bộ slide **15 slide / 15 phút** sử dụng hình chính thức trong `main.pdf`. Ngày đối chiếu nguồn: **23/11/2026**.

## Hình thực sự được dùng

| Slide | File được chèn | Nguồn và phạm vi |
| --- | --- | --- |
| 1 | `google_parallelism_page_57.pdf` | [Google Cloud Training, Module 03, trang 57](https://storage.googleapis.com/cloud-training/T-PSML-O/on-demand/T-PSML-O_M3_Designing_High-performance_ML_systems.pdf#page=57). Trích vùng Data/Model Parallelism, giữ vector. |
| 2 | `google_cloud_data_parallelism.png` | [Google Cloud Blog](https://cloud.google.com/blog/topics/developers-practitioners/optimize-training-performance-reduction-server-vertex-ai). Hình chia input X cho GPU 0/1, không phải Backward/AllReduce. |
| 3 | `nvidia_nccl_allreduce.png` | [NVIDIA NCCL AllReduce](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html#allreduce). Bốn ranks nhận cùng Sum reduction result; phần chữ giải thích phép chia để lấy trung bình. |
| 4 | `nvidia_nccl_reducescatter.png`, `nvidia_nccl_allgather.png` | [NVIDIA NCCL Collectives](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html). Hai collective được giải thích riêng rồi liên hệ với AllReduce. |
| 7 | `nvidia_dgx_gpu_nvswitch_detail.png` | [NVIDIA DGX H100/H200 topology](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html#dgx-h100-200-system-topology). Trích vùng GPU/NVSwitch của một hệ thống DGX, không gọi là sơ đồ GKE. |
| 8 | `google_gpu_network_architecture.png` | [Google GPU networking overview](https://docs.cloud.google.com/ai-hypercomputer/docs/networking-overview). Hình ghi A3U/A4; giải thích Titanium/CX7 NICs, host/storage và GPU-to-GPU planes. |
| 12 | `kueue_theory_of_operation.pdf` | [Kueue Overview](https://kueue.sigs.k8s.io/docs/overview/#high-level-kueue-operation). SVG gốc chuyển PDF vector rồi trích dải admission; TAS được giải thích riêng ở slide 13. |

**Tổng: tám tài sản hình được dùng trên bảy slide.** Các slides 5, 9, 11, 15 dùng chữ/bảng, không cần ảnh trang trí. Các hình có nguồn ngắn ngay trên slide; danh mục tài liệu đầy đủ và IDs R1–R17 nằm ở `part2_references.md`.

## Các sơ đồ tác giả còn dùng

| Slide | File TikZ | Lý do và attribution |
| --- | --- | --- |
| 6 | `03_cluster.tex` | Mô hình Node/Rack/Block tổng quát theo Kueue; không dùng DGX intra-node làm hình Rack/Cluster. |
| 10 | `05_domains.tex` | Kịch bản 6 GPU/rack, job cần 8, để giải thích capacity và locality. |
| 13 | `06_kueue_workflow.tex` | Workflow TAS v0.14.0 theo R7–R11; hình overview không chứa đủ Topology/PodSet assignment. |
| 14 | `07_case_8gpu.tex` | Hai placement 8 workers trên cùng snapshot capacity. Kịch bản tác giả, không phải case study/benchmark do hãng công bố. |

Không gán các sơ đồ này cho tác giả của tài liệu nguồn. Cả slide và notes đều phân biệt hình chính thức với minh họa tự dựng.

## Nguồn gốc và biến đổi kỹ thuật

1. **Google Cloud Training:** tài liệu gốc có 151 trang, tải tại URL R13. Trang 57 được trích nguyên trạng bằng `pdfseparate` thành `google_parallelism_page_57.pdf`. Project giữ trang đã trích để biên dịch; tài liệu đầy đủ có thể tải lại từ nguồn. Slide chọn vùng bằng `trim=100bp 425bp 115bp 120bp,clip`; thứ tự trái/dưới/phải/trên. Không vẽ lại hoặc thay chữ trên hình.
2. **NVIDIA DGX:** giữ PNG gốc `nvidia_dgx_h100_topology.png` (10795 × 6298 px). Bản detail trích hình chữ nhật **x=1800, y=2650, width=8100, height=2500 px**, gốc tọa độ ở góc trên trái. Không đổi màu, thay nhãn hoặc nội suy. Các đường cắt ở rìa còn tiếp tục ra phần ngoài ảnh; caption ghi rõ đây là vùng trích.
3. **Kueue:** giữ SVG gốc `kueue_theory_of_operation.svg`. Render SVG nguyên nội dung qua Chrome headless, khổ giấy trùng viewBox 1202.8845 × 541.3465 CSS px, không header/footer; tạo `kueue_theory_of_operation.pdf` một trang 901.92 × 406.08 pt. Slide 12 chọn dải admission bằng `trim=0bp 132bp 0bp 85bp,clip`. Bản đầy đủ vẫn trong assets. Không dùng overview làm bằng chứng API v0.14.0.
4. **Google A3U/A4:** [PNG gốc](https://docs.cloud.google.com/static/ai-hypercomputer/images/network-architecture.png) giữ nguyên. Không đổi các labels machine types hoặc loại mạng.
5. **Các PNG khác:** giữ nguyên file tải về và tỷ lệ ảnh; nền trắng được đặt ở mức bố cục slide để đọc transparency, không sửa nội dung ảnh.

`sources.json` lưu URL gốc, trang nguồn, ngày đối chiếu, kích thước byte và SHA-256; các bản trích/chuyển đổi ghi rõ derivation. Các PDF/PNG dùng trực tiếp với `graphicx` và pdfLaTeX; không thêm package SVG hoặc đổi compiler.

## Tài sản nguồn dùng để đối chiếu

- Bản DGX topology đầy đủ và SVG Kueue đầy đủ được giữ để đối chiếu, chỉnh vùng trích hoặc xuất lại. Chúng không phải slides phụ vượt quá giới hạn 15 trang.
- URL và checksum các tài sản nguồn được ghi trong `sources.json`; `retained_locally` cho biết tệp nào còn trong project.
