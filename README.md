# PromoPulse API – Promotion & Engagement Platform (Python + FastAPI)

PromoPulse is a backend service built with **Python**, designed for managing **promotional campaigns**, **user subscriptions**, and **event engagement tracking** (views, clicks, redemptions, etc.).  
This project emphasizes **real-world engineering skills** through:

- Robust **relational modeling** (PostgreSQL)
- Clean and maintainable **REST API architecture**
- **Asynchronous processing** with idempotency
- **Event queue + DLQ + retries**
- **Security applied to PII** (encryption)
- **Testing and mocking in depth**
- **Data structures** (hash maps, queues) used for efficient tracking

> The project is intentionally structured as a **professional portfolio repository**, showcasing practical engineering decisions over academic abstractions.

---

## 🚀 Features

| Feature | Description |
|--------|-------------|
| 👥 Users | Create users with encrypted personal data (PII) |
| 🎯 Promotions | Manage marketing campaigns (active, draft, ended) |
| 🔐 Subscriptions | Link users to promotions with validation rules |
| 📊 Events | Receive and process engagement events (VIEW, CLICK, REDEEM) |
| 🧾 Idempotency | Prevent duplicated event processing |
| 🪣 DLQ & Retry | Failed events are retried, then sent to a Dead Letter Queue |
| 📈 Stats | Fast engagement analytics using in-memory hash maps |
| 🔒 PII Security | Encrypt email and phone fields before persisting |
| 🧮 Algorithms | Sliding window rate-limiting + dict aggregation |

---

## 🧱 Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.12+ |
| Web Framework | FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy (async) + Alembic |
| Messaging | In-memory queue (optional: Redis or AWS SQS) |
| Testing | pytest, pytest-asyncio, httpx, unittest.mock |
| Encryption | cryptography (Fernet) |
| Containerization | Docker + Docker Compose |
| Optional Serverless | FastAPI on AWS Lambda via Mangum |

---

## 📐 Architecture Overview

promopulse/ app/ api/                # Routers  
core/               # Config, Security (PII Encryption)  
db/                 # Models, Session, Migrations  
domain/             # Business rules (Entities + Services)  
infrastructure/     # Repositories, Queue, Workers  
tests/              # Unit + Integration  
docker/             # Compose / Dockerfile  
README.md

🧠 **Design Principles**
- Clean organization by domain
- Async-first DB and API
- Small, testable services
- Real data flows (queue → worker → DB)

---

## 🗃️ Database Modeling

### 🔹 Entities

| Table | Purpose |
|-------|---------|
| `users` | PII encrypted |
| `promotions` | Campaign definitions |
| `subscriptions` | Links users to promotions |
| `events` | Incoming engagement events |
| `processed_events` | Idempotency record |
| `dead_letter_events` | Failed events after retries |

📌 Indexes added for subscription lookup, event aggregation, and idempotency.

---

## 🧵 Event Processing Flow

1. Client sends event to `POST /events/ingest`.
2. If already processed (idempotency check) → **return 200**.
3. Else → event enters queue.
4. Worker consumes and:
   - Updates stats (hash map aggregation)
   - Persists data
5. On failure:
   - Retries controlled
   - If retries exhausted → moves to DLQ

📌 **Rate limiting** is implemented using a **sliding window + deque** per subscription.

---

## 🔐 Security Applied

- PII encryption using **`cryptography.Fernet`** (symmetric authenticated encryption)
- Encryption key provided via the **`PII_ENCRYPTION_KEY`** environment variable
- Key never logged; PII should not be logged in plaintext
- Encryption service initialized on startup – app fails fast if key is missing or invalid
- JWT support can be added later as an optional module

---

## 🧪 Testing Strategy

| Test Type | Focus |
|----------|-------|
| Unit | Domain logic, rate limiting, idempotency |
| Integration | End-to-end event ingestion + DB operations |
| Mocking | Fakes for queues, workers, encryption |
| API | Contract tests with httpx |

---

## 🐳 Running the Project

### **Requirements**
- Docker & Docker Compose
- Python 3.12+

### **Generate an Encryption Key**

Use `cryptography.Fernet` to generate a valid key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### **Access DB via terminal**
```bash
docker exec -it promopulse-db psql -U promopulse -d promopulse
```