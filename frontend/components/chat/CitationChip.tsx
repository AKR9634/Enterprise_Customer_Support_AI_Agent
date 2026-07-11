import { IconFileSearch } from "@tabler/icons-react";

export interface CitationChipProps {
  title: string;
  className?: string;
}

export function CitationChip({ title, className = "" }: CitationChipProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-support-surface-alt text-support-text-muted border border-support-border ${className}`}
    >
      <IconFileSearch size={12} />
      {title}
    </span>
  );
}
