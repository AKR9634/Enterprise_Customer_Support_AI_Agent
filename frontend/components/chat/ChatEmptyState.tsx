"use client";

import { IconMessageCircle, IconCreditCard, IconTruck, IconUser, IconDeviceLaptop, IconHelp } from "@tabler/icons-react";

const SUGGESTIONS = [
  { label: "Billing", prompt: "I have a question about my bill", icon: IconCreditCard },
  { label: "Order", prompt: "Where is my order?", icon: IconTruck },
  { label: "Account", prompt: "I need help with my account", icon: IconUser },
  { label: "Product", prompt: "Tell me about your products", icon: IconDeviceLaptop },
  { label: "General", prompt: "I need some help", icon: IconHelp },
];

export interface ChatEmptyStateProps {
  onSuggestionClick: (prompt: string) => void;
  className?: string;
}

export function ChatEmptyState({ onSuggestionClick, className = "" }: ChatEmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-16 px-4 ${className}`}>
      <div className="mb-4 text-support-text-faint">
        <IconMessageCircle size={40} />
      </div>
      <h3 className="text-lg font-medium text-support-text mb-1">How can we help?</h3>
      <p className="text-sm text-support-text-muted text-center max-w-sm mb-6">
        Choose a topic below or type your question directly.
      </p>
      <div className="flex flex-wrap justify-center gap-2 max-w-md">
        {SUGGESTIONS.map((s) => {
          const Icon = s.icon;
          return (
            <button
              key={s.label}
              type="button"
              onClick={() => onSuggestionClick(s.prompt)}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border border-support-border bg-white hover:bg-support-surface active:bg-support-surface-alt transition-colors text-support-text"
            >
              <Icon size={16} className="text-support-text-muted" />
              {s.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
