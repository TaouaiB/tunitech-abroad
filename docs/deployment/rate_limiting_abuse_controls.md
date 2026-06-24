# Rate Limiting & Abuse Controls

To protect the TuniTech Abroad platform from automated abuse and excessive resource usage, rate limiting must be applied. 

## Strategy for MVP

We will use a Django/Redis cache-backed rate limit service. Thin views will call this service. We aim to avoid heavy third-party dependencies unless strictly necessary.

*Note: Caddy/Nginx may add coarse IP limits later, but app-level guardrails are required for user-specific actions.*

## Rate Limits by Action

| Action | Limit / Scope | Protection Goal |
|---|---|---|
| **Login attempts** | 5 per 5 minutes per IP/User | Prevent brute-force credential stuffing. |
| **Signup attempts** | 3 per hour per IP | Prevent mass account creation. |
| **Password reset** | 3 per hour per email | Prevent email bombing / spam. |
| **CV upload** | 5 per day per User | Prevent storage exhaustion and abuse of PDF processing. |
| **Quick Match** | 10 per hour per User | Prevent CPU-heavy matching spam. |
| **Recommendation refresh** | 5 per hour per User | Prevent heavy DB querying spam. |
| **Save / Unsave job** | 30 per minute per User | Prevent rapid automated toggling. |
| **Email / Unsubscribe / Contact** | 5 per hour per User | Prevent transactional email abuse. |
| **Admin endpoints** | Coarse IP limits (Nginx/Caddy) | Prevent scanning of admin panels. |

## Implementation Plan (Phase 15J TODOs)

- [ ] Verify `django-ratelimit` or a custom Redis rate-limit service is correctly applied to the above views.
- [ ] Ensure rate limit violations return a clean `429 Too Many Requests` response.
