CLOUD COMPUTING — PHẦN 1
Ngày thuyết trình: November 27th 2026
10 slide, tỉ lệ 16:9; thời lượng gợi ý 14 phút.

MỞ NHANH
- cloud-part1.pdf: bản trình chiếu cuối cùng.
- main.tex: điểm vào LaTeX; từng slide nằm trong slides/.
- KICH_BAN_THUYET_TRINH.txt: lời dẫn, mốc thời gian, lưu ý kỹ thuật.
- review/all-slides.png: ảnh tổng quan 10 trang.
- review/slide-01.png ... slide-10.png: ảnh từng slide ở độ rộng 1800 px.
- review/layout-audit.json: kết quả kiểm tra hộp chữ từ PDF.
- REVIEW.txt: ghi nhận kiểm tra và sửa bố cục.

Các mục review/, REVIEW.txt và review_layout.py chỉ nằm trong workspace
cục bộ, được git ignore và không cần để biên dịch slide.

BIÊN DỊCH
Mở terminal tại thư mục này, chạy:
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
Lệnh trên tạo main.pdf. Trên Overleaf: tải main.tex, slides/ và assets/,
đặt compiler pdfLaTeX, chọn main.tex làm main document.

Quy trình có render để kiểm tra trên Windows/MiKTeX:
  powershell -ExecutionPolicy Bypass -File build.ps1 -Slide 10
Quy trình này tạo cloud-part1.pdf; -Slide N biên dịch các slide 1..N
và render slide N để kiểm tra ngay trong quá trình soạn.
Script tự tạo thư mục build/ và review/ nếu cần.

Kiểm tra toàn bộ bản cuối:
  python review_layout.py
Cần Python với Pillow, cùng pdftoppm, pdftotext trong PATH.
Các công cụ này chỉ phục vụ kiểm tra, không cần để biên dịch LaTeX.

THIẾT KẾ
Giữ tông xanh, tỉ lệ 16:9 và nền/nhận diện từ mẫu HCMUT được cung cấp.
Nội dung và các sơ đồ được dựng mới bằng TikZ; chỉnh trực tiếp trong .tex.
Font Latin Modern hỗ trợ tiếng Việt và ký hiệu ở dạng vector.
Không dùng ảnh chụp văn bản hoặc hiệu ứng overlay làm tăng số trang.
Nguồn chính thức được tập hợp ở cuối README.txt.
Trang tiêu đề phần 1 chỉ giữ tiêu đề lớn; trang 10 đã bỏ dải thông điệp.
Các khung nội dung đã tách nhau; mũi tên luồng chính căn theo tâm chung.
review_layout.py kiểm tra cả hộp chữ và 45 node/khung được đánh dấu
trong LaTeX, gồm khoảng hở và độ ngang của các hàng mũi tên chính.

PHẠM VI
Chỉ bao gồm người 1 trong Roles.txt, không đi sâu nội dung người 2, 3.
Các mốc: A — bối cảnh/bài toán 4 phút; B — scheduler/gang 4 phút;
C — Kueue 6 phút. Tổng 14 phút, tính cả phần mở đầu.
Thông tin nhóm và GVHD lấy từ ảnh người dùng cung cấp.
Ngày thuyết trình là ngày người dùng yêu cầu, không dùng ngày biên dịch.

NGUỒN CHÍNH THỨC (đối chiếu ngày 24/11/2026)
1. Google Cloud — Introduction to AI/ML workloads on GKE
   https://docs.cloud.google.com/kubernetes-engine/docs/concepts/machine-learning
2. Kubernetes — Kubernetes Scheduler
   https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/
3. Kueue — Overview
   https://kueue.sigs.k8s.io/docs/overview/
4. Kueue — Concepts
   https://kueue.sigs.k8s.io/docs/concepts/
5. Kueue — All-or-nothing Scheduling
   https://kueue.sigs.k8s.io/docs/concepts/all_or_nothing/
6. Kueue — Resource Flavor
   https://kueue.sigs.k8s.io/docs/concepts/resource_flavor/
7. Kueue — Admission
   https://kueue.sigs.k8s.io/docs/concepts/admission/
8. Kueue — Cluster Queue
   https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/
9. Kueue — Workload Priority Class
   https://kueue.sigs.k8s.io/docs/concepts/workload_priority_class/
10. Kueue — Fair Sharing
    https://kueue.sigs.k8s.io/docs/concepts/fair_sharing/
11. Kueue — Cohort
    https://kueue.sigs.k8s.io/docs/concepts/cohort/
12. Kueue — Setup All-or-nothing with ready Pods
    https://kueue.sigs.k8s.io/docs/tasks/manage/setup_wait_for_pods_ready/
13. Kueue — Admission Fair Sharing (lưu ý mở rộng trong kịch bản)
    https://kueue.sigs.k8s.io/docs/concepts/admission_fair_sharing/

Các tính năng tùy chọn cần cấu hình/integration tương ứng. Bộ slide
mô tả cơ chế, không khóa vào một manifest hoặc phiên bản triển khai.
