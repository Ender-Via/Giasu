"use client";

import React from "react";
import DashboardLayout, { NavItem } from "@/components/DashboardLayout";
import RoleGuard from "@/components/RoleGuard";

// Thêm màn hình mới: thêm một mục vào menu này và một thư mục route cùng tên.
const ADMIN_MENU_ITEMS: NavItem[] = [
  { label: "Tổng quan", href: "/admin/dashboard", icon: "Activity" },
  { label: "Duyệt hồ sơ gia sư", href: "/admin/tutor-profiles", icon: "FileText" },
  { label: "Xác thực sinh viên", href: "/admin/student-verifications", icon: "Check" },
  { label: "Duyệt tin tìm gia sư", href: "/admin/jobs", icon: "Clipboard" },
  { label: "Báo cáo vi phạm", href: "/admin/violations", icon: "Alert" },
  { label: "Thông báo", href: "/admin/notifications", icon: "Info" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleGuard allowedRole="Admin">
      <DashboardLayout portalName="Cổng Quản Trị" groupTitle="Quản trị viên" menuItems={ADMIN_MENU_ITEMS}>
        {children}
      </DashboardLayout>
    </RoleGuard>
  );
}
