# Quy trình làm việc

Một vòng làm việc cho **một thẻ** trong file kế hoạch (`KeHoach_GiaSu.xlsx`, đưa lên Google
Sheets): nhận thẻ → code → PR → review → merge → đánh dấu Xong. Làm xong thì lặp lại.

| Vai | Người |
| :-- | :-- |
| **Lead** (nhóm trưởng) — điều phối nhóm, theo dõi Sheet, đôn đốc tiến độ, quản trị Supabase | SV1 Lộc |
| **GitHub owner** — repo, nhánh, merge `main`, `CODEOWNERS`, `docs/`, biểu mẫu OOAD | SV2 Trí Kiệt |
| Thiết kế database — ERD, duyệt migration | SV3 Lân |

## 0. Năm luật không thương lượng

1. **Backend trước, frontend sau.** Thẻ FE của một chức năng nằm ở sprint *sau* thẻ BE của nó.
   BE chưa merge thì FE làm giao diện với dữ liệu giả, nối API sau — không chờ ngồi không.
2. **Hạn của thẻ là 23:59 ngày cuối sprint.** Trễ phải báo trong group **trước** hạn ít nhất
   1 ngày (P1_02), kèm lý do và ngày xong mới.
3. **Không ai commit thẳng lên `develop` hay `main`.** Mọi code đi qua PR, có người duyệt, CI xanh.
4. **Mỗi người tối đa 2 thẻ "Đang làm".**
5. **Thấy tài liệu sai, thiếu hoặc mâu thuẫn với code → báo GitHub owner.** Không tự quyết.

## 1. Sprint 3 ngày

| Sprint | Ngày | Trọng tâm |
| :-- | :-- | :-- |
| S01 | 17–19/11 | Dựng repo, DB, ERD, đăng ký; dọn biểu mẫu |
| S02 | 20–22/11 | Hồ sơ gia sư, xác thực SV, thông báo dùng chung |
| S03 | 23–25/11 | Tin tìm gia sư, Admin duyệt |
| S04 | 26–28/11 | Tìm kiếm + matching, ứng tuyển |
| S05 | 29/11–01/12 | Tuyển chọn + dạy thử, chat, gửi vi phạm |
| S06 | 02–04/12 | Lộ trình, Admin xử lý vi phạm |
| S07 | 05–07/12 | Buổi học + đổi lịch, bài kiểm tra |
| S08 | 08–10/12 | Học phí, báo cáo tiến độ, tác vụ định kỳ |
| S09 | 11–13/12 | Đánh giá + điểm uy tín |
| S10 | 14–16/12 | Thống kê quản trị; **hết backend tính năng** |
| S11 | 17–19/12 | Hết frontend tính năng; dữ liệu demo |
| S12 | 20–22/12 | **Đóng băng tính năng** — chỉ sửa lỗi |
| S13 | 23–25/12 | Kiểm thử toàn bộ, ma trận truy vết |
| S14 | 26–28/12 | Hoàn thiện biểu mẫu OOAD, UML, tập demo |
| Nộp | 29–30/12 | Nộp bài 30/12 |

**Nhịp mỗi sprint**
- **Ngày 1 (sáng):** mỗi người nhắn trong group 1 dòng: thẻ nhận, dự kiến xong ngày nào.
- **Ngày 2 (tối):** mỗi người cập nhật cột Trạng thái trên Sheet. Thẻ có nguy cơ trễ → báo ngay.
- **Ngày 3, 23:59:** hạn mở PR. Thẻ chưa xong → cột Trạng thái ghi `Trễ`, ghi lý do ở Ghi chú,
  tự chuyển sang sprint sau (không xóa dòng cũ, thêm dòng mới).
- **Sau hạn:** GitHub owner merge `develop` → `main` nếu CI xanh; Lead ghi chú buổi chốt sprint ở tab Sprint.

Lead kiểm Sheet mỗi tối. Thẻ quá hạn tô đỏ tự động; quá hạn 2 sprint liên tiếp → họp nhóm điều
chỉnh phân công và ghi nhận vào đánh giá đồng cấp (P1_02).

## 2. Nhánh

`main` = bản để chấm (chỉ GitHub owner merge từ `develop`). `develop` = nhánh tích hợp, nhánh mặc định.
Mỗi người có sẵn nhánh dài hạn, dùng suốt module, **mỗi nhánh chỉ một người**:

