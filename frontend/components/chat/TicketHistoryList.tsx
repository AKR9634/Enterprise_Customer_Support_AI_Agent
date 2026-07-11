"use client";

import type { TicketStatus } from "../ui/StatusPill";
import { Skeleton } from "../ui/Skeleton";
import { TicketHistoryCard } from "./TicketHistoryCard";

export interface TicketSummary {
  id: string;
  subject: string;
  status: TicketStatus;
  created_at: string;
  category?: string;
}

export interface TicketHistoryListProps {
  tickets: TicketSummary[];
  selectedId: string | null;
  onSelect: (ticketId: string) => void;
  loading?: boolean;
}

export function TicketHistoryList({ tickets, selectedId, onSelect, loading }: TicketHistoryListProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="border border-support-border rounded-lg p-4">
            <Skeleton variant="text" className="w-3/4 h-4 mb-2" />
            <Skeleton variant="text" className="w-1/3 h-3" />
          </div>
        ))}
      </div>
    );
  }

  if (tickets.length === 0) {
    return (
      <p className="text-support-text-faint text-center text-sm mt-16">
        No past conversations yet. Start a new chat to create a ticket.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {tickets.map((ticket) => (
        <TicketHistoryCard
          key={ticket.id}
          ticket={ticket}
          onClick={onSelect}
          isSelected={selectedId === ticket.id}
        />
      ))}
    </div>
  );
}
