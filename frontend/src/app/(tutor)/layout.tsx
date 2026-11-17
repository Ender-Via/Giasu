"use client";

import React from "react";
import DashboardLayout, { NavItem } from "@/components/DashboardLayout";
import RoleGuard from "@/components/RoleGuard";

// Thêm màn hình mới: thêm một mục vào menu này và một thư mục route cùng tên.
const TUTOR_MENU_ITEMS: NavItem[] = [
  { label: "Hồ sơ gia sư", href: "/tutor/profiles", icon: "User" },
  { label: "Tìm tin tuyển", href: "/tutor/jobs", icon: "Search" },
  { label: "Ứng tuyển của tôi", href: "/tutor/applications", icon: "Clipboard" },
  { label: "Lộ trình và buổi học", href: "/tutor/roadmaps", icon: "Clock" },
  { label: "Học phí", href: "/tutor/tuition", icon: "FileText" },
  { label: "Tin nhắn", href: "/tutor/chat", icon: "Heart" },
  { label: "Thông báo", href: "/tutor/notifications", icon: "Info" },
];

export default function TutorLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleGuard allowedRole="Tutor">
      <DashboardLayout portalName="Cổng Gia Sư" groupTitle="Sinh viên/Gia sư" menuItems={TUTOR_MENU_ITEMS}>
        {children}
      </DashboardLayout>
    </RoleGuard>
  );
}