| Người | Nhánh | Module |
| :-- | :-- | :-- |
| SV1 Lộc | `feature/be-platform` | AUTH, NOTI, CHAT, PROGRESS, tác vụ định kỳ |
| SV1 Lộc | `feature/be-admin` | VERIFY, ADMIN-REVIEW, VIOLATION, REVIEW, DASH |
| SV3 Lân | `feature/be-recruitment` | PROFILE, REQUEST, SEARCH, APPLY |
| SV3 Lân | `feature/be-learning` | ROADMAP, SESSION, TUITION |
| SV2 Trí Kiệt | `feature/fe-shared` | design system, đăng nhập/đăng ký, thông báo, chat |
| SV2 Trí Kiệt | `feature/fe-tutor` | mọi màn hình của Gia sư |
| SV4 Anh Kiệt | `feature/fe-parent` | mọi màn hình của Phụ huynh |
| SV4 Anh Kiệt | `feature/fe-admin` | mọi màn hình của Admin |
| SV4 Anh Kiệt | `feature/tests` | xUnit, Postman |

Hai nhánh/người để khi một PR đang chờ review vẫn làm được thẻ khác ở nhánh còn lại (commit
thêm vào nhánh đang có PR mở sẽ lẫn vào PR đó).

## 3. Lệnh mỗi lần bắt đầu làm

```bash
git status                       # phải sạch
git checkout develop
git pull
git checkout feature/be-recruitment
git pull
git merge develop                # xung đột ở Program.cs: giữ CẢ HAI phía
dotnet build backend/GiaSu.slnx  # hoặc: cd frontend && npm run build
```

## 4. Commit

`<loại>(<module>): <mô tả tiếng Việt>` — loại: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.
Ví dụ: `feat(apply): thêm API ứng tuyển, chặn quá 5 phiếu đang chờ`.
Commit nhỏ, mỗi commit một việc trọn vẹn. `git add` từng file/thư mục, không `git add .` mù.
Push ít nhất một lần cuối mỗi buổi làm.

**Cấm trên repo chung:** `git push --force`, `git reset --hard` trên nhánh đã push, `git add -f`,
commit secret (connection string, `Jwt:Key`, service key), `dotnet ef database drop`.

## 5. Definition of Done

**Thẻ backend**
- [ ] DTO là `record`, không trả Entity ra ngoài
- [ ] Validator FluentValidation, message tiếng Việt
- [ ] Logic nghiệp vụ ở Service, chỉ Repository gọi `AppDbContext`
- [ ] `[Authorize(Roles = ...)]` bằng hằng số; ngoài phạm vi trả 404 (D07)
- [ ] Đăng ký DI đủ; status code đúng `conventions.md` §2
- [ ] Unit test cho mỗi quy tắc `BR-xx` của thẻ (`backend/GiaSu.Tests`)
- [ ] Postman: ca đúng + ca 400 + ca sai vai trò
- [ ] Migration (nếu có) đã được người backend còn lại duyệt (D11)
- [ ] `dotnet build -warnaserror` và `dotnet test` sạch

**Thẻ frontend**
- [ ] Gọi API qua `apiClient`, lỗi qua `toApiError()`
- [ ] React Hook Form cho form, TanStack Query cho đọc/ghi
- [ ] Đủ 3 trạng thái: đang tải / lỗi / rỗng
- [ ] Dùng được ở 375 px và 1280 px
- [ ] Tự bấm thử theo từng ý trong User Story/BR của thẻ, ghi kết quả vào PR
- [ ] `npm run lint` và `npm run build` sạch

**Thẻ tài liệu (Docs)**: nội dung khớp `DECISIONS.md` và `business-rules.md`, dùng đúng mã
FR/UC/BR/D, GitHub owner đã đọc.

## 6. Pull Request

1. Đủ DoD, đã `git merge develop` và build lại sạch, đã push.
2. Mở PR **vào `develop`** (không bao giờ vào `main`). Tiêu đề = tiêu đề thẻ. Điền mẫu PR có sẵn.
3. Người duyệt do `CODEOWNERS` gán: backend SV1 ↔ SV3, frontend SV2 ↔ SV4. Không tự duyệt.
4. Ghi số PR vào cột **PR** của thẻ trên Sheet, chuyển Trạng thái sang `Chờ review`.
5. Người duyệt phản hồi trong **24 giờ**. Sửa theo góp ý trên chính nhánh đó, push lại.
6. Duyệt xong → người duyệt merge (merge commit, không squash, **không xóa nhánh**).
   Tác giả chuyển thẻ sang `Xong`.

## 7. Khi bị kẹt

| Tình huống | Làm gì |
| :-- | :-- |
| Thẻ chờ thẻ khác chưa xong | Làm thẻ khác của mình; FE thì làm với dữ liệu giả |
| Kẹt một lỗi quá 30 phút | Hỏi trong group, kèm lỗi và những gì đã thử |
| Bị chặn quá 1 ngày | Trạng thái `Bị chặn`, ghi chặn bởi thẻ nào, báo Lead |
| Không chắc lệnh git làm gì | Hỏi trước khi Enter |
