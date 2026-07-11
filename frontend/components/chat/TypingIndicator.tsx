import { IconDots } from "@tabler/icons-react";

export interface TypingIndicatorProps {
  className?: string;
}

export function TypingIndicator({ className = "" }: TypingIndicatorProps) {
  return (
    <div className={`flex items-center gap-2 px-4 py-3 ${className}`}>
      <div className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-full bg-support-text-muted animate-bounce" style={{ animationDelay: "0ms" }} />
        <span className="w-2 h-2 rounded-full bg-support-text-muted animate-bounce" style={{ animationDelay: "150ms" }} />
        <span className="w-2 h-2 rounded-full bg-support-text-muted animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
      <span className="text-xs text-support-text-muted">AI is thinking</span>
    </div>
  );
}
