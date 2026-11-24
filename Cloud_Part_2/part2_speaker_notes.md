# Part 2 - Speaker Notes: 15 slide / 15 phút

Câu hỏi trung tâm: **WHERE? GPU workers nên được đặt ở đâu?** Ngôn ngữ tiếng Việt, giữ thuật ngữ chuyên ngành. Các khoảng thời gian đã gồm chỉ hình, dừng nhịp và chuyển slide; cần tập nói với đồng hồ, không đọc thêm mục giải thích kỹ thuật như một đoạn thoại thứ hai.

- Phần A, slide 1–5: **5:00**.
- Phần B, slide 6–9: **4:00**.
- Phần C, slide 10–15: **6:00**.
- Tổng: **15:00**, không tính Q&A.

Nguồn [R1]–[R17] và attribution hình có trong `part2_references.md`. Danh mục hình thực sự đã chèn nằm trong `part2_official_figures.md`. Không gọi các sơ đồ case study tự dựng là hình của Google/NVIDIA/Kueue.

## Slide 1 - Data Parallelism và Model Parallelism

**Thời gian:** 1:10; mốc **0:00–1:10**.

**Thông điệp chính:** Phân chia training qua nhiều GPU tạo ra các nhu cầu communication khác nhau.

**Giải thích kỹ thuật:** Data Parallelism giữ các model replicas; chia dữ liệu, không tự gộp VRAM. Model Parallelism chia model; hình Google minh họa phân chia theo lớp. Tensor Parallelism là một dạng khác, không cần khai triển trong slide nhập môn này.

**Kịch bản nói:**

“Phần trước trả lời khi nào workload được chạy. Phần của mình trả lời các GPU workers nên được đặt ở đâu. Để hiểu placement, trước hết cần hiểu chúng phối hợp như thế nào.

Đây là hình từ Google Cloud Training. Bên trái, ba thiết bị giữ cùng cấu trúc model nhưng xử lý các mẫu dữ liệu khác nhau: đó là Data Parallelism. Bên phải, một model được chia thành những phần khác nhau để chạy trên nhiều thiết bị: đó là Model Parallelism.

Ta cần nhiều GPU để có thêm compute, hoặc vì model không vừa bộ nhớ một GPU. Tuy nhiên, sau khi chia việc, các phần vẫn phải trao đổi dữ liệu. Vì vậy, thêm GPU tạo ra cả cơ hội tăng tốc lẫn nhu cầu giao tiếp.”

**Cách giải thích hình:** Khoảng 15 giây chỉ ba mạng giống nhau bên trái, rồi hai vùng màu trong cùng model bên phải. Các số viết tay 2, 4, 1 thuộc ví dụ dữ liệu của tài liệu, không phải số lượng GPU hoặc số ranks trong bài. Hình được trích vùng biểu đồ từ trang 57, không vẽ lại.

**Chuyển tiếp:** “Một GPU worker cụ thể làm gì trong một training step?”

**Tài liệu:** [R13] Google Cloud Training, trang 57; [R1] PyTorch DDP.

## Slide 2 - GPU Workers trong một Training Step

**Thời gian:** 0:55; mốc **1:10–2:05**.

**Thông điệp chính:** Worker thực hiện compute cục bộ và tham gia đồng bộ kết quả.

**Giải thích kỹ thuật:** Trong ví dụ, worker là process sử dụng một GPU, không phải cả Node. Forward tính output/loss; Backward tính gradients. DDP có thể bắt đầu sync trong Backward. Các bước trên slide là trình tự logic, không khẳng định Backward và communication phải chạy tách rời.

**Kịch bản nói:**

“Với Data Parallelism đồng bộ, mỗi worker nhận một phần mini-batch. Worker chạy Forward để tính dự đoán và loss, rồi Backward để tính gradients. Những gradients này cần được đồng bộ trước khi các bản sao model tiếp tục cập nhật nhất quán.

Hình Google bên phải cho thấy input X được chia thành hai phần. GPU 0 và GPU 1 thực hiện cùng các phép toán, nhưng trên dữ liệu khác nhau. Hình này minh họa chia input, chưa vẽ quá trình Backward hay đồng bộ. Các bước ở bên trái bổ sung phần đó.

Như vậy worker vừa tự tính toán, vừa cần phối hợp với các workers khác.”

