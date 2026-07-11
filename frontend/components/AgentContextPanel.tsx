"use client";

import { Badge } from "./ui/Badge";
import { Card } from "./ui/Card";
import { Skeleton } from "./ui/Skeleton";

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

const CATEGORY_BADGE: Record<string, "warning" | "info" | "default" | "success"> = {
  billing: "warning",
  order: "info",
  account: "default",
  product: "success",
  general: "default",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <h3 className="m-0 mb-1.5 text-xs font-semibold uppercase tracking-wider text-support-text-muted">
        {title}
      </h3>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-support-text">
      <span className="text-support-text-muted">{label}:</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function StructuredData({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data);
  if (entries.length === 0) return <span className="text-sm text-support-text-faint">No data</span>;

  return (
    <div className="space-y-1.5">
      {entries.map(([key, value]) => (
        <div key={key} className="flex gap-2 text-sm">
          <span className="text-support-text-muted font-medium shrink-0 min-w-[120px]">
            {key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}:
          </span>
          <span className="text-support-text">
            {typeof value === "object" && value !== null
              ? JSON.stringify(value)
              : String(value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function AgentContextPanel({ escalation, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton variant="rectangular" className="w-full h-20" />
        <Skeleton variant="rectangular" className="w-full h-16" />
        <Skeleton variant="rectangular" className="w-full h-24" />
      </div>
    );
  }

  if (!escalation) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-support-text-faint text-center px-4">
          Claim an escalation from the queue to view customer context, AI draft, and business data.
        </p>
      </div>
    );
  }

  const categoryVariant = CATEGORY_BADGE[escalation.category ?? ""] ?? "default";

  const confidenceColor =
    escalation.confidence == null
      ? "text-support-danger"
      : escalation.confidence >= 0.8
        ? "text-support-success"
        : escalation.confidence >= 0.5
          ? "text-support-warning"
          : "text-support-danger";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap text-sm">
        <InfoRow label="Ticket" value={escalation.ticket_id} />
        <span className="text-support-border-strong">|</span>
        <div className="flex items-center gap-1">
          <span className="text-support-text-muted">Confidence:</span>
          <span className={`font-medium ${confidenceColor}`}>
            {escalation.confidence != null
              ? `${(escalation.confidence * 100).toFixed(0)}%`
              : "N/A"}
          </span>
        </div>
        <span className="text-support-border-strong">|</span>
        <Badge variant={categoryVariant}>{escalation.category || "uncategorized"}</Badge>
      </div>

      <Section title="Customer message">
        <Card padding="sm">
          <p className="m-0 text-sm text-support-text whitespace-pre-wrap leading-relaxed">
            {escalation.customer_message || (
              <span className="text-support-text-faint italic">(empty)</span>
            )}
          </p>
        </Card>
      </Section>

      <Section title="Draft AI response">
        <Card padding="sm" className="bg-support-surface border-support-border">
          <p className="m-0 text-sm text-support-text whitespace-pre-wrap leading-relaxed">
            {escalation.draft_response || (
              <span className="text-support-text-faint italic">(empty)</span>
            )}
          </p>
        </Card>
      </Section>

      <Section title="Escalation reason">
        <Card padding="sm" className="bg-support-danger-bg border-support-danger/20">
          <p className="m-0 text-sm text-support-danger-text">
            {escalation.escalation_reason}
          </p>
        </Card>
      </Section>

      <Section title="Routing reason">
        <p className="m-0 text-sm text-support-text">
          {escalation.routing_reason || (
            <span className="text-support-text-faint italic">(not recorded)</span>
          )}
        </p>
      </Section>

      {escalation.retrieved_docs.length > 0 && (
        <Section title="Retrieved documents">
          <div className="space-y-2">
            {escalation.retrieved_docs.map((doc, i) => (
              <Card key={i} padding="sm" className="bg-support-surface-alt">
                <pre className="m-0 text-xs text-support-text whitespace-pre-wrap font-sans leading-relaxed">
                  {JSON.stringify(doc, null, 2)}
                </pre>
              </Card>
            ))}
          </div>
        </Section>
      )}

      {Object.keys(escalation.business_data).length > 0 && (
        <Section title="Business data">
          <Card padding="sm" className="bg-support-surface-alt">
            <StructuredData data={escalation.business_data} />
          </Card>
        </Section>
      )}
    </div>
  );
}
