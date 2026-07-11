"use client";

import { useState } from "react";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { Avatar } from "../../components/ui/Avatar";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import { StatusPill } from "../../components/ui/StatusPill";
import { useToast } from "../../components/ui/ToastProvider";
import { IconBell, IconInbox, IconUser } from "@tabler/icons-react";

export default function DesignPreviewPage() {
  const { addToast } = useToast();
  const [inputValue, setInputValue] = useState("");

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-12">
      <h1 className="text-2xl font-bold">Design System Preview</h1>

      {/* Button variants */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Button</h2>
        <div className="flex flex-wrap gap-3 items-center">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="primary" disabled>Disabled</Button>
        </div>
        <div className="flex flex-wrap gap-3 items-center">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>
      </section>

      {/* Input variants */}
      <section className="space-y-4 max-w-sm">
        <h2 className="text-lg font-semibold">Input</h2>
        <Input placeholder="Default input" value={inputValue} onChange={(e) => setInputValue(e.target.value)} />
        <Input placeholder="With error" error="This field is required" />
        <Input placeholder="Disabled" disabled />
      </section>

      {/* Badge variants */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Badge</h2>
        <div className="flex flex-wrap gap-3 items-center">
          <Badge variant="default">Default</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="danger">Danger</Badge>
          <Badge variant="info">Info</Badge>
        </div>
      </section>

      {/* Avatar variants */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Avatar</h2>
        <div className="flex flex-wrap gap-4 items-center">
          <Avatar name="John Doe" size="sm" />
          <Avatar name="Jane Smith" size="md" />
          <Avatar name="Alice Johnson" size="lg" />
          <Avatar src="" name="With Fallback" size="md" />
        </div>
      </section>

      {/* Card variants */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Card</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card padding="sm">Small padding</Card>
          <Card padding="md">Medium padding (default)</Card>
          <Card padding="lg">Large padding</Card>
        </div>
      </section>

      {/* EmptyState variants */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Empty state</h2>
        <Card padding="lg">
          <EmptyState
            icon={<IconInbox size={40} />}
            title="No messages yet"
            description="Send a message to start a conversation."
          />
        </Card>
        <Card padding="lg">
          <EmptyState
            icon={<IconBell size={40} />}
            title="All caught up"
            description="You have no pending notifications."
            action={<Button variant="primary">Browse tickets</Button>}
          />
        </Card>
      </section>

      {/* Skeleton variants */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Skeleton</h2>
        <div className="space-y-3 max-w-md">
          <Skeleton variant="text" />
          <Skeleton variant="text" width="75%" />
          <Skeleton variant="text" width="50%" />
          <div className="flex items-center gap-3">
            <Skeleton variant="circular" width={40} height={40} />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" />
              <Skeleton variant="text" width="60%" />
            </div>
          </div>
          <Skeleton variant="rectangular" width="100%" height={120} />
        </div>
      </section>

      {/* StatusPill variants */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Status pill</h2>
        <div className="flex flex-wrap gap-3 items-center">
          <StatusPill status="open" />
          <StatusPill status="pending" />
          <StatusPill status="resolved" />
          <StatusPill status="escalated" />
          <StatusPill status="closed" />
        </div>
      </section>

      {/* Toast */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Toast</h2>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" onClick={() => addToast("Ticket created successfully", "success")}>
            Success toast
          </Button>
          <Button variant="danger" onClick={() => addToast("Something went wrong", "error")}>
            Error toast
          </Button>
          <Button variant="secondary" onClick={() => addToast("This is a warning", "warning")}>
            Warning toast
          </Button>
          <Button variant="ghost" onClick={() => addToast("For your information", "info")}>
            Info toast
          </Button>
        </div>
      </section>
    </div>
  );
}
