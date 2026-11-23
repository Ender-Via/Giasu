# Quy ước backend và API

## 0. Khuôn module

Backend là FastAPI modular monolith. Module Auth hiện tại là mẫu:

```text
app/api/auth.py              Router: HTTP, dependency, status code
app/services/auth.py         Quy tắc nghiệp vụ
app/repositories/auth.py     Truy vấn SQLAlchemy, lọc phạm vi
app/schemas/auth.py          DTO Pydantic
app/db/models.py             Model persistence
```

Viết chú thích và message lỗi bằng tiếng Việt; tên module, biến, hàm, class bằng tiếng Anh.

## 1. Nguyên tắc nền

1. Tài nguyên REST là danh từ; route luôn có tiền tố `/api`.
2. Mọi response, kể cả lỗi, theo `ApiResponse<T>` (D04).
3. Mọi endpoint nghiệp vụ có dependency xác thực/phân quyền. Chỉ luồng Supabase Auth công khai
   không đi qua backend; đăng ký S01-04 sẽ quy định riêng.
4. Schema Pydantic tách khỏi model SQLAlchemy; không trả model ra ngoài.
5. Router không chứa logic nghiệp vụ; service không viết SQL; chỉ repository dùng `Session`.
6. Không tin vai trò từ token/client. Vai trò và trạng thái khóa lấy từ bảng `users`.

## 2. Thêm module

Ví dụ `TutorProfile`:

| # | Nơi | Việc |
| :-- | :-- | :-- |
| 1 | `app/db/models.py` | Model, FK `RESTRICT`, index; CHECK nằm trong Alembic migration |
| 2 | `app/schemas/tutor_profiles.py` | Request/response Pydantic; JSON camelCase |
| 3 | `app/repositories/tutor_profiles.py` | Câu truy vấn và lọc `tutor_id = current_user.id` |
| 4 | `app/services/tutor_profiles.py` | BR, trạng thái, transaction, kết quả có kiểu |
| 5 | `app/api/tutor_profiles.py` | Router, dependency, ánh xạ kết quả sang status code |
| 6 | `app/main.py` | `include_router()` |
| 7 | `tests/` | Ca đúng, biên, sai quyền/phạm vi |

Có đổi schema thì tạo Alembic revision theo D11. Trước khi autogenerate phải kiểm tra nội dung
revision; không coi file sinh tự động là đã được review.

### 2.1 Nơi đặt logic

| Lớp | Làm gì | Không làm gì |
| :-- | :-- | :-- |
| Router | Parse request, dependency auth, gọi service, status code | SQL, `if` nghiệp vụ phức tạp |
| Service | BR, kiểm trạng thái, transaction và kết quả nghiệp vụ | Lộ HTTPException cho repository |
| Repository | Truy vấn, lọc phạm vi trong `WHERE`, cập nhật có điều kiện | Quyết định nghiệp vụ |

Chuyển trạng thái phải là cập nhật có điều kiện, ví dụ SQLAlchemy:

```python
statement = (
    update(TutorProfile)
    .where(
        TutorProfile.id == profile_id,
        TutorProfile.tutor_id == user_id,
        TutorProfile.status.in_(["Draft", "Rejected"]),
    )
    .values(status="PendingReview")
)
affected = session.execute(statement).rowcount
```

`affected == 0` thì đọc lại có lọc phạm vi để phân biệt 404 với 409.

## 3. Route và JSON

| Hạng mục | Quy tắc | Ví dụ đúng |
| :-- | :-- | :-- |
| Tiền tố | luôn `/api/` | `/api/tutor-profiles` |
| Tài nguyên | danh từ số nhiều, chữ thường, gạch nối | `/api/student-verifications` |
| Định danh | tham số route | `/api/tutor-profiles/{id}` |
| Tài nguyên con | lồng tối đa một cấp | `/api/tutor-profiles/{id}/evidences` |
| Của mình | đoạn `mine` | `/api/tutor-profiles/mine` |
| Hành động | `POST`, động từ cuối route | `/api/tutor-profiles/{id}/submit` |
| Lọc/phân trang | query string | `?status=Pending&page=1` |

Phân trang: `page` từ 1, mặc định 1; `pageSize` 1–100, mặc định 20. JSON camelCase; enum
PascalCase tiếng Anh; thời gian UTC kết thúc `Utc`; ngày `yyyy-MM-dd`; tiền là số nguyên đồng.

