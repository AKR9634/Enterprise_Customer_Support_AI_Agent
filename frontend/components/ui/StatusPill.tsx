export type TicketStatus = "open" | "pending" | "resolved" | "escalated" | "closed";

export interface StatusPillProps {
  status: TicketStatus;
  className?: string;
}

const styles: Record<TicketStatus, string> = {
  open: "bg-blue-50 text-support-primary",
  pending: "bg-amber-50 text-support-warning",
  resolved: "bg-green-50 text-support-success",
  escalated: "bg-support-danger-bg text-support-danger-text",
  closed: "bg-support-surface-alt text-support-text-muted",
};

export function StatusPill({ status, className = "" }: StatusPillProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full capitalize ${styles[status]} ${className}`}
    >
      {status}
    </span>
  );
}
