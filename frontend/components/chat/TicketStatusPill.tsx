import { StatusPill, type TicketStatus } from "../ui/StatusPill";

export interface TicketStatusPillProps {
  status: TicketStatus;
  className?: string;
}

export function TicketStatusPill({ status, className = "" }: TicketStatusPillProps) {
  return <StatusPill status={status} className={className} />;
}
