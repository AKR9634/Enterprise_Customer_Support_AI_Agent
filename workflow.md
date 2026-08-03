# Deployment Workflow — Docker Hub → EC2

Complete, field-tested runbook for deploying the Enterprise Customer Support AI Agent
(FastAPI backend + Next.js frontend) to a single AWS EC2 instance using images
pushed to Docker Hub. Covers the actual steps, the three gotchas hit during the
first deploy (image size, Supabase IPv6, retrieval threshold), and every env var.

---

## Overview

```
Build (local) ──push──► Docker Hub ◄──pull── EC2 (Docker Compose)
```

- Backend image: `akr6723/support-ai-api`
- Frontend image: `akr6723/support-ai-frontend`
- Deployed: `http://54.210.50.10:3000` (UI) · `http://54.210.50.10:8000` (API/Swagger)

### Key architecture facts that shape the deploy

| Fact | Where | Consequence |
|---|---|---|
| Frontend server rewrites use `BACKEND_API_URL` | `frontend/next.config.mjs` | Server→API traffic stays inside the Docker network (`http://api:8000`) |
| Browser auth calls use `NEXT_PUBLIC_BACKEND_API_URL` | `frontend/components/AuthContext.tsx` | **Inlined at build time** — the EC2 public IP/domain must be known before `docker build` |
| `/auth/*` is NOT in the rewrites | `frontend/next.config.mjs` | Browser hits the API directly → CORS required |
| CORS origins are env-driven | `app/main.py` | Set `CORS_ALLOWED_ORIGINS` in prod `.env` |
| Embedding model downloads at startup | `app/main.py` (warmup) | EC2 needs outbound internet + enough RAM (`t3.small` min) |
| Supabase direct connection is IPv6-only | DNS of `db.<ref>.supabase.co` | EC2 + Docker must have IPv6 enabled |

---

## 0. Prerequisites

- Docker Desktop (engine running) + logged into Docker Hub (`docker login`, use an
  **access token**, not your password)
- Docker Hub namespace (used as `<DOCKERHUB_USER>` below)
- AWS account, key pair `.pem`, EC2 access
- Existing Supabase (Postgres), Qdrant Cloud, OpenRouter, HuggingFace, LangSmith
  credentials (in your local `.env`)

> **Security:** `.env` and `.env.prod` are gitignored and excluded from image builds
> (`.dockerignore`). Secrets never enter the images or git. Never commit `.env*`
> and never build with `--env-file`.

---

## 1. Provision EC2 (AWS Console, us-east-1)

1. **EC2 → Instances → Launch instance**
   - Name: `support-ai-prod`
   - AMI: **Ubuntu 22.04 LTS (HVM)** (64-bit x86)
   - Instance type: `t3.small` (or `t3.medium`)
   - Key pair: `RSA` / `.pem`, save the downloaded file
   - Security group `support-ai-sg` inbound rules:

     | Type | Protocol | Port | Source |
     |---|---|---|---|
     | SSH | TCP | 22 | your IP (or 0.0.0.0/0) |
     | Custom TCP | TCP | 3000 | 0.0.0.0/0 |
     | Custom TCP | TCP | 8000 | 0.0.0.0/0 |

   - Storage: **20 GiB** gp3
   - Launch, wait for **2/2 status checks**

2. **Attach an Elastic IP** (Elastic IPs → Allocate → Associate to the instance).
   Write down the public IPv4 — it is baked into the frontend image.

### 1b. Enable IPv6 (required — see "Gotcha 2" below)

Supabase's direct-connection hostname resolves to IPv6 only, so the EC2 must have
IPv6. Do these in the console:

1. **VPC → Your VPCs** → select your VPC → Actions → Edit CIDRs →
   **Add IPv6 CIDR block** (Amazon-provided) → Save.
2. **VPC → Subnets** → select your subnet → Actions → Edit IPv6 CIDRs →
   **Add IPv6 CIDR** (the `/64`) → Save. Then Actions → Edit subnet settings →
   check **Enable auto-assign IPv6 address** → Save.
