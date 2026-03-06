# Backend Architecture

## Overview

The backend uses a layered architecture with clear separation of concerns. Each layer has a single responsibility and communicates with adjacent layers through well-defined interfaces.

```
HTTP Request
    ↓
[ API Layer ]         FastAPI route handlers, Pydantic schemas
    ↓
[ Service Layer ]     Business logic, orchestration
    ↓
[ Domain Layer ]      Entities, state machines, business rules
    ↓
[ Repository Layer ]  Data access protocols + SQLAlchemy implementations
    ↓
[ Database ]          PostgreSQL via SQLAlchemy ORM
```

---

## The Layers

### API Layer (`src/app/api/`, `src/app/schemas/`)

Responsible for:
- Parsing and validating incoming HTTP requests (via Pydantic schemas)
- Authenticating the current user
- Calling the appropriate service method
- Serializing the response (via Pydantic schemas)
- Translating domain exceptions into HTTP errors

The API layer knows nothing about the database. It speaks in Pydantic schemas on the boundary and domain objects internally.

**Pydantic schemas** are split by direction:
- `*Create` / `*Update` — incoming request bodies; validate user input
- `*Read` / `*ListItem` — outgoing responses; control what fields are exposed

Example: a client sends `ManuscriptCreate` (with `title`, `genre_ids`, etc.), the handler constructs a response using `ManuscriptRead` (with full `genres` objects, not just IDs).

### Service Layer (`src/app/services/`)

Responsible for:
- Orchestrating multi-step operations
- Enforcing business rules that span multiple domain objects
- Coordinating between repositories when needed

Services do not know about HTTP, Pydantic, or SQLAlchemy. They work with domain objects and repository protocols.

Example: `ManuscriptService.create()` creates the `Manuscript` domain object, persists it via the repository, then calls `set_genres()` on the same repository, and re-fetches to return the hydrated result. The service coordinates these steps; no single layer below it does.

### Domain Layer (`src/app/domain/`)

Responsible for:
- Representing core business entities as plain Python dataclasses
- Encoding business rules and state transitions as methods
- Raising domain-specific exceptions when rules are violated

Domain objects have no dependencies on the database, HTTP, or Pydantic. They can be instantiated and tested in complete isolation.

Example: `Manuscript.mark_ready()` enforces that the transition only happens from `DRAFT` state, raising `InvalidStateTransition` otherwise. The service calls this method; the repository persists the result.

**State machine example (Manuscript):**
```
DRAFT → READY → ARCHIVED
  ↑_______|
(unarchive goes to READY, not DRAFT)
```

Methods like `mark_ready()`, `archive()`, and `unarchive()` encode valid transitions. `can_generate_ebook()` expresses a business rule as a readable predicate.

### Repository Layer (`src/app/repositories/`)

Responsible for:
- Persisting and retrieving domain objects
- Translating between SQLAlchemy ORM models and domain dataclasses
- Isolating the rest of the codebase from database concerns

The repository layer has two parts:

**Protocols** (`protocols.py`) define the interface each repository must satisfy, using Python's structural typing (`Protocol`). This lets the service layer depend on the interface, not the implementation — enabling in-memory fakes in tests without inheriting from a base class.

**SQLAlchemy implementations** (`sqlalchemy.py`) provide the real database-backed implementations. Private mapper functions (e.g. `_manuscript_model_to_domain()`) translate ORM models to domain objects. These are intentionally not methods — they're pure functions with no side effects.

Example mapper:
```python
def _manuscript_model_to_domain(model: ManuscriptModel) -> Manuscript:
    return Manuscript(
        id=model.id,
        title=model.title,
        genres=[_genre_model_to_domain(g) for g in model.genres],
        # ... etc
    )
```

Note that `genres` is populated from the SQLAlchemy relationship here — the domain object is always fully hydrated when returned from the repository.

### Database Layer (`src/app/db/`)

SQLAlchemy ORM models define the database schema. These are separate from the domain dataclasses — they carry SQLAlchemy-specific concerns (column types, foreign keys, relationships, cascade rules) that don't belong in the domain.

---

## Request Lifecycle: Two Examples

### Example 1: `GET /manuscripts/{id}`

