# Enterprise-Customer-Support-AI-Agent

A multi-agent, RAG-grounded AI customer support system with a deterministic escalation pipeline. Built as a scaled-down, solo-developer implementation of an enterprise AI support agent blueprint — same architectural principles, minimal infrastructure.

> LangGraph orchestration with specialist routing, Supabase as the system of record, Qdrant for retrieval, and confidence-based human handoff for anything the model shouldn't answer alone.

---

## Table of Contents

- [Enterprise-Customer-Support-AI-Agent](#enterprise-customer-support-ai-agent)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Core Features](#core-features)
  - [Tech Stack](#tech-stack)
  - [Architecture](#architecture)
    - [High-level components](#high-level-components)
    - [Request lifecycle](#request-lifecycle)
    - [SupportState fields](#supportstate-fields)
    - [Node-by-node responsibility](#node-by-node-responsibility)
    - [Multi-agent design](#multi-agent-design)
  - [Folder Structure](#folder-structure)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Setup](#setup)
  - [Development Workflow](#development-workflow)
  - [Phased Build Plan](#phased-build-plan)
  - [Deployment](#deployment)
  - [Testing](#testing)
  - [Design Decisions](#design-decisions)
  - [Metrics](#metrics)
  - [Deliverables Checklist](#deliverables-checklist)

---

## Overview

Enterprise-Customer-Support-AI-Agent handles customer support conversations end-to-end: it classifies intent, retrieves grounded context from a knowledge base, routes the query to the right specialist agent, drafts a response, verifies that response is actually grounded in real data, and — critically — **escalates to a human instead of guessing** whenever confidence or grounding falls short.

The core design principle carried over from the enterprise version: **the LLM never makes an irreversible decision alone.** Low-confidence or ungrounded answers are structurally blocked from reaching the customer, not just discouraged via prompting.

## Core Features

1. **Grounded chat support agent** — Replies are backed by Qdrant-retrieved context, not general-knowledge guesses.
2. **Multi-agent routing** — A Supervisor node classifies intent and hands off to a Billing, Order, or General specialist agent, all sharing one prompt skeleton.
3. **Confidence-based escalation** — Low-confidence or ungrounded answers are held back and routed to a human review queue instead of being sent as-is.
4. **Agent review dashboard** — Humans see escalated tickets with full context (what the AI saw, why it escalated) and reply manually.

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| API | FastAPI |
| Orchestration | LangGraph — multi-agent (Supervisor + Billing/Order/General specialists) |
| System of record | PostgreSQL via Supabase |
| Knowledge store | Qdrant (Qdrant Cloud free tier) |
| DB access | Repository pattern, raw SQL (`psycopg`), no ORM |
| Background jobs | None |
| Observability | LangSmith (free tier) |
| Auth | JWT, 2 roles (`customer`, `agent`) |
| Local dev | Docker Compose (`api`, `frontend`; Supabase & Qdrant are hosted) |
| Production hosting | Railway |
| LLM Provider | Anthropic API (`claude-sonnet-5`), swappable via one abstraction module |
| Linting/formatting | None |

**Assumptions:**
- Basic Python and JS/TS knowledge assumed; no prior LangGraph/RAG experience required.
- Single low-cost hosting budget (~$0–10/month).
- No real customer or payment data — everything is seeded/mock data, clearly labeled as a demo.
- Effort is sequential: data and business logic are built before AI, deterministic behavior before generative behavior.

## Architecture

### High-level components

```
 Customer / Agent (browser)
        │
        ▼
 Next.js + Tailwind frontend
        │  REST, JWT in Authorization header
        ▼
 FastAPI (API layer)
        │
        ▼
 LangGraph (orchestration)
   Supervisor ──► Billing / Order / General agent ──► LLM Provider
        │
    ┌───┴────────────┐
    ▼                ▼
 Service Layer    RAG Layer
 (Ticket,         (chunk, embed,
  Knowledge,       retrieve)
  Escalation)
    │                │
    ▼                ▼
 Repository Layer   Qdrant
    │
    ▼
 Supabase Postgres
```

### Request lifecycle

1. Frontend sends `POST /chat/messages` with a JWT, `ticket_id` (or none), and message text.
2. FastAPI verifies the JWT/role and persists the inbound message.
3. FastAPI invokes the LangGraph with an initial `SupportState`.
4. The graph runs: **classify → context → retrieve → business_data → route (Supervisor) → generate (specialist) → verify → decide**.
5. If confidence and grounding both check out → the final answer is returned.
6. Otherwise → the ticket is escalated, the customer gets an acknowledgment, and the full state (draft answer, retrieved docs, routing reason, escalation reason) is stored for human review.
7. FastAPI persists the outcome and returns the response.

### SupportState fields

`ticket_id`, `customer_message`, `conversation_history`, `category`, `intent_confidence`, `retrieved_docs`, `business_data`, `active_agent`, `routing_reason`, `draft_response`, `grounding_ok`, `confidence`, `escalate`, `escalation_reason`, `final_response`

### Node-by-node responsibility

| Node | Does | Calls |
|---|---|---|
| 1. Classify | Categorizes the message (billing / order / general) | `LLMClient.classify` |
| 2. Context | Loads customer profile + recent conversation history | `TicketService` |
| 3. Retrieve | Embeds the query, searches Qdrant, assembles cited context | `KnowledgeService.search` |
| 4. Business data | Fetches order/payment data if the category needs it | Direct DB lookup via services |
| 5. Route | Supervisor picks the Billing / Order / General agent | `LLMClient.generate` (narrow routing prompt) |
| 6. Generate | Selected specialist drafts a response grounded in retrieved context + business data | `LLMClient.generate` |
| 7. Verify | A separate LLM call checks every factual claim traces back to retrieved context or business data | `LLMClient.generate` |
| 8. Decide | Combines grounding + confidence; escalates if either fails threshold | `EscalationService.evaluate` |

**Structural guarantee:** when `escalate == true`, the final response is always an acknowledgment — never `draft_response` — even if the draft looked correct. This is enforced in Node 8's output assembly, not by a prompt instruction, so it can't be talked around by the model.

### Multi-agent design

- **Supervisor** — routing-only responsibility. Receives the category plus a one-line summary of retrieved context and outputs which specialist should answer. Kept deliberately narrow so it stays a clean classification task.
- **Specialists (Billing, Order, General)** — share one prompt skeleton, differing only in role description and which business-data fields are relevant. Adding a fourth specialist later means one new file, not edits to the others.

## Folder Structure

```
Enterprise-Customer-Support-AI-Agent/
  app/
    api/
      routes/
        chat.py            # POST /chat/messages — the graph entry point
        tickets.py         # GET/POST tickets, PATCH status
        escalations.py     # GET queue, claim, resolve, context
        auth.py            # register/login/refresh
      schemas.py            # all Pydantic In/Out models, one file
      auth.py               # JWT encode/decode, get_current_user, require_role
      deps.py               # DB connection + service constructors for FastAPI Depends()

    graph/
      state.py              # SupportState TypedDict
      workflow.py           # node graph + edges
      nodes/
        classify.py         # Node 1 — intent classification
        context.py          # Node 2 — customer profile + conversation history
        retrieve.py         # Node 3 — Qdrant RAG retrieval
        business_data.py    # Node 4 — pulls order/payment data when relevant
        route.py            # Node 5 — Supervisor: picks a specialist agent
        generate.py         # Node 6 — specialist agent generates draft_response
        verify.py           # Node 7 — grounding check on the draft
        decide.py           # Node 8 — confidence scoring + escalation decision
      agents/
        supervisor_prompt.py    # narrow routing-only prompt
        specialist_skeleton.py  # shared prompt shell (role, account data, reference material)
        billing_agent.py        # role description + billing-specific fields
        order_agent.py
        general_agent.py

    services/
      ticket_service.py       # create_ticket, transition_status (state machine), set_priority
      knowledge_service.py    # search() — embeds query, retrieves + assembles context
      escalation_service.py   # evaluate(), enqueue(), claim(), resolve()

    repositories/
      ticket_repository.py       # create, get_by_id, list_by_customer, update_status
      conversation_repository.py # append_message, list_by_ticket
      escalation_repository.py   # create, list_queued, update_status, assign_reviewer

    rag/
      ingest.py             # chunk + embed + upsert to Qdrant, idempotent by point ID
      retriever.py          # embeds query, filtered Qdrant search, dedupe/re-rank

    llm/
      provider.py           # single LLMClient wrapper: generate(), classify()

    db/
      session.py            # Supabase Postgres connection
      migrations/
        0001_init.sql          # customers, tickets, conversations
        0002_escalations.sql   # escalations table
        0003_auth.sql          # password_hash, role on customers

    config.py               # all environment-driven settings in one file
    main.py                 # FastAPI app entrypoint

  docs/                     # seed knowledge docs (faq.md, refund_policy.md, ...)

  frontend/
    app/
      chat/                 # customer chat UI
      agent/                # escalation queue + review
    components/

  tests/
    unit/                   # services (mocked repos), graph nodes (mocked services)
    integration/            # API + full graph run against a test DB

  scripts/
    seed_db.py              # sample customers/tickets for local dev
    run_ingestion.py         # ingests docs/ into Qdrant

  docker-compose.yml
  requirements.txt
  .env.example
  README.md
```

**Why this shape:**
- `graph/nodes/` is graph plumbing (state in, state out); `graph/agents/` is prompt content. Keeping them separate means editing a specialist's tone never touches graph wiring, and vice versa.
- One `schemas.py` and one `config.py` instead of per-domain files — at this project's size, splitting them adds navigation overhead without payoff.
- `db/migrations/` is deliberately three files — each maps to a build phase, and no table is created before the phase that needs it.

## Getting Started

### Prerequisites

- Docker & Docker Compose
- A [Supabase](https://supabase.com) project (PostgreSQL)
- A [Qdrant Cloud](https://cloud.qdrant.io) free-tier cluster
- An [Anthropic API key](https://console.anthropic.com)

### Setup

```bash
git clone <your-repo-url>
cd Enterprise_Customer_Support_AI_Agent
cp .env.example .env
```

Fill in `.env` with:

```
ANTHROPIC_API_KEY=
DATABASE_URL=
QDRANT_URL=
QDRANT_API_KEY=
JWT_SECRET=
```

Run migrations, then start the stack:

```bash
docker-compose up --build
```

Seed demo data and load the knowledge base:

```bash
python scripts/seed_db.py
python scripts/run_ingestion.py
```

The frontend will be available at `http://localhost:3000` and the API at `http://localhost:8000`.

## Development Workflow

- **Branching:** trunk-based, short-lived feature branches (e.g. `feat/rag-ingestion`, `feat/multi-agent-routing`), merged via PR even solo.
- **Commits:** conventional commits (`feat:`, `fix:`, `refactor:`).
- **CI:** one GitHub Actions job — run `pytest` against a throwaway Postgres service container, then build the Docker image on merge to `main`. No lint/format step.
- **Config:** all secrets live in `.env`, never committed; `.env.example` documents every required variable.

## Phased Build Plan

Each phase produces a runnable, demoable system rather than a half-built layer. Data and business rules come before AI; a single generic agent proves the graph before multi-agent routing is layered on top.

| Phase | Goal | Key deliverables |
|---|---|---|
| **1 — Foundation** | Working ticketing system, zero AI | Supabase schema (`0001_init.sql`), `TicketRepository`, `ConversationRepository`, `TicketService` with a status state machine (`open → pending → resolved/escalated → closed`), FastAPI CRUD for tickets/messages, JWT auth |
| **2 — Knowledge base** | Grounded, cited context — no LLM yet | Seed docs (`faq.md`, `refund_policy.md`, `billing_policy.md`), `rag/ingest.py`, `rag/retriever.py`, `knowledge_service.search()` |
| **3 — Single-agent graph** | One message flows through the full pipeline | `SupportState`, Nodes 1–3 + 6–8 with one generic agent, `POST /chat/messages` wired to the graph, LangSmith tracing on from the start |
| **4 — Multi-agent routing** | Category-specific answers with the right tone/data | Node 4 (business data) + Node 5 (Supervisor), Billing/Order/General specialist prompts, `agents_invoked` visible per chat turn |
| **5 — Escalation loop** | Low-confidence answers caught and handed to a human | `0002_escalations.sql`, `EscalationService`, escalation queue + review API, agent dashboard UI |

**Sequencing principle:** deterministic before AI, single agent before multi-agent. Phase 3 uses one generic agent so graph-wiring bugs are debugged separately from routing-logic bugs; Phase 4 only adds the routing split once the graph is proven to work.

## Deployment

**Local dev**
- `docker-compose.yml` runs `api` and `frontend`; Supabase and Qdrant Cloud are hosted, so `.env` just points at their connection strings.
- `scripts/seed_db.py` seeds demo data; `scripts/run_ingestion.py` embeds `docs/` into Qdrant.

**Production build**
- `docker build` produces one image for `api` and one for `frontend`.
- Migrations run against Supabase before the new container receives traffic.

**Hosting**
- **Database:** Supabase
- **Knowledge store:** Qdrant Cloud
- **API + frontend:** Railway, Docker deploy, redeploys on push to `main`
- **CI/CD:** GitHub Actions runs tests; Railway handles deploys via its GitHub integration. Single environment — no staging tier.

## Testing

Testing mirrors the architectural layering:

- **Repositories** — tests against a real test database, each wrapped in a transaction that's rolled back after.
- **Services** — unit tests with mocked repositories (fast, no DB needed); the ticket status state machine gets a parametrized test covering every (current, new) status pair.
- **Graph nodes and agents** — unit tests with mocked services, verifying node logic without hitting the LLM.
- **End-to-end** — one or two tests running the full graph against a test DB with a fixed/mocked LLM response.

## Design Decisions

- **The LLM never makes an irreversible decision alone.** Low-confidence or ungrounded answers are structurally blocked from reaching the customer — enforced in code, not prompting.
- **Routing is handled by a narrow Supervisor** rather than one sprawling prompt, keeping classification and generation concerns separate.
- **Single agent before multi-agent, deterministic before AI** — each phase is fully demoable on its own, isolating bugs to the layer that introduced them.

## Metrics

Suggested metrics to track and report:

- Escalation rate (% of queries routed to human review)
- Routing accuracy (did the Supervisor send each test query to the right specialist)
- Retrieval precision on a small hand-labeled Q&A test set
- Token/cost per resolved ticket

## Deliverables Checklist

- [ ] Public GitHub repo with a clean README (architecture diagram, setup steps, demo GIF)
- [ ] Working deployed demo link on Railway
- [ ] Seed data + sample knowledge docs so reviewers can run it immediately
- [ ] Test suite passing in CI (badge in README)
- [ ] Short "Design Decisions" write-up explaining the *why*
- [ ] LangSmith trace screenshot showing a multi-agent graph execution
- [ ] Escalation dashboard screenshot showing a low-confidence case caught and routed

---

**Tech stack summary:** FastAPI · LangGraph (multi-agent) · Supabase (PostgreSQL) · Qdrant · Next.js · Tailwind CSS · Anthropic API · Docker · Railway
