"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../components/AuthContext";
import { useToast } from "../../../components/ui/ToastProvider";
import { Input } from "../../../components/ui/Input";
import { Button } from "../../../components/ui/Button";
import { AuthLayout } from "../../../components/auth/AuthLayout";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const { addToast } = useToast();
  const router = useRouter();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    try {
      const user = await login(email, password);
      if (rememberMe) {
        localStorage.setItem("remember_email", email);
      } else {
        localStorage.removeItem("remember_email");
      }
      router.push(user.role === "agent" ? "/agent" : "/chat");
    } catch (err: unknown) {
      addToast(
        err instanceof Error ? err.message : "Sign in failed. Please check your credentials.",
        "error"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <h2 className="mb-1 text-2xl font-bold text-support-text">Sign in</h2>
      <p className="mb-6 text-sm text-support-text-muted">
        Welcome back! Enter your credentials to continue.
      </p>
      <form onSubmit={handleSubmit} noValidate>
        <div className="mb-4">
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-support-text">
            Email
          </label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            autoComplete="email"
            required
          />
        </div>
        <div className="mb-4">
          <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-support-text">
            Password
          </label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            autoComplete="current-password"
            required
          />
        </div>
        <div className="mb-6 flex items-center gap-2">
          <input
            id="remember"
            type="checkbox"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
            className="h-4 w-4 rounded border-support-border-strong text-support-primary focus:ring-support-primary"
          />
          <label htmlFor="remember" className="text-sm text-support-text-muted cursor-pointer select-none">
            Remember me
          </label>
        </div>
        <Button type="submit" size="lg" className="w-full" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-support-text-muted">
        No account?{" "}
        <a href="/auth/register" className="font-medium text-support-primary hover:underline">
          Register
        </a>
      </p>
      <p className="mt-4 text-center text-xs text-support-text-faint">
        Protected by enterprise-grade encryption
      </p>
    </AuthLayout>
  );
}
