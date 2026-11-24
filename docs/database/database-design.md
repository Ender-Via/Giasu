# Thiết kế database

Bản phác để SV3 dựng ERD ở Sprint 01 (migration Alembic từng bảng do người làm module tạo, D11); ERD chốt xong thì cập nhật lại file này và
sheet **P3D_04_CoSoDuLieu**. Tên bảng snake_case số nhiều, khóa chính `id uuid` (riêng `roles`,
`subjects` dùng `smallint`), thời gian `timestamptz` tên kết thúc `_at` (lưu UTC).
Khóa ngoại mặc định `ON DELETE RESTRICT`; không xóa cứng dữ liệu nghiệp vụ.

Trạng thái và quy tắc: `business/business-rules.md`. Tên lớp: `DECISIONS.md` D18. Khu vực: D37.

## Đã có (baseline `0001_initial_auth` + migration `0002_supabase_auth_mapping`)

| Bảng | Cột chính |
| :-- | :-- |
| `roles` | `id`, `name` — seed 3 vai trò (D05) |
| `auth.users` | Do Supabase Auth quản lý; `id uuid` là định danh xác thực, email/mật khẩu/refresh token không do backend nghiệp vụ ghi |
| `users` | `id` (định danh nghiệp vụ), `auth_user_id` (nullable trong bước chuyển tiếp, unique, FK `auth.users.id`), `role_id`, `full_name`, `login_identifier` (email cũ, unique), `credential_reference` (hash cũ, nullable), `is_active`, `token_version` (cột cũ), `created_at` |

`0001_initial_auth` tái hiện đúng schema EF `InitialAuth` để Alembic có baseline. `0002` chỉ thêm
ánh xạ Supabase và nới nullable cho hash cũ, không đổi/xóa `id`, `credential_reference`,
`token_version` hay dữ liệu hiện có. Sau khi S01-04 hoàn tất chuyển tài khoản và mọi row có
`auth_user_id`, một migration riêng mới được phép đặt cột này `NOT NULL`; PR nền hiện tại chưa làm.

Quan hệ xác thực là `auth.users (1) — (0..1) users`. Xóa user Supabase bị `RESTRICT`; khóa tài
khoản nghiệp vụ dùng `users.is_active`, vai trò dùng `users.role_id`.

Sheet **P3D_04_CoSoDuLieu** mô tả mô hình đích gọn hơn: `users.id` đồng thời là FK đến
`auth.users.id`, và `status` biểu diễn trạng thái tài khoản. Với dữ liệu `InitialAuth` đã tồn tại,
đổi trực tiếp PK sẽ làm mất liên kết nên migration chuyển tiếp cố ý giữ `users.id`, thêm
`auth_user_id`, và ánh xạ `status` sang `is_active`. Sau khi S01-04 hoàn tất backfill, nhóm phải
chốt một migration riêng nếu muốn hợp nhất hai UUID; không thực hiện việc đó trong PR nền này.

## Cần thêm