3. **VPC → Route Tables** → the route table of your subnet → Actions → Edit routes →
   add `::/0` → target the **Internet Gateway** → Save.
4. **EC2 → Instances** → select the instance → Actions → Networking →
   Manage IP addresses → **Assign new IPv6 address** → Save.

Verify from the instance:

```bash
ip -6 addr show scope global        # expect a 2600:... global address
curl -6 -s -o /dev/null -w "%{http_code}\n" https://www.google.com   # expect 200
```

---

## 2. Build & push images (on your machine)

### 2.1 Backend

```bash
docker build -t <DOCKERHUB_USER>/support-ai-api:1.0.0 -t <DOCKERHUB_USER>/support-ai-api:latest .
docker push <DOCKERHUB_USER>/support-ai-api:1.0.0
docker push <DOCKERHUB_USER>/support-ai-api:latest
```

No build args. Copies `app/`, `docs/`, `scripts/`, runs `uvicorn` on port 8000.

> **Gotcha 1 — image size:** `sentence-transformers` → `torch>=1.11.0` resolves to a
> CUDA build that pulls ~6 GB of NVIDIA packages. The Dockerfile now installs
> **CPU-only torch first**:
>
> ```dockerfile
> RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
> RUN pip install --no-cache-dir -r requirements.txt
> ```
>
> This drops the image from **9.18 GB → 2.64 GB**.

### 2.2 Frontend — build args are mandatory

```bash
docker build \
  --build-arg BACKEND_API_URL=http://api:8000 \
  --build-arg NEXT_PUBLIC_BACKEND_API_URL=http://<EC2-IP>:8000 \
  -t <DOCKERHUB_USER>/support-ai-frontend:1.0.0 \
  -t <DOCKERHUB_USER>/support-ai-frontend:latest \
  frontend
docker push <DOCKERHUB_USER>/support-ai-frontend:1.0.0
docker push <DOCKERHUB_USER>/support-ai-frontend:latest
```

- `BACKEND_API_URL=http://api:8000` — server-side rewrites; resolves to the API
  service by Docker name inside the compose network (service **must** be named `api`).
- `NEXT_PUBLIC_BACKEND_API_URL=http://<EC2-IP>:8000` — browser auth calls; must be
  publicly reachable. **Changing this later requires rebuilding the frontend image.**

---

## 3. Deploy artifacts

### 3.1 `docker-compose.prod.yml`

```yaml
services:
  api:
    image: <DOCKERHUB_USER>/support-ai-api:1.0.1
    container_name: support-ai-api
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "8000:8000"

  frontend:
    image: <DOCKERHUB_USER>/support-ai-frontend:1.0.0
    container_name: support-ai-frontend
    restart: unless-stopped
    environment:
      BACKEND_API_URL: http://api:8000
    ports:
      - "3000:3000"
    depends_on:
      - api

networks:
  default:
    enable_ipv6: true
```

> **Gotcha 3 — compose network is IPv4-only by default:** the `networks.default.enable_ipv6: true`
> is required for the API container to reach Supabase. Also note that a network
> created before IPv6 was enabled on the daemon stays IPv4-only — recreate with
> `docker compose down` then `up` after enabling Docker IPv6 (section 4).

### 3.2 Prod `.env`

Copy your local `.env` and edit:

- **Add** `CORS_ALLOWED_ORIGINS=http://<EC2-IP>:3000`
- **Rotate** `JWT_SECRET` to a fresh 64-char hex value
- **Remove** `TEST_DATABASE_URL`
- Keep everything else identical: `DATABASE_URL`, `QDRANT_URL`, `QDRANT_API_KEY`,
  `HUGGINGFACEHUB_API_TOKEN`, `OPEN_ROUTER_API_KEY`, `OPENAI_API_KEY`,
  `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_ENDPOINT`,
  `LANGCHAIN_PROJECT`
