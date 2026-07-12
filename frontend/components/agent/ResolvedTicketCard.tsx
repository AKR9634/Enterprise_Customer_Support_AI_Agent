"use client";

import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";

interface ResolvedTicketCardProps {
  id: string;
  ticket_id: string;
  category: string | null;
  customer_message: string | null;
  escalation_reason: string;
  updated_at: string;
  final_reply: string | null;
  onViewDetails: (id: string) => void;
}

const CATEGORY_BADGE: Record<string, "warning" | "info" | "default" | "success"> = {
  billing: "warning",
  order: "info",
  account: "default",
  product: "success",
  general: "default",
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ResolvedTicketCard({
  id,
  category,
  customer_message,
  escalation_reason,
  updated_at,
  final_reply,
  onViewDetails,
}: ResolvedTicketCardProps) {
  const categoryVariant = CATEGORY_BADGE[category ?? ""] ?? "default";

  return (
    <Card padding="md" className="hover:border-support-primary transition-colors cursor-pointer" onClick={() => onViewDetails(id)}>
      <div className="flex items-center gap-2 flex-wrap mb-2">
        {category && <Badge variant={categoryVariant}>{category}</Badge>}
        <span className="text-xs text-support-text-faint ml-auto">
          {formatDate(updated_at)}
        </span>
      </div>
      <p className="m-0 text-sm text-support-text truncate">
        {customer_message || escalation_reason}
      </p>
      {final_reply && (
        <p className="m-0 mt-1 text-xs text-support-text-muted truncate">
          Reply: {final_reply}
        </p>
      )}
    </Card>
  );
}