**Cách giải thích hình:** Khoảng 10 giây lần theo X → split → hai nhánh GPU. Không nói ảnh chứa AllReduce hoặc Reduction Server; bài nguồn có các nội dung đó nhưng ảnh đang dùng chỉ là sơ đồ Data Parallelism.

**Chuyển tiếp:** “Cơ chế nào đưa kết quả gradients chung về mọi worker?”

**Tài liệu:** [R14] Google Cloud Blog, ảnh Data Parallelism; [R1] PyTorch DDP.

## Slide 3 - Gradient Synchronization với AllReduce

**Thời gian:** 1:05; mốc **2:05–3:10**.

**Thông điệp chính:** AllReduce tổng hợp dữ liệu từ các ranks và trả cùng reduction result về mọi rank.

**Giải thích kỹ thuật:** Ảnh NVIDIA là Sum AllReduce. Phép chia cho bốn là bước chuẩn hóa trong ví dụ local batch bằng nhau và cách tính loss tương thích; không biến nghĩa “sum” trên ảnh thành “average”. Model replicas cần khởi tạo và optimizer state nhất quán. Collective không yêu cầu một parameter server độc lập.

**Kịch bản nói:**

“Đây là hình AllReduce trong tài liệu NCCL của NVIDIA. Ban đầu bốn ranks có các input khác nhau. Sau phép reduction, cả bốn đều nhận cùng output. Nếu input là gradient cục bộ, mọi worker sẽ có kết quả tổng hợp để tiếp tục update model.

Chú ý ảnh đang minh họa phép sum. Trong ví dụ bốn local batch có cùng kích thước, nếu muốn gradient trung bình, ta lấy tổng rồi chia bốn. Phân biệt này giúp công thức và hình khớp nhau.

NCCL cung cấp các phép collective cho NVIDIA GPUs. Hình mô tả kết quả của operation; nó không nói tất cả dữ liệu phải đi qua một parameter server hay bắt buộc dùng thuật toán ring.”

**Cách giải thích hình:** Khoảng 10 giây chỉ bốn input màu bên trái và bốn output giống nhau bên phải; đối chiếu công thức Sum với phép chia 4 ở phần chữ dưới hình.

**Chuyển tiếp:** “Có thể hiểu AllReduce qua hai collective đơn giản hơn.”

**Tài liệu:** [R2] NVIDIA NCCL, AllReduce; [R5] NCCL Overview.

## Slide 4 - ReduceScatter và AllGather

**Thời gian:** 0:50; mốc **3:10–4:00**.

**Thông điệp chính:** ReduceScatter tạo các phần kết quả reduction; AllGather tập hợp các phần lên mọi rank.

**Giải thích kỹ thuật:** Hai hình NVIDIA mô tả hai collective độc lập ở mức semantics. Khi áp dụng AllGather lên các phần kết quả từ ReduceScatter, tổ hợp có semantics của AllReduce. Hình không phải trace cụ thể của một run NCCL hoặc chỉ dẫn thứ tự truyền gói tin.

**Kịch bản nói:**

“Bên trái là ReduceScatter: dữ liệu được reduction và mỗi rank giữ một phần kết quả. Bên phải là AllGather: các phần đang nằm trên các ranks được tập hợp lại để mọi rank có đủ dữ liệu.

Kết hợp hai ý này, ta có thể hiểu AllReduce thành ReduceScatter theo sau bởi AllGather. Hai hình dùng ký hiệu input/output riêng của từng operation, nên mình đang giải thích sự kết hợp về cơ chế, không trình bày một trace truyền dữ liệu thực tế.

Chi tiết thuật toán vẫn do thư viện và cấu hình hệ thống quyết định.”

**Cách giải thích hình:** Khoảng 8 giây chỉ output bị chia thành các phần ở hình trái, rồi output đủ các phần ở hình phải. Không gọi các màu là GPU models hoặc tốc độ liên kết.

**Chuyển tiếp:** “Dù chọn thuật toán nào, communication vẫn có thể làm chậm training step.”

**Tài liệu:** [R2] NVIDIA NCCL, ReduceScatter và AllGather.

## Slide 5 - Vì sao Communication làm tăng Step Time?

**Thời gian:** 1:00; mốc **4:00–5:00**.

**Thông điệp chính:** Communication chưa được overlap và việc chờ workers có thể kéo dài đường găng.

