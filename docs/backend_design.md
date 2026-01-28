## Self-Publisher: Backend Technical Details

### Technologies
- Python
- FastAPI
- Pydantic
- MyPy
- Postgres
- SQLAlchemy (if an ORM is needed)
- AWS S3 for binary asset storage

### MVP Scope
- Phase 1 (MVP): Free downloads, basic formats (EPUB, PDF), single author
- Phase 2: Paid downloads, ISBN integration, tracking
- Phase 3: Multi-author publishers, subscriptions

### Data Model (Draft)
- Manuscript: author's work with metadata, content, revisions
- Ebook: generated output file (epub, pdf, etc.) from a manuscript
- Author/Publisher: user account
- Customer: user account (can be anonymous/unregistered)
- WebStore: catalog view for an author/publisher
- Download: tracking instance of someone getting an ebook

### MVP API Endpoints
Phase 1 (MVP):
- POST /manuscripts - create manuscript
- GET /manuscripts - list user's manuscripts
- GET /manuscripts/:id - get single manuscript
- PUT /manuscripts/:id - update manuscript
- DELETE /manuscripts/:id - delete manuscript
- POST /manuscripts/:id/generate - generate ebook(s)
- GET /ebooks/:id/download - download generated ebook

### Out of scope for MVP
- Payment processing (Phase 2)
- ISBN integration
- Analytics/tracking
- Multi-author support
- Frontend/UI (separate project)
- Email notifications (Phase 2)
- Print format support
- Advanced DRM/encryption
