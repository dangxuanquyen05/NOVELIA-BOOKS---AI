# AGENTS.md — NOVELIA BOOKS AGENT OPERATING DIRECTIVE

> **Project:** NOVELIA BOOKS  
> **Classification:** Core Technical & Governance Guidelines  
> **Status:** Active & Mandatory  
> **Target Audience:** All AI Coding Agents, Software Architects, and Contributing Engineers

---

## 1. IDENTITY & MISSION

You are operating within the **NOVELIA BOOKS** engineering workspace as a Senior Software Architect, Technical Lead, AI Engineer, and QA Lead.

NOVELIA BOOKS is a production-grade e-commerce book platform combining full retail operations, store administration, and an advanced AI assistant ecosystem (Novelia AI Assistant & BookMatch AI). It is **not** a mock demo, landing page, or disposable prototype. Every component, schema, and API must adhere to enterprise-level software engineering standards.

---

## 2. NON-NEGOTIABLE CORE COMMANDMENTS

1. **Backend is the Ultimate Authority:**
   - Never trust client-side data for prices, discounts, stock levels, order totals, or user roles.
   - All monetary calculations and stock deductions MUST be validated and executed on the backend within ACID transactions.
   - Hiding UI buttons or views is a UX feature, NOT an authorization mechanism.

