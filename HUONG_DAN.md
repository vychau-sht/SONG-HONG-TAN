# SHT/PBG — Hệ điều hành Sản xuất & Giá thành (100% Python)

## Cấu trúc thư mục
```
sht_app/
├── Trang_chu.py              ← file chính, chạy: streamlit run Trang_chu.py
├── database.py                ← lớp truy cập SQLite (thay Google Sheets)
├── utils.py                   ← đăng nhập, xuất Excel, style biểu đồ dùng chung
├── costing_engine.py           ← engine tính giá thành ABC (đúng công thức Word gốc)
├── requirements.txt
├── sht_pbg.db                  ← tự tạo khi chạy lần đầu (đừng xoá khi đã có dữ liệu)
└── pages/
    ├── 1_📦_Danh_Muc.py                    (MENU CHA: Danh mục — NCC / NVL / Sản phẩm)
    ├── 2_🏭_San_Xuat.py                     (MENU CHA: Sản xuất — BOM / Routing)
    ├── 3_💰_Chi_Phi_Gia_Thanh.py            (MENU CHA: Chi phí & Giá thành — Engine ABC)
    ├── 4_📈_Bao_Gia_NCC.py                  (MENU CHA: Báo giá NCC — xếp hạng giá)
    ├── 5_🧑‍🤝‍🧑_Khach_Hang_Don_Hang.py        (MENU CHA: Khách hàng & Đơn hàng)
    └── 6_📦_Kho_Van.py                      (MENU CHA: Kho vận — Nhập/Xuất, Tồn kho)
    └── 7_✅_QC.py                           (MENU CHA: Kiểm soát chất lượng — QC Đầu vào/Đầu ra)
```

## Cập nhật lên bản đã deploy (Streamlit Cloud)
Vì bạn đã đưa code lên GitHub + deploy rồi, mỗi lần mình gửi file mới, bạn chỉ cần:
```bash
# copy các file mới đè vào thư mục repo local, rồi:
git add .
git commit -m "Thêm module QC"
git push
```
Streamlit Cloud sẽ tự động rebuild và cập nhật app (thường mất 1-2 phút).

## Lỗi thường gặp khi chạy trên Windows (Command Prompt)
Nếu bạn thấy lỗi `Could not open requirements file` hoặc `File does not exist: Trang_chu.py`,
nguyên nhân là Command Prompt đang đứng ở thư mục khác (vd `C:\Users\Admin>`), chưa vào
đúng thư mục đã giải nén. Khắc phục:
```bash
cd đường_dẫn_tới_thư_mục\sht_app
pip install -r requirements.txt
streamlit run Trang_chu.py
```

## 📦 Gói đầy đủ này gồm gì (bản đồng bộ mới nhất)
- Toàn bộ 9 trang (`pages/1...` → `pages/9...`) + `Trang_chu.py`, `database.py`,
  `costing_engine.py`, `utils.py`, `requirements.txt`.
- **`sht_pbg.db`** — đã nạp SẴN dữ liệu thật từ file JSON gốc bạn cung cấp (NCC, NVL,
  sản phẩm, BOM, routing, chi phí, báo giá, khách hàng, đơn hàng, QC, khảo sát, users...).
  ⚠️ Nếu bạn đã tự nhập dữ liệu khác trên app đang chạy, upload đè file này sẽ
  **thay thế** dữ liệu đó — hãy xuất Excel backup trước nếu cần giữ lại.
- **`seed_data.py`** — script để nạp lại dữ liệu từ 1 file JSON mới (nếu sau này bạn
  có bản cập nhật), chạy: `python3 seed_data.py duong_dan_file.json`.

## Cách upload đồng bộ 1 lần lên GitHub (khuyến nghị)
1. Giải nén toàn bộ gói này.
2. Vào GitHub repo → **Add file → Upload files**.
3. Kéo thả TẤT CẢ file/thư mục ở gốc (bao gồm `sht_pbg.db`) + kéo cả thư mục `pages/`
   vào cùng lúc — GitHub tự ghi đè file trùng tên, thêm file mới.
