import clsx from "clsx";
import { CitationChip } from "./CitationChip";
import { TicketStatusPill } from "./TicketStatusPill";
import type { TicketStatus } from "../ui/StatusPill";

export interface MessageBubbleProps {
  role: "customer" | "ai";
  content: string;
  citations?: string[];
  ticketStatus?: TicketStatus;
  className?: string;
}

export function MessageBubble({ role, content, citations, ticketStatus, className = "" }: MessageBubbleProps) {
  const isCustomer = role === "customer";

  return (
    <div className={clsx("flex mb-3", isCustomer ? "justify-end" : "justify-start", className)}>
      <div
        className={clsx(
          "inline-block max-w-[80%] rounded-bubble px-4 py-2.5 text-sm leading-relaxed",
          isCustomer
            ? "bg-support-primary text-white rounded-br-sm"
            : "bg-support-surface-alt text-support-text rounded-bl-sm border border-support-border"
        )}
      >
        <p className="whitespace-pre-wrap">{content}</p>

        {!isCustomer && citations && citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-support-border/50">
            {citations.map((title) => (
              <CitationChip key={title} title={title} />
            ))}
          </div>
        )}

        {!isCustomer && ticketStatus && (
          <div className="mt-2">
            <TicketStatusPill status={ticketStatus} />
          </div>
        )}
      </div>
    </div>
  );
}
