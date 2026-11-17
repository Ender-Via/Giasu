"use client";

import React from "react";
import DashboardLayout, { NavItem } from "@/components/DashboardLayout";
import RoleGuard from "@/components/RoleGuard";

// Thêm màn hình mới: thêm một mục vào menu này và một thư mục route cùng tên.
const PARENT_MENU_ITEMS: NavItem[] = [
  { label: "Tin tìm gia sư", href: "/parent/jobs", icon: "Clipboard" },
  { label: "Lộ trình và buổi học", href: "/parent/roadmaps", icon: "Clock" },
  { label: "Học phí", href: "/parent/payments", icon: "FileText" },
  { label: "Tin nhắn", href: "/parent/chat", icon: "Heart" },
  { label: "Thông báo", href: "/parent/notifications", icon: "Info" },
];

export default function ParentLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleGuard allowedRole="Parent">
      <DashboardLayout portalName="Cổng Phụ Huynh" groupTitle="Phụ huynh" menuItems={PARENT_MENU_ITEMS}>
        {children}
      </DashboardLayout>
    </RoleGuard>
  );
}
