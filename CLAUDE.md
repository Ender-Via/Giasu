# CLAUDE.md

Hướng dẫn cho Claude Code (và trợ lý AI khác) khi làm việc trong repo này.

## Tổng quan
Nền tảng tìm việc gia sư, 3 vai trò `Admin`, `Tutor`, `Parent`. Backend ASP.NET Core 10 dựng
4 lớp (`backend/GiaSu.*`), frontend Next.js 16 (`frontend/`). Database PostgreSQL trên Supabase,
**cả nhóm dùng chung một database**. Code, chú thích, message lỗi, commit viết tiếng Việt.

## Đọc trước khi sửa code
Không đọc hết `docs/`. Bảng "Làm việc gì thì đọc file nào" ở `docs/README.md` chỉ đúng file cho
từng việc. Tối thiểu:
- Thẻ backend: FR + AC của thẻ, `docs/api/api-conventions.md`, `docs/business/user-roles.md` §3.
- Thẻ frontend: mục SCR trong `docs/frontend/ui-screens.md`, `docs/frontend/frontend-conventions.md`.
- Gặp mã `Dxx`: `docs/DECISIONS.md`.

Tài liệu mô tả **thiết kế đích**; thứ đã có trên `develop` ghi ở `docs/api/da-trien-khai.md`.
FR hay SCR còn ghi "chưa viết" thì không code. Tài liệu mâu thuẫn: theo thứ tự ưu tiên ở
`docs/README.md` và báo người dùng, không tự chọn.

## Lệnh
```bash
dotnet build backend/GiaSu.slnx -warnaserror   # DoD: 0 warning
dotnet test backend/GiaSu.slnx
cd frontend && npm run lint && npm run build
```

## Không được làm
- Không `dotnet ef database update`, `database drop`, hay chạy SQL ghi dữ liệu lên DB dùng chung
  khi người dùng chưa đồng ý rõ ràng (D11).
- Không thêm package mới, không sửa `docs/` khi người dùng chưa yêu cầu.
- Không commit secret; không `git push --force`, `git reset --hard` trên nhánh đã push.
- Không tự thêm trạng thái ngoài danh sách ở `docs/business/business-rules.md` §2 (D32).
- Commit message không thêm dòng attribution của AI.
