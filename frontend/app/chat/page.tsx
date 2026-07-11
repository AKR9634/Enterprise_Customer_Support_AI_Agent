"use client";

import { useState, useEffect, useRef, useCallback, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthContext";
import { MessageBubble } from "../../components/chat/MessageBubble";
import { TypingIndicator } from "../../components/chat/TypingIndicator";
import { EscalationBanner } from "../../components/chat/EscalationBanner";
import { ChatEmptyState } from "../../components/chat/ChatEmptyState";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import type { TicketStatus } from "../../components/ui/StatusPill";

interface Message {
  role: "customer" | "ai";
  content: string;
  citations?: string[];
  ticketStatus?: TicketStatus;
}

export default function ChatPage() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [ticketStatus, setTicketStatus] = useState<TicketStatus | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (user === null) router.push("/auth/login");
  }, [user, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSuggestionClick = useCallback((prompt: string) => {
    setInput(prompt);
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || !token || sending) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "customer", content: userMessage }]);
    setSending(true);

    try {
      const res = await fetch("/chat/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userMessage,
          ticket_id: ticketId,
        }),
      });

      if (!res.ok) {
        let detail = "Request failed";
        try {
          const parsed = await res.json();
          detail = parsed.detail || detail;
        } catch {
          const text = await res.text();
          detail = text || detail;
        }
        setMessages((prev) => [
          ...prev,
          { role: "ai", content: `Error: ${detail}` },
        ]);
        return;
      }

      const data = await res.json();
      setTicketId(data.ticket_id);
      setTicketStatus(data.ticket_status || null);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: data.response,
          citations: data.citations || [],
          ticketStatus: data.ticket_status || undefined,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: `Error: ${err instanceof Error ? err.message : "Unable to reach server"}`,
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  if (!user) return null;

  return (
    <main className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-support-text m-0">Customer Support</h1>
          <p className="text-sm text-support-text-muted mt-1">
            {user.full_name} · {user.email}
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => router.push("/auth/login")}>
          Sign out
        </Button>
      </div>

      <div className="border border-support-border rounded-lg bg-white flex flex-col min-h-[500px]">
        <div className="flex-1 overflow-y-auto p-4 space-y-1">
          {ticketStatus === "escalated" && (
            <EscalationBanner
              reason="Your request has been escalated to a human agent for review."
              className="mb-4"
            />
          )}

          {messages.length === 0 ? (
            <ChatEmptyState onSuggestionClick={handleSuggestionClick} />
          ) : (
            messages.map((msg, i) => (
              <MessageBubble
                key={i}
                role={msg.role}
                content={msg.content}
                citations={msg.citations}
                ticketStatus={msg.ticketStatus}
              />
            ))
          )}

          {sending && <TypingIndicator />}

          <div ref={bottomRef} />
        </div>

        <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-support-border p-4">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={sending}
            className="flex-1"
          />
          <Button type="submit" disabled={sending || !input.trim()}>
            {sending ? "Sending..." : "Send"}
          </Button>
        </form>
      </div>
    </main>
  );
}
