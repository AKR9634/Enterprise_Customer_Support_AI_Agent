"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../components/AuthContext";
import { ResolvedTicketList } from "../../../components/agent/ResolvedTicketList";
import { Button } from "../../../components/ui/Button";
import { IconArrowLeft, IconHeadset } from "@tabler/icons-react";

interface ResolvedItem {
  id: string;
  ticket_id: string;
  category: string | null;
  customer_message: string | null;
  escalation_reason: string;
  updated_at: string;
  final_reply: string | null;
}

export default function AgentResolvedPage() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [resolved, setResolved] = useState<ResolvedItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user === null) {
      router.push("/auth/login");
    } else if (user.role !== "agent") {
      router.push("/auth/login");
    }
  }, [user, router]);

  const fetchResolved = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch("/escalations/resolved", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setResolved(data.resolved_escalations || []);
      }
    } catch {
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchResolved();
  }, [fetchResolved]);

  function handleViewDetails(id: string) {
    router.push(`/agent`);
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
            <h1 className="m-0 text-base font-bold text-support-text">Resolved Tickets</h1>
            <p className="m-0 text-xs text-support-text-muted">
              {user.full_name} · {user.email}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push("/agent")}>
            <IconArrowLeft size={16} className="mr-1" />
            Back to Dashboard
          </Button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto">
          <ResolvedTicketList
            resolved={resolved}
            loading={loading}
            onViewDetails={handleViewDetails}
          />
        </div>
      </div>
    </div>
  );
}
