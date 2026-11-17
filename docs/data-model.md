# Mô hình dữ liệu khởi điểm

Bản phác để SV3 dựng ERD ở Sprint 01 (migration từng bảng do người làm module tạo, D11); ERD chốt xong thì cập nhật lại file này và
sheet **P3D_04_CoSoDuLieu**. Tên bảng snake_case số nhiều, khóa chính `id uuid` (riêng `roles`,
`subjects` dùng `smallint`), thời gian `timestamptz` tên kết thúc `_at` (lưu UTC).
Khóa ngoại mặc định `ON DELETE RESTRICT`; không xóa cứng dữ liệu nghiệp vụ.

Trạng thái và quy tắc: `business-rules.md`. Tên lớp: `DECISIONS.md` D18.

## Đã có (migration `InitialAuth`)

| Bảng | Cột chính |
| :-- | :-- |
| `roles` | `id`, `name` — seed 3 vai trò (D05) |
| `users` | `id`, `role_id`, `full_name`, `login_identifier` (email, unique), `credential_reference` (hash), `is_active`, `token_version`, `created_at` |

## Cần thêm

| Bảng | Cột chính | Quan hệ | Module |
| :-- | :-- | :-- | :-- |
| `tutors` | `user_id` (PK = FK users), `phone`, `university`, `student_code`, `verification_status`, `reputation_score` | 1–1 `users` | AUTH |
| `parents` | `user_id` (PK = FK users), `phone`, `reputation_score` | 1–1 `users` | AUTH |
| `students` | `id`, `parent_id`, `full_name`, `grade_level` | N–1 `parents` | REQUEST |
| `subjects` | `id`, `name`, `education_level` | danh mục, seed | PROFILE |
| `student_verifications` | `id`, `tutor_id`, `evidence_file_ref`, `status`, `reject_reason`, `reviewed_by`, `reviewed_at`, `created_at` | N–1 `tutors` | VERIFY |
| `tutor_profiles` | `id`, `tutor_id`, `title`, `description`, `experience`, `education_level`, `province`, `district`, `expected_fee_per_session`, `status`, `availability`, `is_default`, `reject_reason`, `created_at`, `updated_at` | N–1 `tutors` | PROFILE |
| `tutor_profile_subjects` | `profile_id`, `subject_id` (PK ghép) | N–N | PROFILE |
| `tutor_profile_evidences` | `id`, `profile_id`, `file_ref`, `file_name`, `content_type`, `size_bytes` | N–1 `tutor_profiles` | PROFILE |
| `tutor_requests` | `id`, `parent_id`, `student_id`, `subject_id`, `education_level`, `province`, `district`, `address`, `sessions_per_week`, `min_fee`, `max_fee`, `requirements`, `status`, `reject_reason`, `expires_at`, `created_at` | N–1 `parents`, `students`, `subjects` | REQUEST |
| `saved_tutor_requests` | `tutor_id`, `request_id` (PK ghép), `saved_at` | N–N | SEARCH |
| `tutor_applications` | `id`, `request_id`, `tutor_id`, `profile_id`, `introduction`, `status`, `trial_scheduled_at`, `trial_note`, `created_at`, `updated_at` | N–1 `tutor_requests`, `tutors`, `tutor_profiles` | APPLY |
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
| `notifications` | `id`, `recipient_id`, `type`, `title`, `message`, `link`, `is_read`, `created_at` | N–1 `users` | NOTI |
| `notification_preferences` | `user_id`, `type` (PK ghép), `email_enabled` | N–1 `users` | NOTI |
| `audit_logs` | `id`, `actor_id`, `entity`, `entity_id`, `action`, `from_status`, `to_status`, `created_at` | — | dùng chung (BR-22) |

Ràng buộc nên đặt ở database (CHECK), không chỉ ở validator: các cột `status`, `stars` 1–5,
`score` 0–10, `understanding_level` 1–5, `min_fee <= max_fee`, `amount >= 0`.
