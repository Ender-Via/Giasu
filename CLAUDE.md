# CLAUDE.md

Hướng dẫn cho Claude Code (và trợ lý AI khác) khi làm việc trong repo này.

## Tổng quan
Nền tảng tìm việc gia sư, 3 vai trò `Admin`, `Tutor`, `Parent`. Backend ASP.NET Core 10 dựng
4 lớp (`backend/GiaSu.*`), frontend Next.js 16 (`frontend/`). Database PostgreSQL trên Supabase,
**cả nhóm dùng chung một database**. Code, chú thích, message lỗi, commit viết tiếng Việt.

## Đọc trước khi sửa code
1. `docs/conventions.md` — khuôn module, status code, quy ước frontend.
2. `docs/business-rules.md` — trạng thái hợp lệ và quy tắc `BR-xx` của module đang làm.
3. `docs/DECISIONS.md` — khi gặp mã `Dxx` trong code.
Module mẫu đã chạy: Auth (`AuthController` → `AuthService` → `AuthRepository`).

## Lệnh
```bash
dotnet build backend/GiaSu.slnx -warnaserror   # DoD: 0 warning
dotnet test backend/GiaSu.slnx
cd frontend && npm run lint && npm run build
```

## Không được làm
- Không `dotnet ef database update`, `database drop`, hay chạy SQL ghi dữ liệu lên DB dùng chung
  khi người dùng chưa đồng ý rõ ràng (D11).
- Không thêm package mới, không đổi `DECISIONS.md` / `business-rules.md` khi chưa hỏi.
- Không commit secret; không `git push --force`, `git reset --hard` trên nhánh đã push.
- Không tự thêm trạng thái ngoài danh sách ở `business-rules.md` §2 (D32).
- Commit message không thêm dòng attribution của AI.