Không xóa cứng dữ liệu nghiệp vụ. Hai ngoại lệ MVP: minh chứng hồ sơ chưa duyệt và tin đã lưu.

## 4. Status code

| Code | Khi nào |
| :-- | :-- |
| 200 | Đọc, sửa, đổi trạng thái thành công |
| 201 | Tạo mới |
| 400 | Dữ liệu tự nó sai |
| 401 | Thiếu/sai/hết hạn token hoặc tài khoản nghiệp vụ bị khóa |
| 403 | Sai vai trò hoặc bị khóa tính năng |
| 404 | Không tồn tại, ngoài phạm vi, hoặc Supabase user chưa có hồ sơ nghiệp vụ |
| 409 | Xung đột với trạng thái/dữ liệu hiện tại |
| 429 | Vượt giới hạn Auth Supabase |
| 500 | Lỗi chưa xử lý; không lộ exception |

404 dùng cùng một message cho “không tồn tại” và “không thuộc người gọi” để không lộ bản ghi.

## 5. Validation và lỗi

- Request schema dùng Pydantic để kiểm hình dạng, độ dài, miền giá trị.
- Trạng thái và giới hạn số lượng thuộc service, không đặt trong schema.
- Message tiếng Việt có dấu, hướng dẫn được người dùng, không lộ bảng/cột/class/stack trace.
- Tệp: kiểm số lượng, dung lượng, đuôi và magic bytes trước khi gửi Storage.
- Handler chung chuyển lỗi FastAPI/Pydantic sang `ApiResponse<T>`; không trả Problem Details.

## 6. Xác thực và phân quyền

`get_current_auth_user` chỉ xác minh Supabase JWT bằng JWKS, yêu cầu `sub`, `exp`, `iss`, `aud`.
Mọi route cần đăng nhập phải dùng dependency chung `get_current_user`; dependency này ánh xạ
`sub` (`auth.users.id`) qua `users.auth_user_id`, từ chối tài khoản khóa và trả:

- `users.id`: định danh nghiệp vụ dùng cho FK/phạm vi;
- `users.role_id`: vai trò được phép;
- `users.is_active`: trạng thái khóa.

Không dùng riêng `get_current_auth_user` ở route nghiệp vụ vì như vậy sẽ bỏ qua trạng thái khóa.
Không dùng claim `role` của Supabase làm vai trò nghiệp vụ. Không nhận `userId` chủ sở hữu từ
client. Dependency phân quyền theo vai trò sẽ được bổ sung cùng module đầu tiên cần nó; cho tới khi
đó `/api/auth/me` là endpoint đã kiểm chứng duy nhất.

## 7. Response

```json
{
  "success": true,
  "data": { "userId": "...", "fullName": "...", "role": "Tutor" },
  "message": null,
  "errors": null
}
```

Lỗi một câu đặt ở `message`; lỗi nhiều trường đặt ở `errors`. Frontend luôn dùng `toApiError()`.

## 8. Dịch vụ dùng chung

| Dịch vụ | Dùng khi | Thẻ |
| :-- | :-- | :-- |
| File storage | Bucket private, xóa tệp, signed URL 60 phút (D16) | S02-01 |
| Notification | Các sự kiện trong `business-rules.md` §4 | S02-02 |
| Audit log | Chuyển trạng thái BR-22; lỗi ghi log không chặn nghiệp vụ | S03-02 |

## 9. Checklist PR backend

- [ ] Router có dependency auth/role phù hợp; phạm vi lấy từ tài khoản nghiệp vụ đã ánh xạ.
- [ ] Không nhận giá trị server tự đặt từ client (CC-04).
- [ ] Response đúng `ApiResponse<T>` và status code đúng §4.
- [ ] Không trả model SQLAlchemy; không gọi `Session` ngoài repository/service transaction boundary.
- [ ] Migration bảo toàn dữ liệu, có upgrade test trên PostgreSQL local/test; không chạy DB chung.
- [ ] pytest có ca đúng, 400, 401/403, 404 ngoài phạm vi và 409 tương ứng AC.
- [ ] `uv run ruff check .` và `uv run pytest` sạch.
- [ ] Chỉ ghi vào `api/da-trien-khai.md` phần đã chạy/kiểm chứng.
