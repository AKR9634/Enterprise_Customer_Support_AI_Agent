import { ReactNode } from "react";
import { AuthProvider } from "../components/AuthContext";
import { ToastProvider } from "../components/ui/ToastProvider";
import "./globals.css";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ToastProvider>{children}</ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
