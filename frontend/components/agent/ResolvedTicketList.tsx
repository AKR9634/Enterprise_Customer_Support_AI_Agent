"use client";

import { ResolvedTicketCard } from "./ResolvedTicketCard";
import { Skeleton } from "../ui/Skeleton";
import { EmptyState } from "../ui/EmptyState";
import { IconCircleCheck } from "@tabler/icons-react";

interface ResolvedItem {
  id: string;
  ticket_id: string;
  category: string | null;
  customer_message: string | null;
  escalation_reason: string;
  updated_at: string;
  final_reply: string | null;
}

interface Props {
  resolved: ResolvedItem[];
  loading: boolean;
  onViewDetails: (id: string) => void;
}

export function ResolvedTicketList({ resolved, loading, onViewDetails }: Props) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="border border-support-border rounded-lg p-4 bg-white">
            <div className="flex gap-2 mb-2">
              <Skeleton variant="text" className="w-20 h-5" />
            </div>
            <Skeleton variant="text" className="w-full h-4 mb-1" />
            <Skeleton variant="text" className="w-2/3 h-4" />
          </div>
        ))}
      </div>
    );
  }

  if (resolved.length === 0) {
    return (
      <EmptyState
        icon={<IconCircleCheck size={40} />}
        title="No resolved tickets"
        description="Tickets you resolve will appear here."
      />
    );
  }

  return (
    <div className="space-y-2">
      {resolved.map((item) => (
        <ResolvedTicketCard
          key={item.id}
          id={item.id}
          ticket_id={item.ticket_id}
          category={item.category}
          customer_message={item.customer_message}
          escalation_reason={item.escalation_reason}
          updated_at={item.updated_at}
          final_reply={item.final_reply}
          onViewDetails={onViewDetails}
        />
      ))}
    </div>
  );
}
