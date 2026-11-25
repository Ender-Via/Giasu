// Kiểu phản chiếu DTO thông báo (FR-32). Mọi vai trò dùng chung.

export type NotificationType =
  | "ModerationResult"
  | "NewApplication"
  | "ApplicationStatus"
  | "Roadmap"
  | "Session"
  | "RequestExpiry"
  | "Tuition"
  | "Progress"
  | "Violation"
  | "ModerationQueue";

// Nhãn loại thông báo ở SCR-COM-02; backend chỉ trả các loại thuộc vai trò đang đăng nhập
export const NOTIFICATION_TYPE_LABELS: Record<NotificationType, string> = {
  ModerationResult: "Kết quả duyệt hồ sơ, tin, xác thực",
  NewApplication: "Có ứng viên mới",
  ApplicationStatus: "Thay đổi trạng thái ứng tuyển",
  Roadmap: "Lộ trình học",
  Session: "Buổi học và nhắc lịch",
  RequestExpiry: "Tin sắp hết hạn",
  Tuition: "Học phí",
  Progress: "Tiến độ học tập",
  Violation: "Báo cáo vi phạm",
  ModerationQueue: "Có hồ sơ, tin, yêu cầu xác thực mới cần duyệt",
};

export interface NotificationResponse {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  // Đường dẫn nội bộ bắt đầu bằng "/", null khi thông báo không dẫn tới đâu
  link: string | null;
  isRead: boolean;
  createdAtUtc: string;
}

export interface NotificationPageResponse {
  items: NotificationResponse[];
  page: number;
  pageSize: number;
  totalCount: number;
}

export interface UnreadCountResponse {
  count: number;
}

export interface NotificationPreferenceItem {
  type: NotificationType;
  emailEnabled: boolean;
}

export interface NotificationPreferencesResponse {
  items: NotificationPreferenceItem[];
}

// Body của PUT /api/notification-preferences: gửi toàn bộ danh sách
export interface UpdateNotificationPreferencesRequest {
  items: NotificationPreferenceItem[];
}
