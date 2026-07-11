import { ReactNode } from "react";

export interface BadgeProps {
  children: ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info";
  className?: string;
}

const variantStyles: Record<string, string> = {
  default: "bg-support-surface-alt text-support-text",
  success: "bg-green-50 text-support-success",
  warning: "bg-amber-50 text-support-warning",
  danger: "bg-support-danger-bg text-support-danger-text",
  info: "bg-blue-50 text-support-primary",
};

export function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
