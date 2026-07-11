"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
}

const variantStyles: Record<string, string> = {
  primary:
    "bg-support-primary text-white border-transparent hover:opacity-90 active:opacity-80",
  secondary:
    "bg-white text-support-text border-support-border-strong hover:bg-support-surface active:bg-support-surface-alt",
  danger:
    "bg-support-danger text-white border-transparent hover:opacity-90 active:opacity-80",
  ghost:
    "bg-transparent text-support-text border-transparent hover:bg-support-surface active:bg-support-surface-alt",
};

const sizeStyles: Record<string, string> = {
  sm: "px-3 py-1.5 text-xs rounded",
  md: "px-5 py-2.5 text-sm rounded-md",
  lg: "px-6 py-3 text-base rounded-md",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className = "", disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={`inline-flex items-center justify-center font-medium border cursor-pointer transition-all disabled:cursor-not-allowed disabled:opacity-50 ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
