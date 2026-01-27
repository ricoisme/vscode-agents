---
title: Security Checklist and Attack Surface Mapping
---

# Security Checklist (apply to EVERY file)

- Injection: SQL, command, template, header injection
- XSS: All outputs in templates properly escaped?
- Authentication: Auth checks on all protected operations?
- Authorization/IDOR: Access control verified, not just auth?
- CSRF: State-changing operations protected?
- Race conditions: TOCTOU in any read-then-write patterns?
- Session: Fixation, expiration, secure flags?
- Cryptography: Secure random, proper algorithms, no secrets in logs?
- Information disclosure: Error messages, logs, timing attacks?
- DoS: Unbounded operations, missing rate limits, resource exhaustion?
- Business logic: Edge cases, state machine violations, numeric overflow?

---

# Attack Surface Mapping (per changed file)

For every changed file in the branch, produce a mapping entry using the template below. Annotate severity (Critical/High/Medium/Low) and include a one-line remediation.

- File: `<relative path>`
  - User inputs:
    - Request params (query/path/body): list names and expected types
    - Headers: list header names read/used
    - URL components: path segments, host, port, query keys
    - Request body shapes / deserialized types
  - Database queries:
    - All SQL/ORM calls (raw SQL, parameterized queries, EF LINQ) with table names and parameters
    - Any dynamic SQL or string concatenation
  - Authentication / Authorization checks:
    - Where auth is enforced (middleware/controller/action)
    - Any missing authorization or potential IDOR checks
  - Session / State operations:
    - Session read/write, cookies set, distributed cache keys
    - Any read-then-write sequences that could be TOCTOU
  - External calls:
    - HTTP, gRPC, message queues, storage, third-party SDKs (endpoints + sensitive params)
    - Timeout/retry handling present?
  - Cryptographic operations:
    - Key usage, encryption/decryption, hashing, random generators
    - Secret sources (env, vault) and any logging of secrets
  - Other risk points:
    - Unbounded loops/collections, large file processing, streaming
    - Error messages returned to clients
    - Use of reflection, dynamic compilation, unsafe code

## Guidance

For each mapped item, annotate severity (Critical/High/Medium/Low) and include a one-line recommended remediation (e.g., parameterize query, add authorization check, set SameSite/HttpOnly on cookie, add rate limit).

## Example (short)

- File: `src/backend/Stock.Api/Controllers/ItemsController.cs`
  - User inputs: `GET /items?category={string}` (query `category`), `POST /items` (body `ItemDto`) — Low
  - DB queries: EF `db.Items.Where(i => i.Category == category)` (parameterized) — OK
  - AuthZ: `Authorize` missing on `POST /items` — High: add `[Authorize]`
  - External calls: none — Low
  - Crypto: none — Low
  - Other: returns full exception text to client — Medium: sanitize error responses

---

Place this file under the skill's `references/` folder and link to it from `SKILL.md` so reviewers can open the detailed checklist and mapping template.
