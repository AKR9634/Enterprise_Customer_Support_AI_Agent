"use client";

import { useState, useEffect, useRef, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthContext";

interface Message {
  role: string;
  content: string;
}

export default function ChatPage() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (user === null) router.push("/auth/login");
  }, [user, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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

      const body = await res.text();
      if (!res.ok) {
        let detail = "Request failed";
        try {
          const parsed = JSON.parse(body);
          detail = parsed.detail || detail;
        } catch {
          detail = body || detail;
        }
        setMessages((prev) => [
          ...prev,
          { role: "ai", content: `Error: ${detail}` },
        ]);
        return;
      }

      const data = JSON.parse(body);
      setTicketId(data.ticket_id);
      setMessages((prev) => [...prev, { role: "ai", content: data.response }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: `Error: ${err instanceof Error ? err.message : "Unable to reach server"}` },
      ]);
    } finally {
      setSending(false);
    }
  }

  if (!user) return null;

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "24px 16px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700 }}>
            Customer Support
          </h1>
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

      <div
        style={{
          border: "1px solid #e5e7eb",
          borderRadius: 8,
          padding: 16,
          minHeight: 400,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ flex: 1, overflowY: "auto", marginBottom: 16 }}>
          {messages.length === 0 && (
            <p style={{ color: "#9ca3af", textAlign: "center", marginTop: 120 }}>
              Send a message to start a conversation.
            </p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                marginBottom: 12,
                textAlign: msg.role === "customer" ? "right" : "left",
              }}
            >
              <span
                style={{
                  display: "inline-block",
                  padding: "8px 14px",
                  borderRadius: 12,
                  fontSize: 14,
                  lineHeight: 1.5,
                  maxWidth: "80%",
                  background: msg.role === "customer" ? "#3b82f6" : "#f3f4f6",
                  color: msg.role === "customer" ? "#fff" : "#111",
                }}
              >
                {msg.content}
              </span>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={sending}
            style={{
              flex: 1,
              padding: "10px 14px",
              fontSize: 14,
              border: "1px solid #d1d5db",
              borderRadius: 6,
            }}
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            style={{
              padding: "10px 20px",
              fontSize: 14,
              border: "none",
              borderRadius: 6,
              background: "#3b82f6",
              color: "#fff",
              cursor: sending ? "not-allowed" : "pointer",
              opacity: sending ? 0.6 : 1,
            }}
          >
            {sending ? "..." : "Send"}
          </button>
        </form>
      </div>
    </main>
  );
}
