"use client";

import { QueueRow } from "./agent/QueueRow";
import { Skeleton } from "./ui/Skeleton";
import { EmptyState } from "./ui/EmptyState";
import { IconInbox } from "@tabler/icons-react";

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

interface Props {
  escalations: EscalationItem[];
  onClaim: (id: string) => void;
  loading: boolean;
}

export default function AgentQueueList({ escalations, onClaim, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="border border-support-border rounded-lg p-4 bg-white">
            <div className="flex gap-2 mb-2">
              <Skeleton variant="text" className="w-16 h-5" />
              <Skeleton variant="text" className="w-20 h-5" />
            </div>
            <Skeleton variant="text" className="w-full h-4 mb-1" />
            <Skeleton variant="text" className="w-1/3 h-4" />
          </div>
        ))}
      </div>
    );
  }

  if (escalations.length === 0) {
    return (
      <EmptyState
        icon={<IconInbox size={40} />}
        title="Queue is empty"
        description="No escalations in the queue right now. Check back later."
      />
    );
  }

  return (
    <div className="space-y-2">
      {escalations.map((esc) => (
        <QueueRow key={esc.id} escalation={esc} onClaim={onClaim} />
      ))}
    </div>
  );
}
