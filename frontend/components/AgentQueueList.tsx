"use client";

const PRIORITY_COLORS: Record<string, string> = {
  urgent: "#dc2626",
  high: "#ea580c",
  normal: "#2563eb",
  low: "#6b7280",
};

const STATUS_COLORS: Record<string, string> = {
  queued: "#d97706",
  in_review: "#2563eb",
  resolved: "#16a34a",
};

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
    return <div style={{ padding: 24, color: "#6b7280" }}>Loading queue…</div>;
  }

  if (escalations.length === 0) {
    return (
      <div style={{ padding: 24, color: "#6b7280", textAlign: "center" }}>
        No escalations in the queue.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {escalations.map((esc) => (
        <div
          key={esc.id}
          style={{
            border: "1px solid #e5e7eb",
            borderRadius: 8,
            padding: "12px 16px",
            background: "#fff",
            display: "flex",
            flexDirection: "column",
            gap: 8,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                textTransform: "uppercase",
                color: "#fff",
                background: PRIORITY_COLORS[esc.priority] || "#6b7280",
                padding: "2px 8px",
                borderRadius: 4,
              }}
            >
              {esc.priority}
            </span>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: STATUS_COLORS[esc.status] || "#6b7280",
              }}
            >
              {esc.status}
            </span>
            {esc.category && (
              <span
                style={{
                  fontSize: 11,
                  background: "#f3f4f6",
                  padding: "2px 8px",
                  borderRadius: 4,
                  color: "#374151",
                }}
              >
                {esc.category}
              </span>
            )}
            <span style={{ fontSize: 11, color: "#9ca3af", marginLeft: "auto" }}>
              {esc.confidence != null ? `${(esc.confidence * 100).toFixed(0)}% confidence` : "—"}
            </span>
          </div>

          <p
            style={{
              margin: 0,
              fontSize: 14,
              color: "#374151",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {esc.customer_message || esc.escalation_reason}
          </p>

          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button
              onClick={() => onClaim(esc.id)}
              disabled={esc.status !== "queued"}
              style={{
                padding: "6px 16px",
                fontSize: 13,
                fontWeight: 600,
                border: "none",
                borderRadius: 6,
                cursor: esc.status === "queued" ? "pointer" : "not-allowed",
                background: esc.status === "queued" ? "#2563eb" : "#e5e7eb",
                color: esc.status === "queued" ? "#fff" : "#9ca3af",
              }}
            >
              Claim
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
