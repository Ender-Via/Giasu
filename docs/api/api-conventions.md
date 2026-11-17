# Quy ước backend và API

## 0. Về tài liệu này

Cách viết một module backend và một endpoint để mọi module theo cùng khuôn. **Module mẫu đã chạy:
Auth** (`AuthController` → `AuthService` → `AuthRepository`). Đọc file này trước thẻ backend đầu
tiên; trước khi mở PR thì đi checklist §9.

Viết bằng tiếng Việt: chú thích, message lỗi, commit. Tên biến, hàm, class bằng tiếng Anh.

---

## 1. Nguyên tắc nền

1. **REST:** tài nguyên là danh từ, hành động là HTTP method.
2. **Mọi response đúng một khuôn `ApiResponse<T>`**, kể cả lỗi (D04).
3. **Không endpoint nào thiếu phân quyền.** Chỉ `POST /api/auth/login` và `POST /api/auth/register`
   không cần đăng nhập.
4. **DTO tách khỏi Entity.** Không trả Entity ra ngoài; chỉ lộ đúng thứ vai trò đó được xem.
5. **Đơn giản trước:** không thêm abstraction chỉ để trông chuyên nghiệp, không thêm package khi
   chưa hỏi GitHub owner (D03).

---

## 2. Thêm một module — 7 bước

Ví dụ module `TutorProfile`:

| # | Lớp | File |
| :-- | :-- | :-- |
| 1 | Domain | `Entities/TutorProfile.cs`; hằng số trạng thái `Constants/TutorProfileStatuses.cs` (có `IsValid()`) |
| 2 | Infrastructure | `Persistence/Configurations/TutorProfileConfiguration.cs` (CHECK cho cột trạng thái, FK `Restrict`); thêm `DbSet` vào `AppDbContext` |
| 3 | Application | `DTOs/TutorProfiles/*Request.cs`, `*Response.cs` — `record` |
| 4 | Application | `Validators/TutorProfiles/*Validator.cs` — FluentValidation, message tiếng Việt |
| 5 | Application | `Interfaces/ITutorProfileRepository.cs`, `ITutorProfileService.cs`; `Services/TutorProfileService.cs` |
| 6 | Infrastructure | `Persistence/Repositories/TutorProfileRepository.cs` — **chỉ Repository gọi `AppDbContext`** |
| 7 | API | `Controllers/TutorProfilesController.cs`; đăng ký DI trong `Program.cs` thành một khối riêng của module: Repository → Service → Validator |

Có đổi schema → migration theo D11. Khi merge mà `Program.cs` xung đột: giữ cả hai phía.

### 2.1 Nơi đặt logic

| Lớp | Làm gì | Không làm gì |
| :-- | :-- | :-- |
| Controller | Validate request, lấy `userId` từ claim `sub`, gọi Service, đổi kết quả thành status code | `if` nghiệp vụ, gọi `DbContext` |
| Service | Toàn bộ `BR-xx`, kiểm phạm vi, chuyển trạng thái, gọi `INotificationService`. **Chỗ viết unit test** | Ném exception cho lỗi nghiệp vụ |
| Repository | Truy vấn; lọc phạm vi ngay trong câu truy vấn (`WHERE tutor_id = @userId`) | Quyết định nghiệp vụ |

Service trả kết quả có kiểu, Controller đổi sang status code:

```csharp
public enum SubmitProfileResult { Ok, NotFound, InvalidState, MissingRequirements }
```

### 2.2 Chuyển trạng thái an toàn

Mọi chuyển trạng thái chạy một câu cập nhật **có điều kiện** để hai request cùng lúc chỉ một cái
thành công (NFR-03):

```csharp
var affected = await _db.TutorProfiles
    .Where(p => p.Id == id && p.TutorId == userId
             && (p.Status == TutorProfileStatuses.Draft || p.Status == TutorProfileStatuses.Rejected))
    .ExecuteUpdateAsync(s => s.SetProperty(p => p.Status, TutorProfileStatuses.PendingReview));
// affected == 0 → đọc lại để phân biệt 404 (không có / không phải của mình) với 409 (sai trạng thái)
```

---

## 3. Đặt tên route

