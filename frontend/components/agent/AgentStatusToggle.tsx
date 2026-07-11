"use client";

import { useState } from "react";

export function AgentStatusToggle() {
  const [available, setAvailable] = useState(true);

  return (
    <button
      type="button"
      onClick={() => setAvailable((v) => !v)}
      className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-full border transition-colors cursor-pointer ${
        available
          ? "bg-green-50 text-support-success border-support-success/30"
          : "bg-support-surface-alt text-support-text-muted border-support-border"
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          available ? "bg-support-success" : "bg-support-text-faint"
        }`}
      />
      {available ? "Available" : "Away"}
    </button>
  );
}