**Giải thích kỹ thuật:** DDP dùng autograd hooks và gradient buckets để đồng bộ trong Backward. Không dùng công thức cộng toàn bộ thời gian compute và toàn bộ communication như một phép đo chính xác khi hai phần overlap. Stragglers có thể do dữ liệu, compute, mạng hoặc contention; không quy mọi chậm trễ về topology.

**Kịch bản nói:**

“Điểm quan trọng là một training step không chỉ có tính toán. DDP có thể bắt đầu đồng bộ khi Backward còn đang chạy, tức overlap compute với communication. Nhưng phần trao đổi chưa được che vẫn nằm trên đường găng: phải hoàn thành nó thì bước cập nhật mới tiếp tục được.

Nếu collective truyền chậm, kết quả chung đến muộn. Nếu một worker tính toán hoặc truyền dữ liệu chậm hơn, các workers khác có thể phải chờ tại các điểm đồng bộ. Thêm GPU cũng làm xuất hiện thêm trao đổi, nên hiệu quả không chỉ phụ thuộc số GPU.

Điều này dẫn đến câu hỏi phần tiếp theo: các workers đang giao tiếp qua những đường phần cứng nào?”

**Cách giải thích hình:** Slide dùng block và các ý cơ chế, không có biểu đồ hiệu năng. Dành khoảng 5 giây nhấn từ “overlap” và “phần chưa được che”; không nêu phần trăm overhead không đo được.

**Chuyển tiếp:** “Ta đi từ mô hình training xuống cấu trúc vật lý của GPU cluster.”

**Tài liệu:** [R1] DDP, gradient sync và skewed speeds; [R12] DDP design note.

## Slide 6 - GPU Node, Rack, Block và Cluster

**Thời gian:** 0:55; mốc **5:00–5:55**.

**Thông điệp chính:** Cluster có nhiều cấp tổ chức; vị trí workers xác định những liên kết chúng cần dùng.

**Giải thích kỹ thuật:** Sơ đồ tác giả mô tả hierarchy Kueue thường dùng: nhiều Nodes trong Rack, nhiều Racks trong Block. Cloud có thể biểu diễn thêm host/sub-block và VM; không đồng nhất mọi Kubernetes Node với một host vật lý. Hình chỉ vẽ hai GPU mỗi Node để dễ đọc, không chỉ định cấu hình GPU SKU.

**Kịch bản nói:**

“Một Node là máy hoặc VM chứa GPU workers. Nhiều máy có thể nằm trong một Rack; nhiều Rack có thể được nhóm thành Block, rồi thành Cluster. Hình ở đây là mô hình tổng quát để đọc topology.

Đi theo đường bên trong Node, ta thấy GPU có thể trao đổi qua các kết nối cục bộ. Khi sang Node khác, dữ liệu đi qua các thành phần mạng. Nếu workers trải qua nhiều domains, đường communication cũng thay đổi.

Các tên và cấp topology cần bám vào hệ thống thực tế. Một nhãn Rack tự đặt chỉ có ích khi phản ánh đúng cấu trúc vật lý.”

**Cách giải thích hình:** Khoảng 10 giây chỉ Node → Rack → Block; đường đứt là liên kết xuyên rack minh họa. Nêu rõ đây là sơ đồ tác giả dựa trên cơ chế, không phải ảnh kiến trúc Google Cloud.

**Chuyển tiếp:** “Trước hết xem một ví dụ intra-node có thật từ NVIDIA.”

**Tài liệu:** [R6] Kueue topology model; [R3] GKE GPUs.

## Slide 7 - Intra-node: GPU và NVSwitch

**Thời gian:** 1:10; mốc **5:55–7:05**.

**Thông điệp chính:** NVLink/NVSwitch cung cấp một fabric giữa các GPUs trên phần cứng phù hợp.

**Giải thích kỹ thuật:** Hình trích nguyên pixel vùng GPU/NVSwitch từ sơ đồ DGX H100/H200. Tám GPU xanh lá và bốn NVSwitch xanh ngọc còn đủ trong vùng trích. Các đường/nối bị cắt ở rìa tiếp tục tới thành phần ngoài vùng hình; đây không phải sơ đồ đầy đủ của Node. PCIe phục vụ các kết nối I/O khác trong sơ đồ gốc. Không áp cấu hình DGX này cho GKE/A3 hoặc mọi GPU instance. Một số rack-scale systems có NVLink domain vượt qua một instance.

