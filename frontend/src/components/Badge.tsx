"use client";

import React from "react";

export type BadgeTone = "positive" | "warning" | "danger" | "neutral" | "info";
export type BadgeSize = "sm" | "md";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
  size?: BadgeSize;
  showDot?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

const TONE_CONFIG: Record<
  BadgeTone,
  { containerClass: string; dotClass: string; defaultDot: boolean }
> = {
  positive: {
    containerClass: "bg-primary-fixed/50 text-primary border border-primary/20",
    dotClass: "bg-primary",
    defaultDot: true,
  },
  warning: {
    containerClass: "bg-amber-100 text-amber-800 border border-amber-200",
    dotClass: "bg-amber-600",
    defaultDot: true,
  },
  danger: {
    containerClass: "bg-error-container text-on-error-container border border-error/20",
    dotClass: "bg-error",
    defaultDot: true,
  },
  neutral: {
    containerClass: "bg-slate-100 text-on-surface-variant border border-slate-200",
    dotClass: "bg-outline",
    defaultDot: true,
  },
  info: {
    containerClass: "bg-surface-container-low text-secondary border border-secondary/15",
    dotClass: "",
    defaultDot: false,
  },
};

const SIZE_CLASSES: Record<BadgeSize, string> = {
  sm: "px-2 py-0.5 text-[11px] gap-1",
  md: "px-2.5 py-1 text-xs gap-1.5",
};

export function Badge({
  tone = "neutral",
  size = "md",
  showDot,
  icon,
  className = "",
  children,
  ...props
}: BadgeProps) {
  const config = TONE_CONFIG[tone];
  const shouldShowDot = showDot !== undefined ? showDot : config.defaultDot && !icon;

  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full font-semibold transition-colors ${
        config.containerClass
      } ${SIZE_CLASSES[size]} ${className}`}
      {...props}
    >
      {shouldShowDot && (
        <span
          className={`h-1.5 w-1.5 rounded-full shrink-0 ${config.dotClass}`}
          aria-hidden="true"
        />
      )}
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
}