| Hạng mục | Quy tắc | Đúng | Sai |
| :-- | :-- | :-- | :-- |
| Tiền tố | luôn `api/` | `api/tutor-profiles` | `tutor-profiles` |
| Tài nguyên | danh từ số nhiều, chữ thường, gạch nối | `api/student-verifications` | `api/StudentVerification` |
| Định danh | tham số route | `api/tutor-profiles/{id}` | `?id=...` |
| Tài nguyên con | lồng tối đa 1 cấp | `api/tutor-profiles/{id}/evidences` | lồng 3 cấp |
| Của chính mình | đoạn `mine` | `api/tutor-profiles/mine` | `?tutorId=` |
| Hành động nghiệp vụ | `POST`, động từ ở cuối | `POST api/tutor-profiles/{id}/submit` | `POST api/submitProfile` |
| Lọc, phân trang | query string | `?status=Pending&page=1` | nhét vào path |

**Phân trang:** `page` (từ 1, mặc định 1), `pageSize` (1–100, mặc định 20); ngoài miền → 400.
`data = { items, page, pageSize, totalCount }`. Danh sách có giới hạn tự nhiên (hồ sơ của mình ≤ 5,
môn học) thì không phân trang.

**JSON:** camelCase; giá trị liệt kê là chuỗi tiếng Anh (`"PendingReview"`); thời gian UTC, tên
trường kết thúc `Utc` (`createdAtUtc`); ngày không có giờ dạng `yyyy-MM-dd`; tiền là số nguyên
đồng.

**Xóa:** không xóa cứng dữ liệu nghiệp vụ. Chỉ có hai endpoint `DELETE`: gỡ minh chứng của hồ sơ
chưa duyệt (BR-26) và bỏ lưu tin (FR-34).

---

## 4. Status code

| Code | Khi nào |
| :-- | :-- |
| 200 | Đọc, sửa, đổi trạng thái thành công |
| 201 | Tạo mới — `data` là bản ghi vừa tạo (hoặc `{ id }`) |
| 400 | Dữ liệu tự nó sai (validator) |
| 401 | Chưa đăng nhập, token hết hạn, đã thu hồi; sai email/mật khẩu |
| 403 | Sai vai trò; hoặc đang bị khóa tính năng (BR-10) |
| 404 | Không tồn tại **hoặc** ngoài phạm vi |
| 409 | Dữ liệu hợp lệ nhưng xung đột trạng thái hiện tại |
| 429 | Vượt giới hạn đăng nhập/đăng ký |
| 500 | Lỗi chưa xử lý — chỉ do `GlobalExceptionHandler` trả |

### 4.1 400 hay 409?

- **400** = dữ liệu gửi lên *tự nó* sai, chưa cần biết DB có gì: thiếu tiêu đề, học phí âm, tệp
  sai định dạng, gửi duyệt khi thiếu điều kiện BR-04 (thiếu là thiếu trong chính hồ sơ).
- **409** = dữ liệu hợp lệ nhưng xung đột với trạng thái hiện tại: email đã dùng, hồ sơ thứ 6,
  sửa hồ sơ đang chờ duyệt, duyệt yêu cầu đã duyệt, ứng tuyển khi đã đủ 5 phiếu.
- Vi phạm `BR-xx` về trạng thái hay giới hạn số lượng gần như luôn là **409**.

### 4.2 403 hay 404 khi đụng dữ liệu người khác?

Gia sư A gọi `GET /api/tutor-profiles/{id hồ sơ của B}`:

- Trả **404** "Không tìm thấy hồ sơ." — **không** trả 403, vì 403 xác nhận bản ghi có tồn tại.
- Khác với sai vai trò: phụ huynh gọi API chỉ dành cho gia sư bị 403 ngay ở `[Authorize]`, với
  mọi id, nên 403 không lộ gì (BR-SCOPE-05).

---

## 5. Message lỗi

| Quy tắc | Đúng | Sai |
| :-- | :-- | :-- |
| Tiếng Việt có dấu, người dùng hiểu được | `Không tìm thấy hồ sơ.` | `Profile not found` |
| Không lộ bảng, cột, class, exception | `Dữ liệu gửi lên không hợp lệ.` | `FK violation on tutor_profiles.tutor_id` |
| Nói được phải làm gì | `Bạn đã có 5 hồ sơ, không tạo thêm được.` | `Limit exceeded` |

