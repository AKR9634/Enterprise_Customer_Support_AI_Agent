"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../components/AuthContext";
import { TicketHistoryList, type TicketSummary } from "../../../components/chat/TicketHistoryList";
import { MessageBubble } from "../../../components/chat/MessageBubble";
import { Skeleton } from "../../../components/ui/Skeleton";
import { Button } from "../../../components/ui/Button";
import { IconArrowLeft, IconMessageCircle } from "@tabler/icons-react";

interface Message {
  id: string;
  role: "customer" | "ai";
  content: string;
  created_at: string;
}

export default function ChatHistoryPage() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [tickets, setTickets] = useState<TicketSummary[]>([]);
  const [ticketsLoading, setTicketsLoading] = useState(true);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);

  useEffect(() => {
    if (user === null) router.push("/auth/login");
  }, [user, router]);

  useEffect(() => {
    if (!token) return;
    setTicketsLoading(true);
    fetch("/tickets", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch tickets");
        return res.json();
      })
      .then((data: { tickets: TicketSummary[] }) => {
        setTickets(data.tickets ?? []);
      })
      .catch(() => {
        setTickets([]);
      })
      .finally(() => setTicketsLoading(false));
  }, [token]);

  const handleSelectTicket = (ticketId: string) => {
    if (selectedTicketId === ticketId) return;
    setSelectedTicketId(ticketId);
    setMessages([]);
    setMessagesLoading(true);

    fetch(`/tickets/${ticketId}/messages`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch messages");
        return res.json();
      })
      .then((data: { ticket_id: string; messages: Message[] }) => {
        setMessages(data.messages ?? []);
      })
      .catch(() => {
        setMessages([]);
      })
      .finally(() => setMessagesLoading(false));
  };

  const handleBack = () => {
    setSelectedTicketId(null);
    setMessages([]);
  };

  if (!user) return null;

  return (
    <main className="max-w-4xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-support-text m-0">Chat History</h1>
          <p className="text-sm text-support-text-muted mt-1">
            {user.full_name} · {user.email}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => router.push("/chat")}>
            Back to Chat
          </Button>
          <Button variant="secondary" size="sm" onClick={() => router.push("/auth/login")}>
            Sign out
          </Button>
        </div>
      </div>

      <div className="border border-support-border rounded-lg bg-white flex flex-col min-h-[500px] md:flex-row">
        {/* Ticket list panel */}
        <div className={`border-support-border md:border-r md:w-80 shrink-0 ${selectedTicketId ? "hidden md:block" : "block"}`}>
          <div className="p-4 border-b border-support-border">
            <h2 className="text-sm font-semibold text-support-text">Past Tickets</h2>
          </div>
          <div className="p-3 overflow-y-auto max-h-[600px]">
            <TicketHistoryList
              tickets={tickets}
              selectedId={selectedTicketId}
              onSelect={handleSelectTicket}
              loading={ticketsLoading}
            />
          </div>
        </div>

        {/* Message detail panel */}
        <div className={`flex-1 flex flex-col ${!selectedTicketId ? "hidden md:flex" : "flex"}`}>
          {selectedTicketId && messagesLoading && (
            <div className="flex-1 p-6 space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-3">
                  <Skeleton variant="rectangular" className="w-3/4 h-12" />
                </div>
              ))}
            </div>
          )}

          {selectedTicketId && !messagesLoading && messages.length > 0 && (
            <>
              <div className="flex items-center gap-2 p-4 border-b border-support-border md:hidden">
                <button
                  type="button"
                  onClick={handleBack}
                  className="text-support-text-muted hover:text-support-text transition-colors"
                >
                  <IconArrowLeft size={20} />
                </button>
                <span className="text-sm font-medium text-support-text">Conversation</span>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-1 max-h-[600px]">
                {messages.map((msg) => (
                  <MessageBubble
                    key={msg.id}
                    role={msg.role}
                    content={msg.content}
                  />
                ))}
              </div>
              <div className="p-4 border-t border-support-border bg-support-surface text-center text-xs text-support-text-muted">
                This conversation is read-only
              </div>
            </>
          )}

          {selectedTicketId && !messagesLoading && messages.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center text-support-text-faint p-6">
              <IconMessageCircle size={40} className="mb-3" />
              <p className="text-sm">No messages in this ticket.</p>
            </div>
          )}

          {!selectedTicketId && (
            <div className="flex-1 hidden md:flex flex-col items-center justify-center text-support-text-faint p-6">
              <IconMessageCircle size={48} className="mb-3" />
              <p className="text-sm">Select a ticket to view its conversation.</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
