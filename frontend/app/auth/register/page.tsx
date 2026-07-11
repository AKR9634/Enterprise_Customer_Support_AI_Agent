"use client";

import { useState, type FormEvent, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../components/AuthContext";
import { useToast } from "../../../components/ui/ToastProvider";
import { Input } from "../../../components/ui/Input";
import { Button } from "../../../components/ui/Button";
import { AuthLayout } from "../../../components/auth/AuthLayout";
import { PasswordStrengthMeter } from "../../../components/auth/PasswordStrengthMeter";

interface FieldErrors {
  email?: string;
  fullName?: string;
  password?: string;
}

function validateEmail(email: string): string | undefined {
  if (!email) return "Email is required";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Enter a valid email address";
  return undefined;
}

function validateFullName(name: string): string | undefined {
  if (!name.trim()) return "Full name is required";
  if (name.trim().length < 2) return "Name must be at least 2 characters";
  return undefined;
}

function validatePassword(pw: string): string | undefined {
  if (!pw) return "Password is required";
  if (pw.length < 8) return "Password must be at least 8 characters";
  return undefined;
}

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const { register } = useAuth();
  const { addToast } = useToast();
  const router = useRouter();

  const strengthPassword = useMemo(() => password, [password]);

  function validate(): FieldErrors {
    return {
      email: validateEmail(email),
      fullName: validateFullName(fullName),
      password: validatePassword(password),
    };
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;
    const fieldErrors = validate();
    setErrors(fieldErrors);
    const hasErrors = Object.values(fieldErrors).some(Boolean);
    if (hasErrors) return;

    setSubmitting(true);
    try {
      const user = await register(email, fullName, password);
      router.push(user.role === "agent" ? "/agent" : "/chat");
    } catch (err: unknown) {
      addToast(
        err instanceof Error ? err.message : "Registration failed. Please try again.",
        "error"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <h2 className="mb-1 text-2xl font-bold text-support-text">Create account</h2>
      <p className="mb-6 text-sm text-support-text-muted">
        Sign up to get started with AI-powered support.
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
            onChange={(e) => {
              setEmail(e.target.value);
              if (errors.email) setErrors((prev) => ({ ...prev, email: validateEmail(e.target.value) }));
            }}
            placeholder="you@company.com"
            autoComplete="email"
            error={errors.email}
            required
          />
        </div>
        <div className="mb-4">
          <label htmlFor="fullName" className="mb-1.5 block text-sm font-medium text-support-text">
            Full name
          </label>
          <Input
            id="fullName"
            type="text"
            value={fullName}
            onChange={(e) => {
              setFullName(e.target.value);
              if (errors.fullName) setErrors((prev) => ({ ...prev, fullName: validateFullName(e.target.value) }));
            }}
            placeholder="Jane Smith"
            autoComplete="name"
            error={errors.fullName}
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
            onChange={(e) => {
              setPassword(e.target.value);
              if (errors.password) setErrors((prev) => ({ ...prev, password: validatePassword(e.target.value) }));
            }}
            placeholder="At least 8 characters"
            autoComplete="new-password"
            error={errors.password}
            required
          />
          <PasswordStrengthMeter password={strengthPassword} />
        </div>
        <Button type="submit" size="lg" className="w-full" disabled={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-support-text-muted">
        Already have an account?{" "}
        <a href="/auth/login" className="font-medium text-support-primary hover:underline">
          Sign in
        </a>
      </p>
    </AuthLayout>
  );
}
