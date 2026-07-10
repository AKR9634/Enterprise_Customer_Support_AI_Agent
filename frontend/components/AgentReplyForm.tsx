"use client";

import { useState, type FormEvent } from "react";

interface Props {
  escalationId: string;
  onSent: () => void;
}

export default function AgentReplyForm({ escalationId, onSent }: Props) {
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;

    setSending(true);
    setError("");

    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/escalations/${escalationId}/reply`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: message.trim() }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to send reply");
      }

      setMessage("");
      onSent();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to send reply");
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your reply…"
        rows={4}
        disabled={sending}
        style={{
          width: "100%",
          padding: "10px 12px",
          fontSize: 14,
          borderRadius: 6,
          border: "1px solid #d1d5db",
          resize: "vertical",
          fontFamily: "inherit",
          boxSizing: "border-box",
        }}
      />
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button
          type="submit"
          disabled={sending || !message.trim()}
          style={{
            padding: "8px 24px",
            fontSize: 14,
            fontWeight: 600,
            border: "none",
            borderRadius: 6,
            cursor: sending || !message.trim() ? "not-allowed" : "pointer",
            background: sending || !message.trim() ? "#e5e7eb" : "#16a34a",
            color: sending || !message.trim() ? "#9ca3af" : "#fff",
          }}
        >
          {sending ? "Sending…" : "Send Reply"}
        </button>
        {error && <span style={{ fontSize: 13, color: "#dc2626" }}>{error}</span>}
      </div>
    </form>
  );
}
