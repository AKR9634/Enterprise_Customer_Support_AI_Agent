"use client";

import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

interface EscalationItem {
  id: string;
  ticket_id: string;
  status: string;
  priority: string;
  category: string | null;
  customer_message: string | null;
  escalation_reason: string;
  confidence: number | null;
  created_at: string;
}

interface QueueRowProps {
  escalation: EscalationItem;
  onClaim: (id: string) => void;
}

const PRIORITY_BADGE: Record<string, "danger" | "warning" | "info" | "default"> = {
  urgent: "danger",
  high: "warning",
  normal: "info",
  low: "default",
};

const CATEGORY_BADGE: Record<string, "warning" | "info" | "default" | "success"> = {
  billing: "warning",
  order: "info",
  account: "default",
  product: "success",
  general: "default",
};

function getWaitTime(createdAt: string): string {
  const diff = Date.now() - new Date(createdAt).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  const remainMins = mins % 60;
  if (hours < 24) return `${hours}h ${remainMins}m`;
  const days = Math.floor(hours / 24);
  return `${days}d`;
}

export function QueueRow({ escalation: esc, onClaim }: QueueRowProps) {
  const priorityVariant = PRIORITY_BADGE[esc.priority] ?? "default";
  const categoryVariant = CATEGORY_BADGE[esc.category ?? ""] ?? "default";

  return (
    <div className="border border-support-border rounded-lg p-4 bg-white flex flex-col gap-2 hover:border-support-primary transition-colors">
      <div className="flex items-center gap-2 flex-wrap">
        <Badge variant={priorityVariant}>{esc.priority}</Badge>
        {esc.category && <Badge variant={categoryVariant}>{esc.category}</Badge>}
        <span className="text-xs text-support-text-faint ml-auto">
          {getWaitTime(esc.created_at)}
        </span>
      </div>
      <p className="m-0 text-sm text-support-text truncate">
        {esc.customer_message || esc.escalation_reason}
      </p>
      <div className="flex items-center justify-between">
        <span className="text-xs text-support-text-muted">
          {esc.confidence != null
            ? `${(esc.confidence * 100).toFixed(0)}% confidence`
            : "—"}
        </span>
        <Button
          variant="primary"
          size="sm"
          onClick={() => onClaim(esc.id)}
          disabled={esc.status !== "queued"}
        >
          Claim
        </Button>
      </div>
    </div>
  );
}