Message lỗi 404 của một tài nguyên dùng **một câu duy nhất** cho cả "không tồn tại" và "không
phải của bạn".

---

## 6. Validation

- FluentValidation, validator ở `GiaSu.Application/Validators/<Module>/`, gọi **tường minh** trong
  Controller như `AuthController`.
- Validator chỉ kiểm *hình dạng* dữ liệu (bắt buộc, độ dài, định dạng, miền giá trị). Kiểm *trạng
  thái nghiệp vụ* (đã đủ 5 hồ sơ chưa, hồ sơ đang ở trạng thái nào) thuộc Service.
- Giới hạn và câu thông báo phải **trùng** với frontend (`frontend/ui-screens.md` mục SCR); sửa
  một bên thì báo người làm bên kia.
- Tệp tải lên: kiểm số lượng, dung lượng, định dạng (xem cả magic bytes, không tin
  `Content-Type`) ở API **trước khi** gửi lên Storage.

---

## 7. Phân quyền

```csharp
[Authorize(Roles = Roles.Tutor)]                         // một vai trò
[Authorize(Roles = $"{Roles.Tutor},{Roles.Parent}")]      // nhiều vai trò
[Authorize(Roles = Roles.All)]                            // mọi vai trò
```

- Mọi action có `[Authorize(Roles = ...)]` bằng hằng số `GiaSu.Domain.Constants.Roles`. Không dùng
  `[Authorize]` trống.
- `userId` lấy từ claim `sub`:
  `Guid.Parse(User.FindFirst(JwtRegisteredClaimNames.Sub)!.Value)` (`ActiveUserMiddleware` đã bảo
  đảm claim hợp lệ).
- **Phân quyền theo dữ liệu:** `[Authorize(Roles = Roles.Parent)]` chỉ chặn "có phải phụ huynh
  không", không chặn "có phải tin **của mình** không". Mọi endpoint đụng một bản ghi cụ thể phải
  lọc theo `userId` trong truy vấn, ngoài phạm vi → 404 (§4.2). Ma trận: `business/user-roles.md`.
- **Tách route theo vai trò** khi mỗi vai trò nhận tập bản ghi hoặc DTO khác nhau
  (`api/tutor-profiles/mine` cho gia sư, `api/tutor-profiles?status=` cho Admin).

---

## 8. Dịch vụ dùng chung

| Dịch vụ | Dùng khi | Thẻ |
| :-- | :-- | :-- |
| `IFileStorageService` | Lưu, xóa tệp minh chứng; cấp URL ký 60 phút (D16) | S02-01 |
| `INotificationService` | Mọi sự kiện ở `business/business-rules.md` §4; module tự soạn tiêu đề, nội dung, `link`; service chọn kênh (D13) | S02-02 |
| `IAuditLogService` | Mọi chuyển trạng thái ở BR-22; lỗi khi ghi log thì ghi Serilog và **không** chặn nghiệp vụ | S03-02 |

Module gọi dịch vụ sau khi transaction nghiệp vụ đã commit.

---

## 9. Checklist trước khi mở PR

- [ ] Route đúng §3; mọi action có `[Authorize(Roles = ...)]` bằng hằng số.
- [ ] Endpoint đụng bản ghi cụ thể đã lọc phạm vi theo `sub`, ngoài phạm vi trả 404.
- [ ] Giá trị server tự đặt không nhận từ client (CC-04 trong `functional-requirements.md`).
- [ ] Response đúng `ApiResponse<T>`, status code đúng §4.
- [ ] Message tiếng Việt, không lộ cấu trúc nội bộ.
- [ ] Không gọi `DbContext` ngoài Repository; DI đủ Repository, Service, Validator.
- [ ] Unit test cho mỗi `BR-xx` của thẻ; mỗi AC của thẻ có ít nhất một ca kiểm.
- [ ] Postman: ca đúng, ca 400, ca sai vai trò; đụng bản ghi cụ thể thì thêm ca 404 ngoài phạm vi.
- [ ] `dotnet build -warnaserror` và `dotnet test` sạch.
- [ ] Cập nhật `api/da-trien-khai.md` trong PR.
