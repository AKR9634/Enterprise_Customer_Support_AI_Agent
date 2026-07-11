"use client";

import { ReactNode } from "react";
import { IconHeadset } from "@tabler/icons-react";

export interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <div className="flex items-center justify-center bg-support-primary px-6 py-12 md:w-1/2 md:px-12 lg:px-20">
        <div className="text-center md:text-left">
          <div className="mb-4 flex items-center justify-center gap-3 md:justify-start">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20">
              <IconHeadset className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">Enterprise Support</h1>
          </div>
          <p className="text-sm text-white/80 md:text-base">
            AI-powered customer support platform. Fast, accurate, and available 24/7.
          </p>
        </div>
      </div>
      <div className="flex items-center justify-center px-4 py-12 md:w-1/2 md:px-12 lg:px-20">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  );
}