**Kịch bản nói:**

“Đây là một ví dụ phần cứng cụ thể: DGX H100/H200 của NVIDIA. Mình trích vùng GPU và NVSwitch từ sơ đồ gốc để các thành phần chính đủ lớn khi trình chiếu.

Hàng xanh lá là tám GPU. Các khối xanh ngọc phía dưới là NVSwitch, kết nối GPUs trong NVLink fabric. Ý cần nhớ là GPU trong một hệ thống phù hợp có thể dùng đường giao tiếp cục bộ chuyên dụng.

PCIe cũng có vai trò nối các thành phần I/O, nhưng không nên gọi mọi đường GPU–NVSwitch trong hình là PCIe. Ta cũng không được suy ra mọi GPU trên Google Cloud có kiến trúc này. Đây là ví dụ intra-node để phân biệt với communication qua mạng giữa Nodes.”

**Cách giải thích hình:** Khoảng 15 giây lần theo GPU 0/1 xuống NVSwitch xanh ngọc. Không giải thích từng sợi hoặc số bandwidth; sơ đồ đầy đủ được giữ trong asset gốc. Chỉ rõ phần ngoài crop không nằm trong hình đang trình chiếu.

**Chuyển tiếp:** “Khi sang instance khác trên Google Cloud, đường communication được tổ chức ra sao?”

**Tài liệu:** [R15] NVIDIA DGX H100/H200 User Guide; [R4] khác biệt GPU machines.

## Slide 8 - Inter-node Communication trên Google Cloud

**Thời gian:** 1:05; mốc **7:05–8:10**.

**Thông điệp chính:** Hệ thống có thể tách GPU traffic và host/storage traffic để phục vụ communication.

**Giải thích kỹ thuật:** Ảnh Google ghi rõ A3U/A4. A3U nghĩa là A3 Ultra. Titanium NICs nối host/storage planes; CX7 NICs phục vụ GPU-to-GPU qua RoCE/RDMA VPC. RoCE là RDMA over Converged Ethernet, không phải InfiniBand. Không khái quát số VPC hoặc NICs trong ảnh thành quy tắc chung cho tất cả GKE GPU types.

**Kịch bản nói:**

“Hình này đến từ tài liệu Google Cloud và ghi rõ kiến trúc A3 Ultra, A4. Bên trái là máy có CPU và GPUs. Traffic được tách theo hai mục đích.

Nhánh trên, qua Titanium NICs, phục vụ host và storage. Nhánh dưới dùng NVIDIA CX7 NICs và RDMA-enabled VPC cho GPU-to-GPU communication. Việc tách đường giúp GPU traffic có một network plane riêng.

Trong GPU clusters nói chung ta có thể gặp Ethernet và InfiniBand. Riêng ảnh này dùng RoCE, tức RDMA trên Ethernet. Những machine types khác có cấu hình khác; vì thế cần xem đúng tài liệu của phần cứng đang sử dụng.”

**Cách giải thích hình:** Khoảng 12 giây lần theo nhánh Titanium → host/storage rồi nhánh CX7 → RDMA VPC → máy khác. Tập trung đọc các khối chính, không đọc toàn bộ dòng chữ nhỏ.

**Chuyển tiếp:** “Để đánh giá các đường này, ta cần phân biệt bandwidth và latency.”

**Tài liệu:** [R16] Google GPU networking overview; [R4] GPU machine series.

## Slide 9 - Bandwidth, Latency và Communication Overhead

**Thời gian:** 0:50; mốc **8:10–9:00**.

**Thông điệp chính:** Kích thước/tần suất trao đổi và tài nguyên dùng chung quyết định loại bottleneck.

**Giải thích kỹ thuật:** Bandwidth là tốc độ truyền dữ liệu; latency là độ trễ của một trao đổi. Contention có thể làm effective bandwidth giảm hoặc độ trễ tăng. Những đặc điểm này cùng communication pattern ảnh hưởng overhead; khoảng cách vật lý đơn thuần không đủ dự đoán performance.

**Kịch bản nói:**

“Bandwidth cho biết có thể truyền bao nhiêu dữ liệu mỗi giây. Gradient tensors lớn thường nhạy với khả năng truyền này. Latency là độ trễ của một trao đổi, đáng kể khi chương trình lặp nhiều trao đổi ngắn.

