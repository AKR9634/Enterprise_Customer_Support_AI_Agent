import { ReactNode } from "react";

export interface EmptyStateProps {
  icon?: ReactNode;
  title?: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-16 px-4 ${className}`}>
      {icon && <div className="mb-4 text-support-text-faint">{icon}</div>}
      {title && (
        <h3 className="text-lg font-medium text-support-text mb-1">{title}</h3>
      )}
      {description && (
        <p className="text-sm text-support-text-muted text-center max-w-sm">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
