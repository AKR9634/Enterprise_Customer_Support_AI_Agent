import { useMemo } from "react";

export interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeMap: Record<string, string> = {
  sm: "w-8 h-8 text-xs",
  md: "w-10 h-10 text-sm",
  lg: "w-12 h-12 text-base",
};

function getInitials(name?: string): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

export function Avatar({ src, alt = "", name, size = "md", className = "" }: AvatarProps) {
  const initials = useMemo(() => getInitials(name), [name]);

  if (src) {
    return (
      <img
        src={src}
        alt={alt || name || "avatar"}
        className={`rounded-full object-cover ${sizeMap[size]} ${className}`}
      />
    );
  }

  return (
    <div
      className={`rounded-full bg-support-primary flex items-center justify-center text-white font-medium ${sizeMap[size]} ${className}`}
      aria-label={alt || name || "avatar"}
    >
      {initials}
    </div>
  );
}