| Bảng | Cột chính | Quan hệ | Module |
| :-- | :-- | :-- | :-- |
| `tutors` | `user_id` (PK = FK users), `phone`, `verification_status`, `reputation_score` | 1–1 `users` | AUTH (S01-04) |
| `parents` | `user_id` (PK = FK users), `phone`, `reputation_score` | 1–1 `users` | AUTH (S01-04) |
| `students` | `id`, `parent_id`, `full_name`, `grade_level` (1–12, lớp đang học), `created_at` | N–1 `parents` | REQUEST |
| `subjects` | `id`, `name`, `education_level` | danh mục, seed | PROFILE |
| `student_verifications` | `id`, `tutor_id`, `university`, `student_code`, `evidence_file_ref`, `status`, `reject_reason`, `reviewed_by`, `reviewed_at`, `created_at` | N–1 `tutors` | VERIFY |
| `tutor_profiles` | `id`, `tutor_id`, `title`, `description`, `experience`, `education_level`, `teaching_mode`, `province`, `teaching_wards` (text[], 1–5), `expected_fee_per_session`, `status`, `availability`, `is_default`, `reject_reason`, `submitted_at`, `reviewed_by`, `reviewed_at`, `created_at`, `updated_at` | N–1 `tutors` | PROFILE |
| `tutor_profile_subjects` | `profile_id`, `subject_id` (PK ghép) | N–N | PROFILE |
| `tutor_profile_evidences` | `id`, `profile_id`, `file_ref`, `file_name`, `content_type`, `size_bytes` | N–1 `tutor_profiles` | PROFILE |
| `tutor_requests` | `id`, `parent_id`, `student_id`, `subject_id`, `education_level`, `teaching_mode`, `province`, `ward`, `address` (ba cột này `null` khi `Online`), `sessions_per_week`, `min_fee`, `max_fee`, `requirements`, `status`, `reject_reason`, `expires_at`, `submitted_at`, `reviewed_by`, `reviewed_at`, `created_at`, `updated_at` | N–1 `parents`, `students`, `subjects` | REQUEST |
| `saved_tutor_requests` | `tutor_id`, `request_id` (PK ghép), `saved_at` | N–N | SEARCH |
| `tutor_applications` | `id`, `request_id`, `tutor_id`, `profile_id`, `introduction`, `status`, `trial_scheduled_at`, `trial_note`, `created_at`, `updated_at` | N–1 `tutor_requests`, `tutors`, `tutor_profiles`; unique (`request_id`, `tutor_id`) WHERE `status` IN (`Pending`, `Viewed`, `TrialInvited`) | APPLY |
| `conversations` | `id`, `application_id` (unique), `created_at` | 1–1 `tutor_applications` | CHAT |
| `messages` | `id`, `conversation_id`, `sender_id`, `content`, `sent_at` | N–1 `conversations` | CHAT |
| `learning_roadmaps` | `id`, `application_id` (unique), `tutor_id`, `parent_id`, `student_id`, `subject_id`, `goal`, `schedule_note`, `fee_per_session`, `start_date`, `end_date`, `status`, `parent_feedback` | 1–1 `tutor_applications` | ROADMAP |
| `roadmap_plan_items` | `id`, `roadmap_id`, `week_number`, `planned_content`, `planned_sessions`, `is_done` | N–1 `learning_roadmaps` | ROADMAP |
| `class_sessions` | `id`, `roadmap_id`, `scheduled_start_at`, `scheduled_end_at`, `status`, `taught_content`, `homework`, `understanding_level`, `tutor_note`, `recorded_at`, `confirmed_at`, `dispute_reason` | N–1 `learning_roadmaps` | SESSION |
| `reschedule_requests` | `id`, `session_id`, `requested_by`, `proposed_start_at`, `proposed_end_at`, `reason`, `status`, `created_at` | N–1 `class_sessions`; unique (`session_id`, `requested_by`) | SESSION |
| `assessments` | `id`, `roadmap_id`, `title`, `test_date`, `score`, `target_score`, `note` | N–1 `learning_roadmaps` | PROGRESS |
| `progress_reports` | `id`, `roadmap_id`, `period_start`, `period_end`, `sessions_completed`, `plan_completion_percent`, `average_score`, `is_behind_schedule`, `tutor_comment`, `generated_at` | N–1 `learning_roadmaps` | PROGRESS |
| `tuition_invoices` | `id`, `roadmap_id`, `period_month`, `session_count`, `amount`, `due_date`, `status` | N–1 `learning_roadmaps`; unique (`roadmap_id`, `period_month`) | TUITION |
| `payments` | `id`, `invoice_id` (unique), `amount`, `method`, `transaction_code`, `recorded_by`, `paid_at`, `confirmed_by_tutor_at` | 1–1 `tuition_invoices` | TUITION |
| `reviews` | `id`, `roadmap_id`, `reviewer_id`, `reviewee_id`, `stars`, `comment`, `reply`, `replied_at`, `created_at` | unique (`roadmap_id`, `reviewer_id`) | REVIEW |
| `reputation_flags` | `id`, `tutor_id`, `reason`, `created_at`, `handled_at` | N–1 `tutors` | REVIEW |
| `violation_reports` | `id`, `reporter_id`, `reported_user_id`, `category`, `description`, `status`, `resolution`, `handled_by`, `created_at`, `resolved_at` | N–1 `users` | VIOLATION |
| `violation_evidences` | `id`, `report_id`, `file_ref`, `file_name` | N–1 `violation_reports` | VIOLATION |
| `account_sanctions` | `id`, `user_id`, `report_id`, `type` (`Warning`, `FeatureLock`, `PermanentBan`), `locked_until`, `reason`, `created_by`, `created_at` | N–1 `users` | VIOLATION |
| `notifications` | `id`, `recipient_id`, `type`, `title`, `message`, `link`, `is_read`, `created_at`; index (`recipient_id`, `is_read`, `created_at`) | N–1 `users` | NOTI |
| `notification_preferences` | `user_id`, `type` (PK ghép), `email_enabled` | N–1 `users` | NOTI |
| `audit_logs` | `id`, `actor_id`, `entity`, `entity_id`, `action`, `from_status`, `to_status`, `created_at` | — | dùng chung (BR-22) |

Ràng buộc nên đặt ở database (CHECK), không chỉ ở validator: các cột `status`, `stars` 1–5,
`score` 0–10, `understanding_level` 1–5, `min_fee <= max_fee`, `amount >= 0`, `province` thuộc danh mục D37,
`grade_level` 1–12, `sessions_per_week` 1–7.

`submitted_at` là lần gửi duyệt gần nhất (danh sách chờ duyệt của Admin sắp theo cột này);
`reviewed_by`, `reviewed_at` là lần duyệt/từ chối gần nhất (FR-04, FR-06).
