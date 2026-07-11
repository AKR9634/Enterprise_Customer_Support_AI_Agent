"use client";

import type { TicketStatus } from "../ui/StatusPill";
import { StatusPill } from "../ui/StatusPill";
import { Badge } from "../ui/Badge";

const CATEGORY_BADGES: Record<string, "info" | "success" | "warning" | "danger" | "default"> = {
  billing: "warning",
  order: "info",
  account: "default",
  product: "success",
  general: "default",
};

export interface TicketHistoryCardProps {
  ticket: {
    id: string;
    subject: string;
    status: TicketStatus;
    created_at: string;
    category?: string;
  };
  onClick: (ticketId: string) => void;
  isSelected?: boolean;
}

export function TicketHistoryCard({ ticket, onClick, isSelected }: TicketHistoryCardProps) {
  const badgeVariant = CATEGORY_BADGES[ticket.category ?? ""] ?? "default";

  return (
    <div
      onClick={() => onClick(ticket.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onClick(ticket.id); }}
      className={`border border-support-border rounded-lg bg-white p-4 cursor-pointer transition-colors hover:border-support-primary ${
        isSelected ? "border-support-primary ring-1 ring-support-primary" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-support-text truncate">
            {ticket.subject}
          </h3>
          <p className="text-xs text-support-text-muted mt-1">
            {new Date(ticket.created_at).toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {ticket.category && (
            <Badge variant={badgeVariant}>{ticket.category}</Badge>
          )}
          <StatusPill status={ticket.status} />
        </div>
      </div>
    </div>
  );
}
