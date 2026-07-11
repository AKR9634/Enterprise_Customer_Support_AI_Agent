"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthContext";
import AgentQueueList from "../../components/AgentQueueList";
import AgentContextPanel from "../../components/AgentContextPanel";
import AgentReplyForm from "../../components/AgentReplyForm";
import { AgentStatusToggle } from "../../components/agent/AgentStatusToggle";
import { Button } from "../../components/ui/Button";
import { IconHeadset } from "@tabler/icons-react";

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

  function handleSent() {
    setSelectedId(null);
    setContext(null);
    fetchQueue();
  }

  if (!user || user.role !== "agent") {
    return null;
  }

  return (
    <div className="flex flex-col h-screen bg-support-surface">
      <header className="flex items-center justify-between px-6 py-3 border-b border-support-border bg-white shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-support-primary">
            <IconHeadset size={20} className="text-white" />
          </div>
          <div>
            <h1 className="m-0 text-base font-bold text-support-text">Agent Dashboard</h1>
            <p className="m-0 text-xs text-support-text-muted">
              {user.full_name} · {user.email}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <AgentStatusToggle />
          <Button variant="ghost" size="sm" onClick={() => router.push("/auth/login")}>
            Sign out
          </Button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-[380px] shrink-0 border-r border-support-border bg-white overflow-y-auto p-4">
          <AgentQueueList
            escalations={queue}
            onClaim={handleClaim}
            loading={queueLoading}
          />
        </aside>

        <main className="flex-1 overflow-y-auto p-6">
          {selectedId && context ? (
            <div className="max-w-3xl mx-auto space-y-6">
              <AgentContextPanel escalation={context} loading={false} />
              <div className="border-t border-support-border pt-6">
                <h2 className="m-0 mb-3 text-sm font-semibold text-support-text">
                  Manual Reply
                </h2>
                <AgentReplyForm escalationId={selectedId} onSent={handleSent} />
              </div>
            </div>
          ) : selectedId ? (
            <div className="max-w-3xl mx-auto">
              <AgentContextPanel escalation={null} loading={true} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <p className="text-sm text-support-text-faint">
                Claim an escalation from the queue to review customer context and reply.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
