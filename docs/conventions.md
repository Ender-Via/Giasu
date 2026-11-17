# Quy ước code

Đọc hết file này trước thẻ đầu tiên. Mẫu đã chạy được: module **Auth** (backend) và trang
`/login` (frontend) — làm theo đúng khuôn đó.

Viết bằng tiếng Việt: chú thích, message lỗi, commit. Tên biến, hàm, class bằng tiếng Anh.

---

## 1. Backend

### 1.1 Thêm một module — 7 bước

Ví dụ module `TutorProfile`:

| # | Lớp | File |
| :-- | :-- | :-- |
| 1 | Domain | `Entities/TutorProfile.cs`, hằng số trạng thái `Constants/TutorProfileStatuses.cs` |
| 2 | Infrastructure | `Persistence/Configurations/TutorProfileConfiguration.cs`, thêm `DbSet` vào `AppDbContext` |
| 3 | Application | `DTOs/TutorProfiles/*Request.cs`, `*Response.cs` — dùng `record`, **không** trả Entity ra ngoài |
| 4 | Application | `Validators/TutorProfiles/*Validator.cs` (FluentValidation, message tiếng Việt) |
| 5 | Application | `Interfaces/ITutorProfileRepository.cs`, `ITutorProfileService.cs`; `Services/TutorProfileService.cs` |
| 6 | Infrastructure | `Persistence/Repositories/TutorProfileRepository.cs` — **chỉ Repository được gọi `AppDbContext`** |
| 7 | API | `Controllers/TutorProfilesController.cs`; đăng ký DI trong `Program.cs` thành một khối riêng của module |

Migration (bước 2 có đổi schema): đọc D11 trước khi tạo.

### 1.2 Nơi đặt logic
- **Controller**: validate request, lấy `userId` từ claim `sub`, gọi Service, đổi kết quả thành
  status code. Không có `if` nghiệp vụ.
- **Service**: toàn bộ quy tắc `BR-xx`, kiểm phạm vi dữ liệu, chuyển trạng thái, gọi
  `INotificationService`. Đây là chỗ viết unit test.
- **Repository**: truy vấn. Lọc phạm vi (`WHERE parent_id = @userId`) ngay trong câu truy vấn.
- Service trả kết quả có kiểu (ví dụ `enum ApplyResult { Ok, NotFound, LimitReached, Closed }`),
  Controller đổi sang status code. Không ném exception cho lỗi nghiệp vụ.

### 1.3 Phân quyền
- Mọi action có `[Authorize(Roles = Roles.Tutor)]` (hoặc ghép hằng số). Không dùng `[Authorize]` trống.
- Bản ghi ngoài phạm vi → **404** (D07).

---

## 2. API

| Mục | Quy ước |
| :-- | :-- |
| Route | `api/<tài-nguyên-số-nhiều-kebab>`: `api/tutor-profiles`, `api/tutor-requests/{id}/applications` |
| Hành động đổi trạng thái | `POST api/<tài-nguyên>/{id}/<động-từ>`: `.../submit`, `.../withdraw`, `.../approve` |
| JSON | camelCase; enum là chuỗi (`"PendingReview"`); thời gian UTC, tên trường kết thúc `Utc` |
| Phân trang | Query `page` (từ 1), `pageSize` (mặc định 20, tối đa 100); `data = { items, page, pageSize, totalCount }` |
| Response | Luôn `ApiResponse<T>` (D04) |

### Status code
| Code | Khi nào |
| :-- | :-- |
| 200 | Đọc, sửa, đổi trạng thái thành công |
| 201 | Tạo mới — kèm bản ghi vừa tạo trong `data` |
| 400 | Dữ liệu tự nó sai (validator) |
| 401 | Chưa đăng nhập, token hết hạn hoặc đã thu hồi |
| 403 | Sai vai trò, hoặc đang bị khóa tính năng (BR-10) |
| 404 | Không tồn tại **hoặc** không thuộc phạm vi của mình |
| 409 | Xung đột trạng thái: chuyển trạng thái không hợp lệ, vượt giới hạn 5 phiếu, đã thanh toán |
| 429 | Vượt giới hạn đăng nhập |

Mỗi endpoint mới phải có request trong Postman Collection (`docs/testing/`): 1 ca đúng, 1 ca 400,
1 ca sai vai trò.

---

## 3. Frontend

| Mục | Quy ước |
| :-- | :-- |
| Route | `src/app/(<vai-trò>)/<vai-trò>/<màn-hình>/page.tsx`; khung và menu đã có sẵn cho `admin`, `tutor`, `parent` |
| File riêng của màn hình | `_components/`, `_lib/<tên>-api.ts` (hàm gọi API), `_lib/<tên>-rules.ts` (validate phía client) |
| Dùng chung | `src/components` (Button, Form, Table, Modal, ConfirmDialog, Pagination, StateFeedback…), `src/lib`, `src/types` |
| Gọi API | Chỉ qua `apiClient` (`src/lib/axios.ts`); đọc dữ liệu bằng TanStack Query, ghi bằng `useMutation` |
| Form | React Hook Form cho mọi form |
| Lỗi | `toApiError(error)` rồi hiện `message`/`errors` từ backend; **không** `if (status === 409)` để tự viết message |
| Trạng thái màn hình | Đủ 3 trạng thái: đang tải / lỗi / rỗng (NFR-05) |
| Responsive | Dùng được ở 375 px (không cuộn ngang) và 1280 px; nút bấm cao ≥ 44 px |
| Giao diện tham khảo | Bản prototype EJS 20 màn hình ở thư mục `views/pages` (repo cũ `D:\Giasu`) |

Backend chưa xong thì làm giao diện với dữ liệu giả trong `_lib/<tên>-api.ts`, nối API sau.
