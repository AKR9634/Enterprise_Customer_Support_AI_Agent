"use client";

import { InputHTMLAttributes, forwardRef } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", error, ...props }, ref) => {
    return (
      <div className="w-full">
        <input
          ref={ref}
          className={`w-full px-3.5 py-2.5 text-sm border rounded-md outline-none transition-colors placeholder:text-support-text-faint ${
            error
              ? "border-support-danger focus:border-support-danger"
              : "border-support-border-strong focus:border-support-primary"
          } ${className}`}
          {...props}
        />
        {error && (
          <p className="mt-1 text-xs text-support-danger">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
