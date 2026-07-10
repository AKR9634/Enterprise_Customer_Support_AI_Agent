"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthContext";
import AgentQueueList from "../../components/AgentQueueList";
import AgentContextPanel from "../../components/AgentContextPanel";
import AgentReplyForm from "../../components/AgentReplyForm";

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

export default function AgentPage() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [queue, setQueue] = useState<EscalationItem[]>([]);
  const [queueLoading, setQueueLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [context, setContext] = useState<ContextEscalation | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [claimLoading, setClaimLoading] = useState(false);

  useEffect(() => {
    if (user === null) {
      router.push("/auth/login");
    } else if (user.role !== "agent") {
      router.push("/auth/login");
    }
  }, [user, router]);

  const fetchQueue = useCallback(async () => {
    if (!token) return;
    setQueueLoading(true);
    try {
      const res = await fetch("/escalations", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setQueue(data.escalations || []);
      }
    } catch {
      // silently fail — queue stays empty
    } finally {
      setQueueLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  async function handleClaim(id: string) {
    if (!token) return;
    setClaimLoading(true);
    try {
      const res = await fetch(`/escalations/${id}/claim`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      setSelectedId(id);
      setContextLoading(true);
      const ctxRes = await fetch(`/escalations/${id}/context`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (ctxRes.ok) {
        const ctx = await ctxRes.json();
        setContext(ctx);
        setQueue((prev) => prev.filter((e) => e.id !== id));
      }
    } finally {
      setClaimLoading(false);
      setContextLoading(false);
    }
  }

  function handleBack() {
    setSelectedId(null);
    setContext(null);
    fetchQueue();
  }

  if (!user || user.role !== "agent") {
    return null;
  }

  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "24px 16px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700 }}>Agent Dashboard</h1>
          <p style={{ margin: "4px 0 0", fontSize: 14, color: "#6b7280" }}>
            {user.full_name} · {user.email}
          </p>
        </div>
        <button
          onClick={() => router.push("/auth/login")}
          style={{
            padding: "8px 16px",
            fontSize: 13,
            border: "1px solid #d1d5db",
            borderRadius: 6,
            background: "#fff",
            cursor: "pointer",
          }}
        >
          Sign out
        </button>
      </div>

      {selectedId && context ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div>
            <button
              onClick={handleBack}
              style={{
                padding: "6px 12px",
                fontSize: 13,
                border: "1px solid #d1d5db",
                borderRadius: 6,
                background: "#fff",
                cursor: "pointer",
                marginBottom: 16,
              }}
            >
              ← Back to queue
            </button>
            <AgentContextPanel escalation={context} loading={false} />
          </div>
          <div
            style={{
              borderTop: "1px solid #e5e7eb",
              paddingTop: 20,
            }}
          >
            <h2
              style={{
                margin: "0 0 12px",
                fontSize: 16,
                fontWeight: 600,
              }}
            >
              Manual Reply
            </h2>
            <AgentReplyForm escalationId={selectedId} onSent={handleBack} />
          </div>
        </div>
      ) : (
        <AgentQueueList
          escalations={queue}
          onClaim={handleClaim}
          loading={queueLoading || claimLoading}
        />
      )}
    </main>
  );
}