```
1. FastAPI receives request, extracts path param and auth token
2. CurrentAuthorId dependency resolves the authenticated author UUID
3. Handler calls service.get(manuscript_id)
4. Service calls repo.get(manuscript_id)
5. Repository calls session.get(ManuscriptModel, manuscript_id)
6. SQLAlchemy loads ManuscriptModel + genres relationship from DB
7. _manuscript_model_to_domain() maps to Manuscript dataclass
8. Service receives Manuscript, raises ManuscriptNotFound if None
9. Handler checks manuscript.author_id == author_id (ownership)
10. Handler constructs ManuscriptRead from Manuscript fields
11. FastAPI serializes ManuscriptRead to JSON response
```

### Example 2: `POST /manuscripts` (create with genres)

```
1. FastAPI receives multipart form data
2. Handler validates title, reads file bytes, uploads file to storage
3. Handler calls service.create(author_id, title, ..., genre_ids=[1, 3])
4. Service instantiates Manuscript domain object (genres=[])
5. Service calls repo.add(manuscript) → inserts row, returns Manuscript with DB-assigned ID
6. Service calls repo.set_genres(manuscript.id, [1, 3]) → deletes + re-inserts join table rows
7. Service calls repo.get(manuscript.id) → re-fetches with genres populated
8. Service returns fully hydrated Manuscript to handler
9. Handler constructs ManuscriptRead (genres: list[GenreRead]) and returns
```

The re-fetch in step 7 is necessary because the in-memory `Manuscript` from step 5 does not have its `genres` list updated by the `set_genres()` call — that only touches the database.

---

## The Genre System

Genres are hierarchical reference data (parent → children) stored in a `genres` table with a self-referential `parent_id`. Manuscripts are linked to genres via a `manuscript_genres` join table (many-to-many).

**ID types:** Genres use auto-increment integer PKs (not UUIDs) because they are lookup/reference data never exposed directly in URLs — slugs serve that purpose instead.

**Ownership of genre assignment:** Genre IDs travel through the system as `list[int]`, converted to join table rows by `ManuscriptRepository.set_genres()`. The `Manuscript` domain object holds `genres: list[Genre]` as a read-only view populated by the repository. Genre assignment is never done through the domain object directly.

**API boundary:**
- Inbound: `genre_ids: list[int]` (in `ManuscriptCreate` / `ManuscriptUpdate`)
- Outbound: `genres: list[GenreRead]` (in `ManuscriptRead`)

---

## Key Patterns

### Soft Delete

Most entities have a `deleted_at: datetime | None` field. Soft-deleted records remain in the database but are filtered out by default. Repository methods accept `include_deleted: bool = False` to opt in to seeing them. Hard deletes exist but are rarely used.

### Mutable Default Fields in Dataclasses

Python shared-mutable-default gotcha: never use `= []` as a default for a list field in a dataclass. Always use `field(default_factory=list)`:

```python
# Wrong
genres: list[Genre] = []

# Correct
genres: list[Genre] = field(default_factory=list)
```

Pydantic models don't have this problem — `= []` is safe there.

### Protocol-Based Repositories

Services depend on repository protocols, not concrete implementations:

```python
class ManuscriptService:
    def __init__(self, repo: ManuscriptRepository, ...):  # protocol, not SQLAlchemy class
```

This means tests can pass an `InMemoryManuscriptRepository` that satisfies the same protocol without any database setup.

### Schema Separation (in/out)

Never reuse the same Pydantic schema for input and output. Input schemas validate user-provided data; output schemas control the API surface. They will diverge as the project evolves (e.g., `genre_ids` on input, full `GenreRead` objects on output).

---

## Adding a New Feature

When adding a new entity (e.g. Tags in STORE-002), the typical sequence is:

1. **Domain** — create the dataclass in `src/app/domain/`, export from `__init__.py`
2. **Database** — add `*Model` to `src/app/db/models.py`; create an Alembic migration
3. **Repository** — add protocol to `protocols.py`; implement in `sqlalchemy.py` with a mapper function; export from `__init__.py`
4. **Schemas** — add `*Create`, `*Update`, `*Read` to `src/app/schemas/`
5. **Service** — add or update service to orchestrate operations
6. **API** — add route handlers; wire up dependencies
7. **Tests** — unit test domain logic; integration test the API endpoints