Ngoài ra còn có contention, khi các luồng traffic cùng dùng một liên kết hay tài nguyên. Vì intra-node và inter-node đi qua phần cứng khác nhau, cùng số GPU chưa nói lên overhead giống nhau.

Do đó, ta cần xem cả workload, đường communication và mức tranh chấp thực tế, thay vì giả định một cấp topology luôn nhanh hơn với một hệ số cố định.”

**Cách giải thích hình:** Dùng ba hàng trong bảng như ba câu hỏi kiểm tra; không coi bảng là số liệu benchmark.

**Chuyển tiếp:** “Scheduling có thể sử dụng hiểu biết topology này để chọn vị trí workers.”

**Tài liệu:** [R5] NCCL Overview; [R4], [R16] Google networking.

## Slide 10 - Topology-Aware Scheduling: Availability và Locality

**Thời gian:** 1:00; mốc **9:00–10:00**.

**Thông điệp chính:** Tổng capacity và capacity trong domain là hai điều khác nhau.

**Giải thích kỹ thuật:** Tình huống tác giả dựng: Block A có hai racks, mỗi rack hai nodes còn ba GPU mỗi node. Job cần tám Pods, một GPU/Pod. Quota, CPU, RAM và các điều kiện khác đủ. Không có yêu cầu về cùng một GPU device trong Node; ví dụ xét locality giữa Nodes.

**Kịch bản nói:**

“Resource Availability trả lời còn bao nhiêu tài nguyên. Resource Locality trả lời tài nguyên đó nằm ở đâu. Topology-Aware Scheduling xét cả hai khi chọn domain cho workers.

Trong ví dụ, mỗi Rack có hai Nodes, mỗi Node còn ba GPU. Một Rack còn sáu, cả Block còn mười hai. Job cần tám GPU, nên đủ tổng capacity, nhưng không Rack nào chứa được cả job.

Điểm quan trọng là một yêu cầu locality có thể làm thay đổi tính khả thi của placement. Vì vậy, kiểm tra tổng GPU trước rồi chia workers tùy ý chưa giải quyết đầy đủ bài toán.”

**Cách giải thích hình:** Khoảng 12 giây cộng 3 + 3 = 6 ở từng rack rồi so 6 với nhu cầu 8. Sơ đồ tự dựng, không gán cho tác giả nguồn chính thức.

**Chuyển tiếp:** “Ta muốn locality là điều kiện bắt buộc hay một ưu tiên có thể nới?”

**Tài liệu:** [R6] Kueue TAS; [R8] PodSetTopologyRequest.

## Slide 11 - Required và Preferred Topology

**Thời gian:** 0:55; mốc **10:00–10:55**.

**Thông điệp chính:** Required và Preferred diễn đạt mức ràng buộc locality khác nhau.

**Giải thích kỹ thuật:** Required cùng rack chờ khi không domain nào chứa được PodSet. Preferred xét các cấp rộng hơn; có thể phân qua domains khi cần và đủ capacity. Fallback không phải timeout. Đổi locality lấy thời gian chờ là trade-off ở mức chính sách, không bảo đảm thời gian hoàn thành job tối ưu.

**Kịch bản nói:**

“Tiếp tục ví dụ vừa rồi: nếu Required là cùng Rack, không Rack nào đủ tám GPU, nên workload phải chờ admission. Nếu chỉ Preferred cùng Rack, Kueue có thể xét cấp rộng hơn là Block; mười hai GPU trống trong Block có thể đáp ứng yêu cầu tám workers.

Required phù hợp khi locality là điều kiện cần của workload. Preferred cho phép ưu tiên locality nhưng vẫn có fallback khi không vừa domain mong muốn.

Locality chặt hơn có thể làm tăng thời gian chờ. Ngược lại, nới locality có thể tăng communication overhead. Không có lựa chọn nào bảo đảm speedup cho mọi workload.”

**Cách giải thích hình:** Khoảng 6 giây đối chiếu hai block; nhắc fallback là theo cấp topology, không đợi một timeout rồi bỏ Required.

**Chuyển tiếp:** “Kueue đặt quyết định đó vào quy trình admission của Kubernetes.”

**Tài liệu:** [R6] User-facing APIs; [R8] required/preferred fields.

## Slide 12 - Kueue: luồng Admission tổng quan

