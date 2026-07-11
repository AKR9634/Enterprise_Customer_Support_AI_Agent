"use client";

import { useState, type FormEvent } from "react";
import { Button } from "./ui/Button";

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
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your reply…"
        rows={4}
        disabled={sending}
        className="w-full px-3.5 py-2.5 text-sm border border-support-border-strong rounded-md outline-none transition-colors placeholder:text-support-text-faint focus:border-support-primary resize-vertical font-sans box-border disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <div className="flex items-center gap-3">
        <Button
          type="submit"
          variant="primary"
          size="md"
          disabled={sending || !message.trim()}
        >
          {sending ? "Sending…" : "Send Reply"}
        </Button>
        {error && <span className="text-xs text-support-danger">{error}</span>}
      </div>
    </form>
  );
}
