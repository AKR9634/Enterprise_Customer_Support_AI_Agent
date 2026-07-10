"use client";

interface ContextEscalation {
  escalation_id: string;
  ticket_id: string;
  customer_message: string | null;
  draft_response: string | null;
  escalation_reason: string;
  routing_reason: string | null;
  category: string | null;
  confidence: number | null;
  retrieved_docs: Record<string, unknown>[];
  business_data: Record<string, unknown>;
}

interface Props {
  escalation: ContextEscalation | null;
  loading: boolean;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <h3
        style={{
          margin: "0 0 6px",
          fontSize: 13,
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          color: "#6b7280",
        }}
      >
        {title}
      </h3>
      {children}
    </div>
  );
}

export default function AgentContextPanel({ escalation, loading }: Props) {
  if (loading) {
    return (
      <div style={{ padding: 24, color: "#6b7280" }}>
        Loading escalation context…
      </div>
    );
  }

  if (!escalation) {
    return (
      <div
        style={{
          padding: 24,
          color: "#9ca3af",
          textAlign: "center",
          border: "2px dashed #e5e7eb",
          borderRadius: 8,
        }}
      >
        Claim an escalation to view its context.
      </div>
    );
  }

  const confidenceColor =
    escalation.confidence == null
      ? "#dc2626"
      : escalation.confidence >= 0.8
        ? "#16a34a"
        : escalation.confidence >= 0.5
          ? "#d97706"
          : "#dc2626";

  return (
    <div>
      <div
        style={{
          display: "flex",
          gap: 12,
          fontSize: 12,
          color: "#6b7280",
          marginBottom: 24,
        }}
      >
        <span>Ticket: <strong>{escalation.ticket_id}</strong></span>
        <span>|</span>
        <span>
          Confidence:{" "}
          <strong style={{ color: confidenceColor }}>
            {escalation.confidence != null
              ? `${(escalation.confidence * 100).toFixed(0)}%`
              : "N/A"}
          </strong>
        </span>
        <span>|</span>
        <span>Category: <strong>{escalation.category || "—"}</strong></span>
      </div>

      <Section title="Customer message">
        <div
          style={{
            background: "#f9fafb",
            borderRadius: 6,
            padding: 12,
            fontSize: 14,
            lineHeight: 1.5,
            whiteSpace: "pre-wrap",
          }}
        >
          {escalation.customer_message || "(empty)"}
        </div>
      </Section>

      <Section title="Draft AI response">
        <div
          style={{
            background: "#f9fafb",
            borderRadius: 6,
            padding: 12,
            fontSize: 14,
            lineHeight: 1.5,
            whiteSpace: "pre-wrap",
          }}
        >
          {escalation.draft_response || "(empty)"}
        </div>
      </Section>

      <Section title="Escalation reason">
        <div
          style={{
            background: "#fef2f2",
            borderRadius: 6,
            padding: 12,
            fontSize: 14,
            color: "#991b1b",
          }}
        >
          {escalation.escalation_reason}
        </div>
      </Section>

      <Section title="Routing reason">
        <div style={{ fontSize: 14, color: "#374151" }}>
          {escalation.routing_reason || "(not recorded)"}
        </div>
      </Section>

      {escalation.retrieved_docs.length > 0 && (
        <Section title="Retrieved documents">
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {escalation.retrieved_docs.map((doc, i) => (
              <div
                key={i}
                style={{
                  background: "#f3f4f6",
                  borderRadius: 6,
                  padding: "8px 12px",
                  fontSize: 13,
                }}
              >
                <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                  {JSON.stringify(doc, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </Section>
      )}

      {Object.keys(escalation.business_data).length > 0 && (
        <Section title="Business data">
          <div
            style={{
              background: "#f3f4f6",
              borderRadius: 6,
              padding: 12,
              fontSize: 13,
            }}
          >
            <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
              {JSON.stringify(escalation.business_data, null, 2)}
            </pre>
          </div>
        </Section>
      )}
    </div>
  );
}
