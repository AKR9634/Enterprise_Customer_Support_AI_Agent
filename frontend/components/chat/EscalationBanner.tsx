import { IconAlertTriangle } from "@tabler/icons-react";

export interface EscalationBannerProps {
  reason: string;
  className?: string;
}

export function EscalationBanner({ reason, className = "" }: EscalationBannerProps) {
  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-lg bg-support-danger-bg border border-support-danger/20 ${className}`}
    >
      <IconAlertTriangle size={20} className="mt-0.5 shrink-0 text-support-danger" />
      <div className="text-sm text-support-danger-text">
        <p className="font-medium">Escalated to human agent</p>
        <p className="mt-0.5">{reason}</p>
        <p className="mt-1 text-xs opacity-80">
          A support agent will review your request and follow up shortly.
        </p>
      </div>
    </div>
  );
}
