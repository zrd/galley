# Logging Roadmap

## Current State
No logging exists in the application.

---

## 1. Setup (`src/app/logging.py`)

Create a centralized logging configuration:
- Structured JSON logging with correlation IDs
- Configure log levels via environment variable (`LOG_LEVEL`)
- Use `structlog` or standard logging with JSON formatter

**Key decisions:**
- **Format:** JSON (for log aggregation) vs human-readable (for dev)
- **Library:** `structlog` (cleaner API) vs stdlib `logging` (no dependencies)
- **Correlation:** Add request ID to trace requests across layers

---

## 2. Request Logging (middleware)

**Where:** `src/app/main.py` - add middleware

**What to log:**
- Request: method, path, query params, request ID
- Response: status code, duration
- Skip health checks to reduce noise

---

## 3. Authentication Events (`src/app/security/auth.py`)

**What to log:**
- Login success/failure (email, not password)
- Token refresh
- Invalid token attempts (rate limit warning)

**Level:** INFO for success, WARNING for failures

---

## 4. Service Layer (`src/app/services/`)

**What to log:**
- Entity creation (type, ID)
- State transitions (manuscript draft→ready)
- Soft deletes and restores
- Cascade operations

**Level:** INFO, include entity IDs for tracing

---

## 5. Storage Operations (`src/app/storage/`)

**What to log:**
- Upload success/failure (key, size, duration)
- Download requests
- Delete operations

**Level:** INFO, WARNING for failures

---

## 6. Error Handling (`src/app/api/errors.py`)

**What to log:**
- Unhandled exceptions (ERROR with stack trace)
- Domain exceptions (WARNING)
- Include request ID for correlation

---

## 7. Configuration (`src/app/config.py`)

Add settings:
```python
LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT: str = "json"  # json, text
```

---

## Implementation Order

1. **Setup** - logging config, request ID middleware
2. **Errors** - catch unhandled exceptions first
3. **Auth** - security-relevant events
4. **Services** - business operations
5. **Storage** - I/O operations
6. **Request middleware** - add last (can be noisy)

---

## Example Log Output

```json
{"timestamp": "2025-02-05T10:30:00Z", "level": "INFO", "request_id": "abc123", "event": "manuscript.created", "manuscript_id": "uuid", "author_id": "uuid"}
{"timestamp": "2025-02-05T10:30:01Z", "level": "WARNING", "request_id": "def456", "event": "auth.login_failed", "email": "user@example.com", "reason": "invalid_password"}
{"timestamp": "2025-02-05T10:30:02Z", "level": "INFO", "request_id": "ghi789", "event": "storage.upload", "key": "manuscripts/abc.epub", "size_bytes": 1048576, "duration_ms": 230}
{"timestamp": "2025-02-05T10:30:03Z", "level": "ERROR", "request_id": "jkl012", "event": "unhandled_exception", "exception": "ValueError", "message": "...", "traceback": "..."}
```

---

## Guidelines

- **Don't log:** passwords, tokens, file contents, PII beyond email
- **Do log:** entity IDs, operation types, durations, error context
- **Levels:**
  - DEBUG: Detailed internal state (dev only)
  - INFO: Normal operations (entity CRUD, state changes)
  - WARNING: Recoverable issues (auth failures, missing files)
  - ERROR: Unhandled exceptions, data integrity issues