- Optional runtime tuning (all have sane defaults in `app/config.py`):
  `LLM_MODEL`, `CONFIDENCE_THRESHOLD`, `RETRIEVAL_SCORE_THRESHOLD`, `JWT_EXPIRY_HOURS`

> **Gotcha:** Docker's env-file parser rejects whitespace around `=` (`KEY = value`
> breaks it). Normalize every line to `KEY=value` with no spaces.

### 3.3 All env vars the app reads

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | — | required; Supabase direct IPv6 host |
| `JWT_SECRET` | — | required; rotate for prod |
| `QDRANT_URL` | — | required |
| `QDRANT_API_KEY` | — | required |
| `OPEN_ROUTER_API_KEY` | — | required (LLM via OpenRouter/ChatOpenAI) |
| `CORS_ALLOWED_ORIGINS` | localhost:3000/3001 | comma-separated; set to your UI origin |
| `HUGGINGFACEHUB_API_TOKEN` | — | HF rate limits for embedding model download |
| `OPENAI_API_KEY` | — | present in `.env`; not consumed by app code |
| `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` / `LANGCHAIN_ENDPOINT` / `LANGCHAIN_PROJECT` | — | LangSmith tracing |
| `TEST_DATABASE_URL` | — | not needed in prod |
| `JWT_ALGORITHM` | HS256 | |
| `JWT_EXPIRY_HOURS` | 24 | |
| `QDRANT_COLLECTION` | knowledge_base | |
| `EMBEDDING_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 500 / 50 | |
| `LLM_MODEL` | gpt-4o-mini | |
| `OPEN_ROUTER_BASE_URL` | https://openrouter.ai/api/v1 | |
| `LLM_TEMPERATURE` / `LLM_MAX_TOKENS` | 0.0 / 1024 | |
| `CONFIDENCE_THRESHOLD` | 0.7 | graph confidence gate |
| `RETRIEVAL_SCORE_THRESHOLD` | 0.40 | retrieval gate (see Gotcha 4) |
| `ESCALATION_ACKNOWLEDGMENT` | default ack text | |
| `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` | false / "" / default | LangSmith |

---

## 4. Install Docker on EC2

```bash
# run as ubuntu
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu
```

### Enable IPv6 on the Docker daemon (required — see Gotcha 3)

```bash
echo '{"ipv6": true, "fixed-cidr-v6": "fd00:1:1:1::/64"}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

Docker ≥ 25 does NAT66 automatically, so containers can reach the IPv6-only
Supabase host.

---

## 5. Copy artifacts & deploy

```bash
sudo mkdir -p /opt/support-ai && sudo chown ubuntu:ubuntu /opt/support-ai

# from your machine
scp docker-compose.prod.yml ubuntu@<EC2-IP>:/opt/support-ai/
scp .env.prod             ubuntu@<EC2-IP>:/opt/support-ai/.env    # name it .env on EC2

# on EC2
cd /opt/support-ai
docker compose -f docker-compose.prod.yml up -d

docker compose -f docker-compose.prod.yml ps
docker logs support-ai-api --tail 100
```

First API boot downloads the embedding model (~90 MB) — expect 30–90 s before it
responds. Images are public, so no `docker login` on the EC2 is needed to pull.

---

## 6. One-time data setup (against prod DB/Qdrant)

```bash
cd /opt/support-ai

# migrations (idempotent; tracks applied files in schema_migrations)
docker run --rm --env-file .env <DOCKERHUB_USER>/support-ai-api:1.0.1 python scripts/migrate.py

# seed demo customers/orders/products (also runs migrate internally)
docker run --rm --env-file .env <DOCKERHUB_USER>/support-ai-api:1.0.1 python scripts/seed_db.py

# load docs/ into Qdrant (chunk + embed + upsert)
docker run --rm --env-file .env <DOCKERHUB_USER>/support-ai-api:1.0.1 python scripts/run_ingestion.py
```

---

