# Tài liệu nhóm

Bộ tài liệu tối thiểu để bắt tay vào code. Chỉ GitHub owner (SV2 Trí Kiệt) sửa thư mục này (D02);
thấy sai hoặc thiếu thì báo GitHub owner.

| File | Đọc khi | Nội dung |
| :-- | :-- | :-- |
| `team-workflow.md` | **Ngày đầu tiên** | Luật nhóm, sprint 3 ngày, nhánh, commit, PR, Definition of Done |
| `conventions.md` | **Trước thẻ đầu tiên** | Khuôn thêm module backend, quy ước API, quy ước frontend |
| `DECISIONS.md` | Gặp mã `Dxx` | Quyết định kỹ thuật và các quy tắc đã chốt lại so với biểu mẫu |
| `business-rules.md` | Mỗi thẻ | Module ↔ FR ↔ người phụ trách, trạng thái hợp lệ, quy tắc `BR-xx`, sự kiện thông báo |
| `data-model.md` | Thẻ backend | Bảng và cột khởi điểm |

Yêu cầu gốc (FR, NFR, User Story, Use Case, SSD) nằm trong **biểu mẫu OOAD** (`Biểu mẫu OOAD.xlsx`
trên Drive nhóm). Thứ tự ưu tiên khi hai nguồn khác nhau:
`DECISIONS.md` > `business-rules.md` > biểu mẫu OOAD.

## Mã định danh

| Mã | Ở đâu |
| :-- | :-- |
| `FR-xx`, `NFR-xx`, `US-xx`, `UC-xx`, `SSD-xx` | Biểu mẫu OOAD |
| `BR-xx` | `business-rules.md` §3 |
| `Dxx` | `DECISIONS.md` |
| `UI-xx` | Biểu mẫu OOAD sheet P3D_05 (SV2 điền ở S05) |
| `Sxx-yy` | Mã thẻ trong file kế hoạch |

Tiêu đề thẻ, tiêu đề PR và chú thích code đều trích các mã này để truy vết được vào sheet
**P4_02_TruyVet** lúc cuối kỳ.
