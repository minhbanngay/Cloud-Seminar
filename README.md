# Cloud-Seminar

Bài seminar Cloud Computing hoàn chỉnh bằng LaTeX, tỉ lệ 16:9, gồm **34 slide**.

- [PDF trình chiếu đầy đủ](main.pdf)
- [Mã nguồn ghép ba phần](main.tex)
- [Script biên dịch trên Windows](build.ps1)
- [Phân công nội dung](Roles.txt)

Ngày thuyết trình: **November 27th 2026**.

| Phần | Nội dung | Slide trong bản đầy đủ | PDF từng phần |
| --- | --- | --- | --- |
| 1 | Kubernetes, Gang Scheduling và Kueue | 1–10 | [Cloud_Part1](Cloud_Part1/cloud-part1.pdf) |
| 2 | Distributed Training và Topology-Aware Scheduling | 11–26 (trang chuyển: 11) | [Cloud_Part_2](Cloud_Part_2/main.pdf) |
| 3 | GPU Sharing và Resource Optimization | 27–34 | [Cloud_Part3](Cloud_Part3/cloud-part3.pdf) |

Bản đầy đủ thêm trang chuyển chương 2 theo thiết kế trang chuyển chương 1 và giữ bố cục, hình ảnh, nội dung trong ba PDF thành phần; đồng bộ kích thước trang, đánh số slide liên tục 1–34 và thêm bookmarks cho ba phần. Phần 2 tiếp tục ẩn các dòng nguồn trên slide; tài liệu tham khảo riêng vẫn được giữ lại.

## Biên dịch bản đầy đủ

Từ thư mục `D:\Cloud-Seminar`, chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

Script xuất `main.pdf` tại thư mục gốc và tự dọn file biên dịch trung gian. Cần MiKTeX/TeX Live với các gói `pdfpages`, `tikz`, `hyperref`, `geometry`, `lmodern` và hỗ trợ tiếng Việt T5.

Hoặc chạy pdfLaTeX hai lượt:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

## Chỉnh sửa nội dung

`main.tex` ở thư mục gốc ghép trực tiếp ba PDF, giúp giữ nguyên thiết kế từng phần. Để sửa chữ, hình ảnh hoặc sơ đồ, chỉnh mã nguồn LaTeX trong thư mục phần tương ứng và biên dịch lại PDF phần đó trước khi chạy `build.ps1` ở thư mục gốc.

- Phần 1: `Cloud_Part1/main.tex`, `Cloud_Part1/slides/`; script `Cloud_Part1/build.ps1` xuất `cloud-part1.pdf`.
- Phần 2: `Cloud_Part_2/main.tex`, `Cloud_Part_2/part2_topology.tex`; pdfLaTeX xuất `main.pdf` ngay trong thư mục phần 2.
- Phần 3: `Cloud_Part3/main.tex`, `Cloud_Part3/slides/`; script `Cloud_Part3/build.ps1` xuất `cloud-part3.pdf`.

Khi thêm hoặc bớt slide, sửa `\SeminarPageTotal` trong `main.tex` gốc cho khớp tổng số trang.

Trên Overleaf, tải `main.tex` ở thư mục gốc cùng ba thư mục thành phần, chọn pdfLaTeX và đặt `main.tex` gốc làm main document.

## Kịch bản và tài liệu tham khảo

- [Kịch bản phần 1](Cloud_Part1/KICH_BAN_THUYET_TRINH.txt)
- [Kịch bản phần 2](Cloud_Part_2/part2_speaker_notes.md)
- [Kịch bản phần 3](Cloud_Part3/KICH_BAN_THUYET_TRINH.txt)
- [Tài liệu tham khảo phần 2](Cloud_Part_2/part2_references.md)
- Nguồn phần 1 và 3 được ghi trong kịch bản hoặc README của từng phần.
