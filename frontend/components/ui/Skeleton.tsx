export interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  className = "",
  variant = "text",
  width,
  height,
}: SkeletonProps) {
  const baseClass = "animate-pulse bg-support-surface-alt";
  const variantClass =
    variant === "circular"
      ? "rounded-full"
      : variant === "rectangular"
      ? "rounded-md"
      : "rounded h-4";

  return (
    <div
      className={`${baseClass} ${variantClass} ${className}`}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}
