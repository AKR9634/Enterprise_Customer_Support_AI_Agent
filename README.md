<div align="center">

# 🤖 Enterprise Customer Support AI Agent

### A production-style, multi-agent RAG system that knows when *not* to answer

**LangGraph orchestration · Confidence-gated escalation · Full-stack, fully tested**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/langgraph)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Postgres](https://img.shields.io/badge/Postgres-Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC244C?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

[![Tests](https://img.shields.io/badge/tests-64%20files%20%7C%208.6k%20LOC-brightgreen?style=flat-square)](#-testing)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](#-license)
[![Status](https://img.shields.io/badge/status-active%20development-yellow?style=flat-square)]()

<br/>

**[🌐 Project Website](https://powerful-clarity-production-30db.up.railway.app/auth/login) · [📐 Architecture](#-architecture) · [🚀 Quickstart](#-quickstart) · [🧠 Design Decisions](#-design-decisions)**

</div>

---

## 💡 The Problem This Solves

Most "AI support agent" side projects wire a chatbot to an LLM and call it done. That works great in a demo — right up until the model confidently hallucinates a refund policy that doesn't exist, and now it's a support ticket for the CEO.

This project is built around one non-negotiable rule:

> **The LLM never makes an irreversible decision alone.**

Every response passes through a **grounding check** and a **confidence gate** before it ever reaches a customer. If either fails, the system doesn't let the model "try its best" — it structurally routes the conversation to a human, full context attached. This is enforced in code at the graph level, not requested via a prompt that a jailbreak or a weird edge case could talk the model out of.

---

## ✨ Core Features

| | |
|---|---|
| 🎯 **Grounded answers, not guesses** | Every reply is backed by context retrieved from Qdrant — the agent cites what it read, it doesn't freelance |
| 🧩 **Multi-agent specialist routing** | A Supervisor node classifies intent and hands off to Billing, Order, Account, Product, or General agents — each with focused context, not one bloated prompt |
| 🛑 **Confidence-gated escalation** | Low-confidence or ungrounded drafts are structurally blocked from reaching the customer and routed to a human review queue instead |
| 🕵️ **Full escalation transparency** | Human agents see exactly what the AI saw, what it drafted, and *why* it escalated — not just a raw transcript |
| 🔐 **Real auth, real roles** | JWT-based auth with `customer` / `agent` roles gating every route |
| 🧪 **Tested like production code** | 64 Python modules backed by 33 test files (~4.6k lines) spanning unit, service, and full-graph integration tests |

---

## 🏗️ Architecture

### System overview

```
┌──────────────────────┐
│  Customer / Agent UI  │   Next.js 14 (App Router) + Tailwind
└──────────┬────────────┘
           │  REST · JWT in Authorization header
           ▼
┌──────────────────────┐
│      FastAPI          │   Routes → Auth → Services
└──────────┬────────────┘
           ▼
┌────────────────────────────────────────────────────┐
│                LangGraph Orchestration               │
│                                                        │
│  classify → context → retrieve → business_data        │
│      → route (Supervisor) → generate (specialist)     │
│      → verify → decide                                │
└───────┬───────────────────────────┬──────────────────┘
        ▼                           ▼
┌───────────────┐           ┌───────────────┐
│ Service Layer  │           │   RAG Layer    │
│ Ticket ·       │           │ embed · chunk  │
│ Knowledge ·    │           │ retrieve       │
│ Escalation     │           └───────┬───────┘
└───────┬───────┘                   ▼
        ▼                     ┌───────────┐
┌───────────────┐             │  Qdrant    │
│ Repository     │             └───────────┘
│ Layer          │
└───────┬───────┘
        ▼
┌───────────────┐
│  Supabase       │
│  Postgres       │
└───────────────┘
```

### The 8-node request lifecycle

Every chat message runs through a deterministic, inspectable pipeline — no black box:

| # | Node | Responsibility |
|---|------|-----------------|
| 1 | **Classify** | Categorizes the message: billing / order / account / product / general |
| 2 | **Context** | Loads customer profile and recent conversation history |
| 3 | **Retrieve** | Embeds the query, searches Qdrant, assembles cited context |
| 4 | **Business Data** | Pulls live order/payment/product data when the category needs it |
| 5 | **Route** (Supervisor) | Picks the specialist agent best suited to answer |
| 6 | **Generate** | The selected specialist drafts a response grounded in retrieved context + business data |
| 7 | **Verify** | A separate LLM call fact-checks every claim in the draft against real retrieved data |
| 8 | **Decide** | Combines grounding + confidence → answer the customer, or escalate to a human |

> **Structural guarantee:** when `escalate == true`, the response returned is *always* the acknowledgment message — never the drafted answer — even if the draft looked perfectly fine. That branch is enforced in Node 8's output assembly, not by asking the model nicely.

### Multi-agent design

```
                     ┌───────────────┐
   category +  ───▶  │  Supervisor    │  ───▶ picks one specialist
   context summary    │  (routing-only)│
                     └───────────────┘
                             │
        ┌──────────┬─────────┼─────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼
    Billing     Order      Account    Product    General
    Agent       Agent      Agent      Agent      Agent
```

All five specialists share **one prompt skeleton**, differing only in role description and which business-data fields they get. Adding a sixth specialist later means one new file — not edits scattered across the codebase.

---

## 🧰 Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router) · TypeScript · Tailwind CSS |
| **API** | FastAPI · Pydantic v2 |
| **Orchestration** | LangGraph — multi-agent supervisor + specialists |
| **LLM Provider** | Anthropic API (Claude), swappable via a single provider abstraction |
| **System of record** | PostgreSQL via Supabase |
| **Knowledge store** | Qdrant (vector search) |
| **DB access** | Repository pattern, raw SQL via `psycopg` — no ORM |
| **Auth** | JWT · role-based (`customer`, `agent`) |
| **Observability** | LangSmith tracing |
| **Local dev** | Docker Compose |
| **Deployment** | Railway |

</div>

---

## 📂 Project Structure

```
Enterprise-Customer-Support-AI-Agent/
├── app/
│   ├── api/
│   │   ├── routes/          # chat, tickets, escalations, auth, accounts, products
│   │   ├── auth.py          # JWT encode/decode, role guards
│   │   └── schemas.py       # every Pydantic In/Out model
│   ├── graph/
│   │   ├── state.py         # SupportState — the object threaded through every node
│   │   ├── workflow.py      # the 8-node graph definition
│   │   ├── nodes/           # classify · context · retrieve · business_data
│   │   │                    # route · generate · verify · decide
│   │   └── agents/          # Supervisor + 5 specialist prompt modules
│   ├── services/            # Ticket, Escalation, Knowledge, Billing, Order, Account, Product
│   ├── repositories/        # one repo per table — raw SQL, no ORM magic
│   ├── rag/                 # ingest.py (chunk+embed+upsert), retriever.py
│   ├── llm/                 # provider.py — single LLM client abstraction
│   └── db/                  # session + versioned SQL migrations
├── frontend/
│   ├── app/                 # chat/, agent/, auth/ route groups
│   └── components/          # chat bubbles, escalation banners, agent queue, design system
├── docs/                    # seed knowledge base (FAQ, refund/billing/shipping policy)
├── scripts/                 # seed_db · run_ingestion · migrate
└── tests/
    ├── unit/                 # services (mocked repos), graph nodes (mocked services)
    └── integration/          # real DB + full-graph execution
```

**Why this shape:** `graph/nodes/` is pure plumbing (state in, state out); `graph/agents/` is prompt content. Editing a specialist's tone never touches graph wiring, and vice versa.

---

## 🚀 Quickstart

### Prerequisites

- Docker & Docker Compose
- A [Supabase](https://supabase.com) project (PostgreSQL)
- A [Qdrant Cloud](https://cloud.qdrant.io) cluster
- An [Anthropic API key](https://console.anthropic.com)

### Setup

```bash
# 1. Clone
git clone https://github.com/<your-username>/Enterprise_Customer_Support_AI_Agent.git
cd Enterprise_Customer_Support_AI_Agent

# 2. Configure environment
cp .env.example .env
```

Fill in `.env`:

```env
ANTHROPIC_API_KEY=
DATABASE_URL=
QDRANT_URL=
QDRANT_API_KEY=
JWT_SECRET=
```

```bash
# 3. Run migrations & start the stack
docker-compose up --build

# 4. Seed demo data + load the knowledge base
python scripts/seed_db.py
python scripts/run_ingestion.py
```

| Service | URL |
|---|---|
| 💬 Customer chat UI | http://localhost:3000 |
| 🖥️ API | http://localhost:8000 |
| 📖 API docs (Swagger) | http://localhost:8000/docs |

---

## 🧪 Testing

Testing mirrors the architecture, layer by layer:

```bash
pytest                       # full suite
pytest tests/unit            # services + graph nodes, fully mocked, fast
pytest tests/integration     # real test DB, full graph execution
```

- **Repositories** — run against a real test database, wrapped in a transaction and rolled back after each test
- **Services** — unit-tested against mocked repositories; the ticket status state machine is parametrized across every valid `(current, new)` status pair
- **Graph nodes & agents** — unit-tested with mocked services, no live LLM calls
- **End-to-end** — full graph execution against a test DB with a fixed/mocked LLM response

**33 test files · ~4,600 lines of tests** across unit and integration layers.

---

## 🧠 Design Decisions

- **The LLM never makes an irreversible decision alone.** Low-confidence or ungrounded answers are structurally blocked from reaching the customer — enforced in code, not prompting.
- **Routing is a narrow, single-purpose Supervisor**, not one sprawling do-everything prompt. Classification and generation are kept as separate concerns.
- **Single generic agent before multi-agent, deterministic logic before generative logic.** The graph was proven end-to-end with one agent before specialist routing was layered on top — isolating "is the graph wired correctly" bugs from "is the routing logic correct" bugs.
- **No ORM.** A thin repository layer over raw SQL keeps query behavior explicit and easy to reason about at this scale.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built as a scaled-down, solo-developer implementation of an enterprise AI support blueprint** — same architectural principles that guard production systems, minimal infrastructure.

⭐ If this project is useful or interesting, consider starring it.

</div>