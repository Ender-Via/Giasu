# Tài liệu nhóm

Đặc tả yêu cầu (SRS) và quy ước của dự án. Chỉ GitHub owner (SV2 Trí Kiệt) sửa thư mục này (D02);
thấy sai, thiếu hay mâu thuẫn thì báo GitHub owner, không tự chọn một bên rồi code theo.

Biểu mẫu OOAD (`.xlsx` trên Drive nhóm) là **bản xuất** từ bộ tài liệu này để nộp, không phải nguồn
để code. Cuối kỳ (thẻ S13, S14) các sheet được chép lại từ đây.

## Cấu trúc

| Đường dẫn | Nội dung |
| :-- | :-- |
| `DECISIONS.md` | Quyết định `Dxx`: công nghệ, phạm vi MVP, tên gọi, các quy tắc chốt lại so với biểu mẫu |
| `business/business-rules.md` | Module ↔ FR ↔ người làm; trạng thái hợp lệ; giá trị liệt kê; quy tắc `BR-xx`; sự kiện thông báo |
| `business/user-roles.md` | Ba vai trò, phạm vi dữ liệu `BR-SCOPE-xx`, ma trận vai trò × quyền |
| `requirements/functional-requirements.md` | FR theo module: luồng, quy tắc, phân quyền, API dự kiến |
| `requirements/acceptance-criteria.md` | `AC-<MODULE>-xx` dạng Cho trước / Khi / Thì, có dòng truy vết |
| `requirements/non-functional-requirements.md` | NFR-01–06 có cách đo, checklist bảo mật tối thiểu |
| `frontend/ui-screens.md` | Mã `SCR-*`, bản đồ màn hình, đặc tả từng màn hình |
| `frontend/design-system.md` | Màu, chữ, tông trạng thái, component dùng chung, responsive |
| `frontend/frontend-conventions.md` | Thư mục một màn hình, query key, form, lỗi, danh sách cấm |
| `frontend/frontend-architecture.md` | Routing, phiên đăng nhập, cách gọi API |
| `api/api-conventions.md` | Khuôn module backend, route, status code, 400/409, 403/404, checklist PR |
| `api/da-trien-khai.md` | Những gì **đã có** trên `develop` |
| `database/database-design.md` | Bảng và cột (SV3 giữ phần ERD) |
| `testing/testing-strategy.md` | xUnit, Postman, dữ liệu test, checklist kiểm một màn hình |
| `onboarding/team-workflow.md` | Luật nhóm, sprint 3 ngày, nhánh, commit, PR, Definition of Done |

## Khi tài liệu mâu thuẫn

Tài liệu đứng trước đúng, tài liệu đứng sau phải sửa theo:

1. `DECISIONS.md`
2. `business/business-rules.md` và `business/user-roles.md`
3. `requirements/functional-requirements.md`, rồi `requirements/acceptance-criteria.md`
4. `database/database-design.md`, `api/api-conventions.md`
5. `frontend/ui-screens.md` về hành vi; `frontend/design-system.md` về hình thức;
   `frontend/frontend-conventions.md`, `frontend/frontend-architecture.md` về cách viết code
6. Biểu mẫu OOAD, mô tả thẻ trong file kế hoạch, chú thích trong code, code hiện có

Đổi một quy tắc thì sửa từ trên xuống: D → BR → FR → AC → SCR → code.

## Làm việc gì thì đọc file nào

| Việc | Đọc |
| :-- | :-- |
| Ngày đầu tiên | `onboarding/team-workflow.md`, `README.md` ở gốc repo |
| Thẻ backend | FR và AC của thẻ; BR được nhắc; `business/user-roles.md` §3; `api/api-conventions.md`; `database/database-design.md` khi đụng bảng |
| Thẻ frontend | Mục SCR và §4 của `frontend/ui-screens.md`; AC ghi ở dòng "Yêu cầu"; `frontend/design-system.md`; `frontend/frontend-conventions.md` |
| Thẻ test | AC của module; `testing/testing-strategy.md` |
| Review PR backend | `api/api-conventions.md` §9; AC của thẻ |
| Review PR frontend | Mục SCR; `testing/testing-strategy.md` §3.3, §3.4 |
| Gặp mã `Dxx` trong code | `DECISIONS.md` |

## Mã định danh

| Mã | Ở đâu |
| :-- | :-- |
| `FR-01`–`FR-36`, `NFR-01`–`NFR-06`, `US-xx`, `UC-xx`, `SSD-xx` | Giữ nguyên số của biểu mẫu OOAD |
| `BR-xx`, `BR-SCOPE-xx` | `business/` |
| `AC-<MODULE>-xx` | `requirements/acceptance-criteria.md` |
| `SCR-<NHÓM>-xx` | `frontend/ui-screens.md` (cột cuối §3 ghi mã `UI-xx` tương ứng của biểu mẫu) |
| `Dxx` | `DECISIONS.md` |
| `Sxx-yy` | Mã thẻ trong file kế hoạch |

Tiêu đề thẻ, tiêu đề PR, tên test và chú thích code đều trích các mã này để truy vết được vào sheet
**P4_02_TruyVet** cuối kỳ.
