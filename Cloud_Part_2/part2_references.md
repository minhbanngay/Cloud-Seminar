# Part 2 - Tài liệu tham khảo

Phiên bản bài: **15 slide / 15 phút**. Ngày đối chiếu: **23/11/2026**. Nguồn do PyTorch, NVIDIA, Google Cloud, Kubernetes hoặc Kubernetes SIGs công bố. Các ví dụ API/annotations Kueue được ghim ở **v0.14.0**, không trộn với API mới trên website hiện hành.

## R1 - PyTorch Distributed Data Parallel

[Getting Started with Distributed Data Parallel](https://docs.pytorch.org/tutorials/intermediate/ddp_tutorial.html)

Slide 1–3, 5, 15: model replicas, Forward/Backward, gradient synchronization, overlap và việc chờ các processes có tốc độ khác nhau. Không suy ra linear speedup theo số GPUs.

## R2 - NVIDIA NCCL Collective Operations

[Collective Operations](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html)

Slide 3–4 dùng ba ảnh gốc: [AllReduce](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/_images/allreduce.png), [ReduceScatter](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/_images/reducescatter.png), [AllGather](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/_images/allgather.png). Ảnh AllReduce là sum; phép lấy trung bình được giải thích riêng. Trang tại ngày truy cập ghi NCCL 2.32.3. Các hình mô tả collective semantics, không phải trace của một thuật toán NCCL cụ thể.

## R3 - Google Cloud GPUs in GKE

[About GPUs in Google Kubernetes Engine](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/gpus)

Bối cảnh GPU Nodes và GKE, slide 6. Không dùng để khẳng định một GPU interconnect chung cho mọi machine type.

## R4 - Google Cloud GPU machine architecture

[GPU machines in accelerator-optimized machine family](https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines)

Slide 7–9: cấu hình interconnect/networking tùy machine series. Một số NVLink domains rack-scale vượt qua ranh giới instance; không khẳng định NVLink chỉ có trong một Node. Không lấy số bandwidth lý thuyết làm benchmark của workload.

## R5 - NVIDIA NCCL Overview

[Overview of NCCL](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/overview.html)

Slide 3–4, 9: thư viện communication primitives hỗ trợ nhiều interconnect, intra-node và inter-node. Không coi NCCL là scheduler Kubernetes.

## R6 - Kueue TAS v0.14.0

[Topology Aware Scheduling - source documentation at v0.14.0](https://github.com/kubernetes-sigs/kueue/blob/v0.14.0/site/content/en/docs/concepts/topology_aware_scheduling.md)

Slide 6, 10–11, 14–15: hierarchy qua node labels, capacity theo topology domain và yêu cầu Required/Preferred. Required cùng domain là ràng buộc; Preferred xét các cấp rộng hơn. Fallback không phải timeout để bỏ Required. Các sơ đồ số GPU trong bài là kịch bản tác giả, không phải hình/benchmark của Kueue.

## R7 - Kueue release v0.14.0

[Release v0.14.0](https://github.com/kubernetes-sigs/kueue/releases/tag/v0.14.0)

Slide 13: TAS lên Beta, bật mặc định; Topology chuyển từ v1alpha1 sang v1beta1. Đây là nguồn để ghim phiên bản, không phải hướng dẫn nâng cấp cluster trong bài nói.

## R8 - Kueue v0.14.0 Workload / PodSet API

[workload_types.go](https://github.com/kubernetes-sigs/kueue/blob/v0.14.0/apis/kueue/v1beta1/workload_types.go)

Đối chiếu `spec.podSets[].topologyRequest.required/preferred` và `status.admission.podSetAssignments[].topologyAssignment`. Nếu cấp thấp nhất là hostname, assignment có thể xác định Node cụ thể. Slide 10–11, 13–14.

## R9 - Kueue v0.14.0 ResourceFlavor API

[resourceflavor_types.go](https://github.com/kubernetes-sigs/kueue/blob/v0.14.0/apis/kueue/v1beta1/resourceflavor_types.go)

Slide 13: `spec.topologyName` tham chiếu Topology; `spec.nodeLabels` chọn nhóm Nodes. Quota được cấu hình qua ClusterQueue, không nằm trong ResourceFlavor.

## R10 - Kueue v0.14.0 TAS Pod ungating controller

[topology_ungater.go](https://github.com/kubernetes-sigs/kueue/blob/v0.14.0/pkg/controller/tas/topology_ungater.go)

Slide 13: áp NodeSelector theo assignment và gỡ topology scheduling gate. Không thay vai trò binding của kube-scheduler.

## R11 - Kubernetes kube-scheduler

[Kubernetes Scheduler](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/)

Slide 12–13, 15: filtering/scoring và binding Pod vào Node. Workload được admit chưa đồng nghĩa mọi Pod đã Running.

## R12 - PyTorch DDP internals

[Distributed Data Parallel design note](https://docs.pytorch.org/docs/2.15/notes/ddp.html)

Slide 5: gradient buckets/autograd hooks và sync trong Backward. Không dùng tổng compute time + tổng communication time như công thức chính xác khi có overlap.

## R13 - Google Cloud Training: Data / Model Parallelism

[Designing High-performance ML Systems, Module 03, v2.0.3, trang PDF 57](https://storage.googleapis.com/cloud-training/T-PSML-O/on-demand/T-PSML-O_M3_Designing_High-performance_ML_systems.pdf#page=57)

Hình chính thức trên slide 1. Trích trang 57 bằng `pdfseparate`, rồi chọn vùng biểu đồ bằng `graphicx trim/clip`; giữ nội dung vector. Các số viết tay thuộc ví dụ nguồn, không phải số lượng GPU.

## R14 - Google Cloud Blog: Data Parallelism

[Optimize training performance with Reduction Server on Vertex AI](https://cloud.google.com/blog/topics/developers-practitioners/optimize-training-performance-reduction-server-vertex-ai)

[Ảnh Data Parallelism gốc](https://storage.googleapis.com/gweb-cloudblog-publish/images/Screen_Shot_2021-08-23_at_2.25.47_PM.max-700x700.png)

Slide 2 chỉ sử dụng hình input X chia cho GPU 0/1. Không gọi ảnh này là sơ đồ AllReduce/Backward hay khẳng định job của seminar dùng Reduction Server.

## R15 - NVIDIA DGX H100/H200 topology

[DGX H100/H200 User Guide - System Topology](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html#dgx-h100-200-system-topology)

[Ảnh topology gốc](https://docs.nvidia.com/dgx/dgxh100-user-guide/_images/dgx-h100-system-topology.png)

Slide 7 dùng vùng GPU/NVSwitch trích từ PNG, giữ pixel và màu gốc. Hình là ví dụ một hệ thống DGX, không phải sơ đồ GKE/A3 hoặc toàn cluster. Bản đầy đủ vẫn giữ trong assets.

## R16 - Google Cloud GPU networking overview

[GPU networking overview](https://docs.cloud.google.com/ai-hypercomputer/docs/networking-overview)

[Ảnh network architecture gốc](https://docs.cloud.google.com/static/ai-hypercomputer/images/network-architecture.png)

Slide 8: hình ghi “High-level A3U and A4 network architecture”, tách host/storage data plane với GPU-to-GPU data plane. Dùng RoCE/RDMA, không phải InfiniBand trong ảnh. Slide 9 dùng làm bối cảnh về đường communication; không đưa benchmark.

## R17 - Kueue High-level operation

[Kueue Overview](https://kueue.sigs.k8s.io/docs/overview/#high-level-kueue-operation)

[SVG gốc](https://kueue.sigs.k8s.io/images/theory-of-operation.svg)

Slide 12 dùng SVG chuyển thành PDF rồi trích vùng admission. Hình tổng quan website tại ngày tải, không phải workflow TAS chuyên biệt hoặc bằng chứng API v0.14.0. Chữ nodeAffinity trên ảnh là mô tả overview; phần TAS v0.14.0 ở slide 13 dựa vào APIs/controller R8–R10.

## API và annotations được dùng

| Thành phần | Giá trị / vị trí v0.14.0 | Nguồn |
| --- | --- | --- |
| API group/version | `kueue.x-k8s.io/v1beta1` | R7–R9 |
| Topology hierarchy | `spec.levels[].nodeLabel`, từ rộng đến hẹp | R6 |
| ResourceFlavor → Topology | `spec.topologyName` | R9 |
| Required / Preferred | `spec.podSets[].topologyRequest.required/preferred` | R8 |
| Job PodTemplate annotation | `spec.template.metadata.annotations` | R6 |
| Required annotation | `kueue.x-k8s.io/podset-required-topology` | R6, R8 |
| Preferred annotation | `kueue.x-k8s.io/podset-preferred-topology` | R6, R8 |
| Assignment | `status.admission.podSetAssignments[].topologyAssignment` | R8 |
| Pod constraints + gate | NodeSelector theo assignment, gỡ topology gate | R10 |

Fragment dưới đây chỉ minh họa vị trí annotation trong spec của một `batch/v1 Job`, không phải manifest hoàn chỉnh:

```yaml
template:
  metadata:
    annotations:
      kueue.x-k8s.io/podset-required-topology: "cloud.provider.com/topology-rack"
```

Key `cloud.provider.com/topology-rack` là ví dụ trong tài liệu Kueue, không phải khẳng định là label GKE. Node labels thực phải phù hợp Topology và phần cứng. Manifest GPU đầy đủ còn cần requests/limits `nvidia.com/gpu` và quota phù hợp. Ví dụ bài nói xét capacity có sẵn, không mô tả Provisioning AdmissionCheck.

Danh mục nguồn ảnh/biến thể: [part2_official_figures.md](part2_official_figures.md). Nền/logo giữ từ template gốc. Không có benchmark hoặc paper được tạo ra để minh họa lợi ích.
