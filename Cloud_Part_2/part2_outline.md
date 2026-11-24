# Part 2 - Distributed Training & Topology-Aware Scheduling

**15 slide / 15 phút.** Giữ template Beamer Madrid/BKTemplate, tỷ lệ 16:9, fonts, background và hình học footer. `main.tex` là entry chính, tạo `main.pdf` của Part 2.

Câu hỏi trung tâm: **WHERE? GPU workers nên được đặt ở đâu để hỗ trợ hiệu quả Distributed Training?** Nội dung tiếng Việt, giữ thuật ngữ kỹ thuật. Không thêm cover/agenda ngoài 15 slide.

## Outline và thời gian

| # | Phần | Slide | Hình / cách trình bày | Thời gian | Mốc kết thúc |
| --- | --- | --- | --- | --- | --- |
| 1 | A | Data Parallelism và Model Parallelism | Google Cloud Training, trang 57, PDF vector | 1:10 | 1:10 |
| 2 | A | GPU Workers trong một Training Step | Hình Data Parallelism của Google Cloud | 0:55 | 2:05 |
| 3 | A | Gradient Synchronization với AllReduce | Hình AllReduce bốn ranks của NVIDIA NCCL | 1:05 | 3:10 |
| 4 | A | ReduceScatter và AllGather | Hai hình collective gốc từ NVIDIA | 0:50 | 4:00 |
| 5 | A | Vì sao Communication làm tăng Step Time? | Cơ chế overlap, chờ workers và đường găng | 1:00 | 5:00 |
| 6 | B | GPU Node, Rack, Block và Cluster | Sơ đồ tổng quát của tác giả theo Kueue | 0:55 | 5:55 |
| 7 | B | Intra-node: GPU và NVSwitch | Vùng GPU/NVSwitch từ sơ đồ DGX H100/H200 | 1:10 | 7:05 |
| 8 | B | Inter-node Communication trên Google Cloud | Hình kiến trúc network planes A3 Ultra/A4 | 1:05 | 8:10 |
| 9 | B | Bandwidth, Latency và Communication Overhead | Bảng khái niệm và tác động | 0:50 | 9:00 |
| 10 | C | TAS: Availability và Locality | Ví dụ mỗi rack 6 GPU trống, job cần 8 | 1:00 | 10:00 |
| 11 | C | Required và Preferred Topology | Hai lựa chọn và trade-off thời gian chờ | 0:55 | 10:55 |
| 12 | C | Kueue: luồng Admission tổng quan | Trích vùng admission từ hình Kueue chính thức | 1:05 | 12:00 |
| 13 | C | Kueue TAS: Admission đến Pod Placement | Workflow tác giả, API ghim v0.14.0 | 1:15 | 13:15 |
| 14 | C | Case Study: 8-GPU Worker Placement | 4 + 4 cùng rack vs. 2 + 2 + 2 + 2 qua racks | 1:05 | 14:20 |
| 15 | C | Key Takeaways | Thông điệp kết thúc và chuyển sang Part 3 | 0:40 | 15:00 |

**A = 5:00; B = 4:00; C = 6:00; tổng = 15:00 (900 giây).** Phân bổ đã gồm chỉ hình và chuyển tiếp, không gồm Q&A. Thời lượng thực tế phụ thuộc tốc độ nói; tập theo các mốc tích lũy trong notes.

## Đối chiếu 13 mục nội dung

| Mục | Nội dung | Slide |
| --- | --- | --- |
| 1 | Data Parallelism / Model Parallelism | 1 |
| 2 | Vai trò workers | 2 |
| 3 | Gradient Synchronization / AllReduce | 3–4 |
| 4 | Giao tiếp ảnh hưởng training time | 5 |
| 5 | GPU Node, Rack, Cluster | 6 |
| 6 | PCIe, NVLink/NVSwitch, Ethernet/InfiniBand | 6–8 |
| 7 | Intra-node / inter-node | 7–8 |
| 8 | Bandwidth, latency, overhead | 5, 9 |
| 9 | Khái niệm TAS | 10 |
| 10 | Availability / locality | 10 |
| 11 | TAS trong Kueue | 12–13 |
| 12 | Workers gần nhau / phân tán | 14 |
| 13 | Lợi ích và giới hạn | 11, 14–15 |

Thông điệp được ghi nguyên văn ở slide 15: **“Có đủ GPU chưa chắc đã đủ; vị trí của các GPU cũng quyết định hiệu quả huấn luyện phân tán.”** Câu chuyển tiếp sang GPU sharing giữ nguyên theo yêu cầu nhóm.

## Quy tắc ghép hình và nội dung

- Bảy slide (1, 2, 3, 4, 7, 8, 12) sử dụng tám tài sản hình chính thức hoặc bản trích/chuyển định dạng của chúng; danh mục ở `part2_official_figures.md`.
- Bốn sơ đồ tác giả còn dùng ở slide 6, 10, 13, 14 vì cần mô hình tổng quát hoặc kịch bản riêng. Attribution nêu rõ tác giả tự dựng và tài liệu cơ chế, không gọi là hình xuất bản bởi Google/NVIDIA/Kueue.
- Sum AllReduce trong ảnh được phân biệt với phép chia lấy trung bình trong ví dụ.
- Hình DGX là một hệ thống NVIDIA cụ thể; chỉ dùng cho intra-node. Hình mạng Google ghi rõ A3 Ultra/A4; không áp cho mọi GPU instance, không gọi RoCE là InfiniBand.
- Hình Kueue overview chỉ giải thích admission tổng quát. TAS được trình bày riêng bằng workflow và sources v0.14.0; không lấy hình overview làm bằng chứng API của phiên bản này.
- Không có số liệu benchmark, throughput/latency hoặc phần trăm speedup tự tạo.
- Slide 10–11 dùng snapshot mỗi rack 6 GPU trống. Slide 14 dùng snapshot khác: mỗi node 4 GPU trống. Quota, CPU, RAM và các điều kiện scheduling khác giả định đủ.
- Kueue v0.14.0 là phiên bản tham chiếu; không tuyên bố là phiên bản mới nhất. Ví dụ TAS dùng capacity có sẵn, không có Provisioning AdmissionCheck.

## Biên dịch và tích hợp

```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Hai lượt để ổn định navigation, section bookmarks và tổng số trang. Nguồn dùng link trực tiếp và IDs, không cần BibTeX riêng cho excerpt. Giữ cấu hình `biblatex` từ template.

`main.tex` gọi `\input{part2_topology}` bên trong document và đặt section để footer hiển thị Phần 2/3. Khi ghép thêm bài nhóm, giữ Part 2 sau Part 1 và trước Part 3. Giữ kèm thư mục `figures/part2/`, các thư viện TikZ và màu BKTemplate từ preamble. File nội dung tạo một section cho Part 2 và ba subsections A/B/C.

`part2_speaker_notes.md`: kịch bản theo 15 slide. `part2_references.md`: nguồn học thuật và API. `part2_official_figures.md`: nguồn ảnh, cách trích/chuyển đổi và mapping thực tế. Giữ `thesiscite.bib` vì preamble có tham chiếu đến tệp này. Các tệp phụ trợ do LaTeX tạo ra có thể xóa sau khi biên dịch thành công.