**Thời gian:** 1:05; mốc **10:55–12:00**.

**Thông điệp chính:** Kueue xét admission trước khi Pods được kube-scheduler binding.

**Giải thích kỹ thuật:** Hình chính thức được chuyển SVG → PDF vector, rồi trích dải admission để dễ đọc. Bản đầy đủ được giữ trong assets. Các nhánh Autoscaler và external checks là tùy chọn. Chữ nodeAffinity trong hình overview mô tả khái quát constraint injection theo flavor; không dùng nó để thay thế mô tả TAS v0.14.0 áp NodeSelector ở slide 13. Admitted không đồng nghĩa mọi Pod đã Running.

**Kịch bản nói:**

“Đây là vùng admission trích từ hình hoạt động tổng quan chính thức của Kueue. Admin chuẩn bị flavors và queues; user gửi job qua Kubernetes API. Kueue xét quota và các chính sách để quyết định workload nào được admit, rồi áp các ràng buộc cần thiết.

Sau admission, Job Controller tạo Pods và kube-scheduler thực hiện binding Pods vào Nodes phù hợp. Vì vậy, admission và Pod binding là những bước có vai trò khác nhau.

Hình nguồn còn có các nhánh autoscaling và external checks tùy chọn. Mình không dùng hình overview này như sơ đồ TAS đầy đủ; slide tiếp theo sẽ bổ sung các đối tượng và topology assignment theo phiên bản Kueue cụ thể.”

**Cách giải thích hình:** Khoảng 12 giây đi theo Admin/User → API Server → Kueue. Giải thích phần dưới của hình gốc bằng hai dòng chữ về Job Controller và kube-scheduler; không nói phần đã crop là một workflow TAS hoàn chỉnh.

**Chuyển tiếp:** “Với TAS, Kueue cần thêm topology definition và requirements của PodSet.”

**Tài liệu:** [R17] Kueue Overview; [R11] Kubernetes Scheduler.

## Slide 13 - Kueue TAS: Admission đến Pod Placement

**Thời gian:** 1:15; mốc **12:00–13:15**.

**Thông điệp chính:** Kueue chọn topology assignment; kube-scheduler bind Pods theo các ràng buộc được áp.

**Giải thích kỹ thuật:** Ghim Kueue v0.14.0, API `kueue.x-k8s.io/v1beta1`, TAS Beta/on by default. Topology xác định node-label levels; ResourceFlavor tham chiếu `spec.topologyName`. ClusterQueue quản lý quota/flavors, LocalQueue trỏ ClusterQueue. PodTemplate annotation được tích hợp thành PodSet requirements. TAS controller áp NodeSelector theo assignment và gỡ topology gate. Cấp thấp nhất hostname có thể chỉ định Node cụ thể. Flow dùng capacity sẵn có, không có Provisioning AdmissionCheck.

**Kịch bản nói:**

“Ví dụ TAS dùng Kueue 0.14.0. Admin khai báo Topology theo các node labels, ResourceFlavor tham chiếu Topology, rồi cấu hình queues và quota. Phía user, annotation nằm trên PodTemplate để diễn đạt yêu cầu locality cho PodSet.

Kueue xét quota cùng topology capacity và ghi topology assignment cho nhóm Pods. Controllers tạo Pods, áp node selectors tương ứng assignment, rồi phía TAS gỡ topology scheduling gate. Sau đó kube-scheduler kiểm tra các Nodes phù hợp và thực hiện binding.

Kueue có tham gia quyết định vị trí. Nếu topology xuống đến hostname, assignment có thể chỉ định Node cụ thể. Điều cần phân biệt là topology assignment của workload và thao tác binding từng Pod. Nhãn topology cũng phải phản ánh phần cứng thật.”

**Cách giải thích hình:** Khoảng 12 giây đọc hai ô đầu vào, ô admission, ô controllers, rồi scheduler. Annotation dưới hình là Required; annotation Preferred có cùng prefix và kết thúc bằng `podset-preferred-topology`. Các chi tiết API được lưu trong references, không đọc YAML dài.

**Chuyển tiếp:** “Ta áp dụng ý tưởng đó vào placement của một job tám workers.”

**Tài liệu:** [R7] release; [R8] Workload API; [R9] ResourceFlavor; [R10] TAS controller; [R11] binding.

## Slide 14 - Case Study: 8-GPU Worker Placement

