# Cloud-Seminar

Slide seminar Cloud Computing bằng LaTeX Beamer, tỉ lệ 16:9.

- [PDF trình chiếu phần 1](Cloud_Part1/cloud-part1.pdf)
- [Mã nguồn LaTeX](Cloud_Part1/main.tex)
- [Kịch bản thuyết trình](Cloud_Part1/KICH_BAN_THUYET_TRINH.txt)
- [Phân công nội dung](Roles.txt)

Ngày thuyết trình: **November 27th 2026**.

## Biên dịch

Trong thư mục `Cloud_Part1`, chạy pdfLaTeX hai lượt:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Trên Overleaf, tải `main.tex`, `slides/`, `assets/` và chọn compiler pdfLaTeX.

Các file review/test, file biên dịch tạm, ZIP và thư mục mẫu UART được ignore.