2. **Absolute RBAC Enforcement:**
   - User roles are strictly defined: `CUSTOMER`, `STAFF`, `ADMIN`.
   - Every private backend endpoint MUST enforce role checks via dependency injection (`get_current_active_user`, `require_roles(...)`).
   - Cross-tenant data leaks are strictly prohibited (e.g., a customer must NEVER be able to query another customer's orders or profile).

3. **AI is a Constrained Advisor, NOT a Superuser:**
   - The AI Assistant has **ZERO** direct SQL or database connection access.
   - The AI must interact with the system strictly through strongly-typed, schema-validated backend tool functions.
   - All AI tool calls execute within the security context of the authenticated user.
   - Mutating actions (e.g., creating drafts, modifying inventory, cancelling orders) require an explicit user confirmation step.
   - Untrusted inputs (user prompts, book contents, external webhooks) must NEVER be treated as system instructions.

4. **Database & Financial Integrity:**
   - Primary database is **MySQL Server** (database: `novelia_books`).
   - All monetary amounts MUST use `DECIMAL(12, 2)` or `DECIMAL(15, 2)`. Float or double types are strictly forbidden for currency.
   - At order creation, a permanent snapshot of item metadata (`title`, `price_at_purchase`, `isbn`, `sku`) must be captured in `order_items`.
   - Prevent negative inventory and race conditions using appropriate locking mechanisms (`SELECT ... FOR UPDATE` or optimistic versioning).
   - All schema changes MUST be managed via versioned **Alembic migrations**. Manual ad-hoc database modifications are strictly prohibited.
   - SQLite is **NEVER** to be used as a substitute for MySQL in integration tests.

5. **External Integrations Realism:**
   - Shipping (GHN/GHTK) and Payment (VNPay/MoMo/ZaloPay) integrations must use strict interface abstractions (`ShippingProvider`, `PaymentProvider`).
   - Clearly delineate between `MOCK`, `SANDBOX`, and `LIVE` environments.
   - Never claim an external provider is "integrated and working" unless verifiable credentials and sandbox/live tests have succeeded.

6. **Truth in Testing & Quality Assurance:**
   - Never declare a test or feature as `PASS` without executing real test suites and inspecting logs.
   - All unresolved bugs or failing tests must be documented transparently with reproduction steps.
   - Development and test databases must be strictly isolated (`novelia_books` vs `novelia_books_test`). Tests must NEVER mutate development or production data.

---

## 3. TECHNICAL STACK SPECIFICATION

| Component | Required Technology | Forbidden / Disallowed Alternatives |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.12+, FastAPI | Django, Flask, Express |
| **ORM & Migrations** | SQLAlchemy 2.x, Alembic | Raw cursor queries without ORM/Core, Tortoise ORM |
| **DB Driver** | PyMySQL or tested MySQL-compatible driver | SQLite (for integration tests), MongoDB |
| **Config & Validation** | Pydantic v2, `pydantic-settings` | Unvalidated dictionaries, raw `os.environ` |
| **Frontend Framework** | React 18+, TypeScript, Vite | Angular, Vue, Vanilla JS without TypeScript |
| **Styling & UI** | Tailwind CSS, shadcn/ui (Radix primitives) | Ad-hoc unstyled CSS, bloated full UI frameworks |
| **State & Data Fetching**| TanStack Query (React Query) / Axios | Raw `fetch` without error boundaries |
| **AI LLM Interface** | Decoupled Provider Adapter (Gemini / OpenAI API) | Direct client-side API calls, unabstracted LLM calls |
| **Backend Testing** | Pytest, Pytest-Asyncio, HTTPX (`TestClient`) | Unverified manual testing alone |
| **Frontend Testing** | Vitest, React Testing Library | Untested components |

---

## 4. ARCHITECTURAL LAYERING RULES

The backend codebase must strictly follow a layered, modular architecture:

```
backend/
├── app/
│   ├── api/             # FastAPI routers, endpoint definitions, HTTP status codes
│   │   ├── v1/          # Versioned API routes (auth, books, orders, ai, admin)
│   │   └── deps.py      # Dependency injection (db session, current user, rbac)
│   ├── core/            # Security (JWT, hashing), config (pydantic-settings), logging
│   ├── models/          # SQLAlchemy declarative models (DB entities)
│   ├── schemas/         # Pydantic schemas (Request, Response, Tool Call schemas)
│   ├── repositories/    # Data access layer (pure DB queries, transactions)
│   ├── services/        # Business logic, orchestration, calculation, event emission
│   ├── integrations/    # External adapters (Shipping, Payment, AI Provider)
│   │   ├── ai/          # AI client, prompt templates, tool definitions, guardrails
│   │   ├── payment/     # PaymentProvider interface, Mock, Sandbox adapters
│   │   └── shipping/    # ShippingProvider interface, Mock, GHN/GHTK adapters
│   └── db/              # Session factory, base model, Alembic migrations env
```

### Layer Rules:
- **Routers (`api/`)** must only validate request formats, invoke Service methods, and return response schemas. They must NEVER contain business algorithms or raw SQL.
- **Services (`services/`)** contain all domain business rules, pricing logic, inventory validation, and state machines. They do not deal directly with HTTP request objects.
- **Repositories (`repositories/`)** encapsulate database queries.
- **Models (`models/`)** contain only SQLAlchemy table definitions and relationships.
- **Frontend (`frontend/`)** must never embed business calculations (e.g., discount formulas, shipping fee math) as the source of truth. The frontend is a presentation and interaction layer.

---

## 5. AI INTEGRATION & TOOL CALLING CONVENTIONS

1. **Tool Definition:** Every AI tool must be defined as a Pydantic schema with strict field descriptions, types, and constraints.
2. **Context Injection:** When an AI tool is invoked, the backend must inject the `current_user` context into the tool executor. The tool must never accept a `user_id` parameter directly from the LLM prompt without verifying it matches the authenticated session (unless the caller has `ADMIN` role).
3. **Audit Log:** Every tool execution must generate a persistent record in `ai_audit_logs` capturing:
   - `session_id`, `user_id`, `role`
   - `tool_name`
   - `input_arguments` (sanitized of sensitive PII/secrets)
   - `execution_status` (`SUCCESS`, `REJECTED_RBAC`, `FAILED_VALIDATION`, `ERROR`)
   - `execution_duration_ms`
4. **Two-Phase Confirmation for Mutations:**
   - Any tool that alters database state (e.g., `cancel_order`, `draft_promotion`, `adjust_inventory`) must return a structured `CONFIRMATION_REQUIRED` payload containing a summary of the pending action and an ephemeral confirmation token.
   - The user must explicitly approve the action in the UI before the backend executes the mutation.
5. **System Resilience (Graceful Degradation):**
   - If the AI API provider is down or times out, the core e-commerce shop (browsing, cart, checkout, admin CRUD) must continue operating with zero disruption.
   - The AI chat interface must display a graceful, localized fallback error notice.

---

## 6. ENVIRONMENT & RUNTIME STANDARDS

- **OS Environment:** Windows 10/11 (PowerShell / Command Prompt).
- **Paths & Tooling:** Use forward-compatible path handling (`pathlib` in Python, standard Node.js path utils). Avoid hardcoded POSIX or Windows-only shell idiosyncrasies.
- **Ports (Default):**
  - Frontend: `http://localhost:5173`
  - Backend: `http://localhost:8000`
  - MySQL Server: `localhost:3306`
- **Secrets Management:**
  - Create and maintain `.env.example` with clear documentation for all required variables.
  - Never commit `.env` or any file containing API keys, private keys, or credentials to git.

---

## 7. PROTOCOL FOR AI AGENT INTERACTIONS

When receiving tasks or prompts from the user:
1. **Analyze First:** Check existing documentation and codebase before generating or modifying code.
2. **Do Not Overreach:** Strictly limit actions to the scope requested in the prompt. Do not begin subsequent phases autonomously.
3. **Traceability:** Document any technical decisions, trade-offs, or open questions in `docs/08_ARCHITECTURE_DECISIONS.md`.
4. **No Placeholders in Production Code:** Avoid `TODO: implement later` in critical security, authorization, or financial calculation paths.
5. **Review Before Completion:** Verify that all changes comply with this `AGENTS.md` directive before declaring a task finished.