**Thời gian:** 1:05; mốc **13:15–14:20**.

**Thông điệp chính:** Cùng tám GPU nhưng khác phạm vi communication.

**Giải thích kỹ thuật:** Kịch bản tác giả dựng: hai racks, hai nodes/rack, bốn GPU trống/node cùng loại. Tám workers = tám Pods = tám GPU requests; không thêm coordinator dùng GPU ngoài tám worker. Hai hình là hai phương án trên cùng snapshot, không phải hai job chạy đồng thời. CPU/RAM/quota/taints và các điều kiện khác đáp ứng. Giả định liên kết xuyên rack là nút thắt; không có benchmark hoặc phần trăm cải thiện.

**Kịch bản nói:**

“Job cần tám workers, mỗi worker một GPU. Cluster có hai Rack, mỗi Rack hai Nodes, mỗi Node bốn GPU trống. Hai bên dùng cùng trạng thái tài nguyên ban đầu.

Bên trái, bốn workers ở Node A1 và bốn ở A2, toàn bộ trong cùng Rack. Bên phải, mỗi Node hai workers, nên job trải qua hai Rack. Ô xanh là workers của job; ô trắng là GPU chưa dùng.

Cả hai phương án đều đủ tám GPU. Nếu liên kết xuyên Rack là nút thắt, locality của phương án trái có thể giảm overhead. Nhưng đây là kịch bản minh họa kiến trúc, không phải thử nghiệm, nên không suy ra nhanh hơn bao nhiêu phần trăm.”

**Cách giải thích hình:** Khoảng 12 giây đếm 4 + 4 và 2 + 2 + 2 + 2; chỉ liên kết xuyên rack đại diện. Không nói scheduler không xét topology bắt buộc sẽ phân tán như bên phải. Snapshot này khác slide 10.

**Chuyển tiếp:** “Từ đó, mình chốt lại thông điệp về WHERE.”

**Tài liệu:** [R6], [R8] cho cơ chế; số Nodes/GPU và placement là giả định tự xây dựng.

## Slide 15 - Key Takeaways

**Thời gian:** 0:40; mốc **14:20–15:00**.

**Thông điệp chính:** Có đủ GPU chưa chắc đã đủ; vị trí GPU cũng ảnh hưởng hiệu quả training.

**Giải thích kỹ thuật:** Tóm tắt có điều kiện, không cam kết topology-aware placement luôn cải thiện performance. Nhắc đúng ranh giới Kueue admission và kube-scheduler binding.

**Kịch bản nói:**

“Distributed Training cần cả compute và communication. Topology-Aware Scheduling kết hợp capacity với locality; Kueue hỗ trợ topology-aware admission, còn kube-scheduler thực hiện Pod binding.

Có đủ GPU chưa chắc đã đủ; vị trí của các GPU cũng quyết định hiệu quả huấn luyện phân tán.

Sau khi xác định khi nào workload được chạy và các GPU workers nên được đặt ở đâu, vấn đề tiếp theo là làm thế nào để sử dụng và chia sẻ GPU hiệu quả hơn?”

**Cách giải thích hình:** Không thêm ảnh mới. Dừng một nhịp ở thông điệp kết thúc, đọc câu handoff rồi nhường phần trình bày cho thành viên Part 3.

**Chuyển tiếp:** Câu cuối giữ nguyên nội dung handoff nhóm yêu cầu.

**Tài liệu:** [R1], [R6], [R11].

## Câu hỏi dự phòng, ngoài 15 phút

- **Có đủ tổng GPU mà job vẫn chờ?** Kiểm tra domain Required, quota và các ràng buộc tài nguyên/scheduling khác.
- **TAS có tự đo latency hoặc cấu hình NVLink không?** Ví dụ dùng topology labels và capacity; không có cơ chế tự benchmark hay cấu hình interconnect.
- **Vì sao không luôn gom trong một Node?** Có thể không đủ GPUs, VRAM hoặc tài nguyên khác; mục tiêu locality phải đi cùng tính khả thi.
- **Hình nguồn có chứng minh speedup của case study không?** Không. Hình nguồn giải thích cơ chế/phần cứng; case study là minh họa không có số liệu đo.
- **Node có luôn bằng host vật lý không?** Không; trong cloud Node có thể là VM. Mô hình labels phải phản ánh nền tảng triển khai thực.