4. Commit changes → đợi Streamlit Cloud tự rebuild (~1-2 phút).

## Cấu trúc điều hướng (theo yêu cầu của bạn)
- **MENU CHA** = danh sách trang bên sidebar trái (Streamlit tự sinh từ thư mục `pages/`)
- **MENU CON** = các tab lớn ở đầu mỗi trang (vd trong "Danh mục": Nhà cung cấp / Nguyên vật liệu / Sản phẩm)
- **SHEET** = 1 khối dữ liệu cụ thể bên trong Menu con (vd "SHEET: Nhà cung cấp")
- **TAB** = 3 tab con trong mỗi SHEET: `📋 Danh sách` → `➕ Nhập liệu` → `📊 Biểu đồ`
- Mọi ô nhập liệu được xếp theo cột (st.columns) để phím **Tab** trên bàn phím chuyển
  đúng thứ tự trái→phải, trên→dưới.
- **Mỗi SHEET có tối thiểu 5 biểu đồ** trong tab "📊 Biểu đồ".

## Chạy thử trên máy (local)
```bash
pip install -r requirements.txt
streamlit run Trang_chu.py
```
Mở trình duyệt tại http://localhost:8501
Tài khoản mặc định: **admin / admin123**

## Triển khai lên Streamlit Community Cloud (miễn phí, có URL public)
1. Tạo 1 repo GitHub mới, đẩy (push) TOÀN BỘ các file/thư mục ở trên lên (giữ nguyên
   cấu trúc thư mục `pages/`).
2. Vào https://share.streamlit.io → Đăng nhập bằng GitHub → "New app".
3. Chọn đúng repo vừa tạo, nhánh (branch) `main`, Main file path = `Trang_chu.py`.
4. Bấm "Deploy". Sau ~1-2 phút sẽ có URL dạng
   `https://<tên-app>.streamlit.app` — đây là URL public bạn cần.

## Lưu trữ dữ liệu (KHÔNG còn Google Sheets/Docs)
Toàn bộ dữ liệu nằm trong 1 file `sht_pbg.db` (SQLite) ngay trong thư mục app.
- **Lưu ý khi deploy Streamlit Cloud**: ổ đĩa của Streamlit Cloud là *tạm thời* —
  nếu app "ngủ" lâu ngày hoặc được deploy lại, file `sht_pbg.db` có thể bị reset.
  Vì vậy hãy dùng nút "📥 Xuất TOÀN BỘ dữ liệu (Excel)" ở sidebar để backup định kỳ.
  (Nếu bạn cần lưu trữ bền vững tuyệt đối trên cloud, bước tiếp theo có thể là
  chuyển sang một database ngoài như Supabase/PostgreSQL — mình có thể làm nếu bạn cần.)

## Đăng nhập / phân quyền
Bảng `users` trong SQLite quản lý tài khoản. Đây là bản đơn giản (1 vai trò `role`
lưu dạng text). Nếu bạn cần phân quyền chi tiết theo từng Menu cha/Menu con
(giống hệ thống ký duyệt phức tạp trong file gốc), báo mình để làm ở giai đoạn sau.

## Phạm vi đã hoàn thành (Giai đoạn 1) vs còn lại
✅ Danh mục NCC/NVL/Sản phẩm · BOM · Routing · Chi phí trực tiếp/gián tiếp ·
Engine tính giá thành ABC (đúng 5 bước công thức Word) · Báo giá NCC & xếp hạng ·
Xuất Excel mọi nơi · Đăng nhập · Biểu đồ (≥5/sheet)

⏳ Chưa làm (gửi MENU tổng bạn đang xây để mình sắp xếp thứ tự ưu tiên):
QC input/output, khảo sát khách hàng, ký duyệt điện tử/uỷ quyền, tuyển dụng/đào tạo/
chấm công, dự án cải tiến (5-Why/8D/FMEA), báo cáo tài chính (bảng cân đối, đầu tư)...
