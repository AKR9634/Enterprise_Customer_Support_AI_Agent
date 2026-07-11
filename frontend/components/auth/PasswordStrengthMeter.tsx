"use client";

import { useMemo } from "react";

export interface PasswordStrengthMeterProps {
  password: string;
}

type StrengthLevel = "empty" | "weak" | "fair" | "strong" | "very-strong";

const LEVELS: { label: string; value: StrengthLevel; minFraction: number }[] = [
  { label: "Weak", value: "weak", minFraction: 0 },
  { label: "Fair", value: "fair", minFraction: 0.25 },
  { label: "Strong", value: "strong", minFraction: 0.5 },
  { label: "Very strong", value: "very-strong", minFraction: 0.75 },
];

const FILL_COLORS: Record<StrengthLevel, string> = {
  empty: "bg-gray-200",
  weak: "bg-support-danger",
  fair: "bg-support-warning",
  strong: "bg-support-success",
  "very-strong": "bg-support-success",
};

function assessStrength(pw: string): StrengthLevel {
  const len = pw.length;
  if (len === 0) return "empty";
  if (len < 6) return "weak";

  const hasUpper = /[A-Z]/.test(pw);
  const hasLower = /[a-z]/.test(pw);
  const hasDigit = /\d/.test(pw);
  const hasSpecial = /[^a-zA-Z0-9]/.test(pw);

  let score = 0;
  if (len >= 8) score++;
  if (len >= 12) score++;
  if (hasUpper && hasLower) score++;
  if (hasDigit) score++;
  if (hasSpecial) score++;

  if (score >= 5) return "very-strong";
  if (score >= 3) return "strong";
  if (score >= 1) return "fair";
  return "weak";
}

export function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps) {
  const strength = useMemo(() => assessStrength(password), [password]);

  const activeSegments =
    strength === "empty"
      ? 0
      : strength === "weak"
      ? 1
      : strength === "fair"
      ? 2
      : strength === "strong"
      ? 3
      : 4;

  const label = strength === "empty" ? "" : strength === "very-strong" ? "Very strong" : LEVELS.find((l) => l.value === strength)?.label ?? "";

  return (
    <div className="mt-1">
      <div className="flex gap-1">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full transition-colors ${
              i < activeSegments ? FILL_COLORS[strength] : "bg-support-border"
            }`}
          />
        ))}
      </div>
      {label && (
        <p
          className={`mt-1 text-xs ${
            strength === "weak"
              ? "text-support-danger"
              : strength === "fair"
              ? "text-support-warning"
              : "text-support-success"
          }`}
        >
          {label}
        </p>
      )}
    </div>
  );
}