## 7. Verification / smoke tests

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://<EC2-IP>:3000/chat   # 200
curl -s -o /dev/null -w "%{http_code}\n" http://<EC2-IP>:8000/docs   # 200
```

**CORS check** (must echo the origin back):

```bash
curl -s -o /dev/null -D - -H "Origin: http://<EC2-IP>:3000" http://<EC2-IP>:8000/auth/me
# expect: HTTP/1.1 401  +  access-control-allow-origin: http://<EC2-IP>:3000
```

**Full pipeline** (register → login → chat):

```bash
curl -s -X POST http://<EC2-IP>:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"smoke@example.com","full_name":"Smoke","password":"Test12345!"}'
# -> { "access_token": "..." }

curl -s -X POST http://<EC2-IP>:8000/auth/login -H "Content-Type: application/json" \
  -d '{"email":"smoke@example.com","password":"Test12345!"}'
# -> token

curl -s -X POST http://<EC2-IP>:8000/chat/messages \
  -H "Content-Type: application/json" -H "Authorization: Bearer <TOKEN>" \
  -d '{"message":"What is the return policy for a defective Widget Pro?"}'
# -> { "response": "...", "escalated": false, ... }
```

Also test through the frontend origin (port 3000) so the Next.js rewrite path is
covered. In the browser: `http://<EC2-IP>:3000/chat` → login → send a message;
check LangSmith for a trace.

---

## 8. Gotchas encountered on first deploy (read these)

1. **Image bloat (9.18 GB → 2.64 GB).** `pip install torch --index-url .../whl/cpu`
   must run *before* `requirements.txt` so the resolver doesn't pull the CUDA runtime.

2. **Supabase direct connection is IPv6-only.** `db.<ref>.supabase.co` has only an
   AAAA record. Enable IPv6 on VPC → subnet → instance route (section 1b) and on the
   Docker daemon. Alternative: use the IPv4 **pooler** hostname — that changes the
   connection mode and deviates from the project's "direct connection" rule.

3. **Compose networks are IPv4-only.** Add `networks.default.enable_ipv6: true`.
   If the network was created before IPv6 was on the daemon, run
   `docker compose down` then `up` to recreate it.

4. **Retrieval threshold was too strict.** `app/rag/retriever.py` had a hardcoded
   `score_threshold=0.55`, but all-MiniLM-L6-v2 scores for relevant chunks are
   ~0.45–0.55, so every query was filtered out and everything escalated. Moved to
   `RETRIEVAL_SCORE_THRESHOLD` (default **0.40**) in `app/config.py`. Tune per
   knowledge base.

5. **Docker `--env-file` rejects whitespace around `=`.** Normalize `.env` lines.

6. **PowerShell/Windows:** passing JSON to `curl.exe` via `-d '{"a":1}'` mangles
   escaping. Use `-d "@file.json"` instead.

---

## 9. Upgrading / rollback

**Upgrade:** bump the version → build → push → on EC2 edit `image:` tag →
```bash
cd /opt/support-ai
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

**Rollback:** edit `docker-compose.prod.yml` back to a previous tag, then
`docker compose -f docker-compose.prod.yml up -d`. Keep old tags on Docker Hub.

---

## 10. Security & operations checklist

- [ ] `.env*` gitignored and never committed; secrets only live on the EC2 and in
      Docker Hub (via image runtime env, not inside images)
- [ ] Rotate the EC2 key pair if the `.pem` was ever shared (it was, in this session)
- [ ] Rotate `JWT_SECRET`, and any API keys that may have leaked
- [ ] Security group: open only 22/3000/8000 (or switch to a reverse proxy)
- [ ] Recommended next step: **Caddy/nginx reverse proxy** on 80/443 with a domain —
      removes the open `8000` port and CORS. Requires one frontend rebuild with the
      new `NEXT_PUBLIC_BACKEND_API_URL`
- [ ] Backups: state lives in Supabase (PITR) and Qdrant (snapshots); the EC2 itself
      is stateless and rebuildable from the two images + `.env`
