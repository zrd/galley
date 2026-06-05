# Publishing States

The visibility of an ebook to customers is determined by two independent fields:
`ManuscriptState` (on the manuscript) and `Visibility` (on each ebook). Neither
alone is sufficient — both must permit access for a customer to browse or download.

---

## ManuscriptState

Controls the editing lifecycle of the manuscript. Acts as a gate on all ebooks
regardless of their individual visibility settings.

| State      | Effect on ebooks                                          |
|------------|-----------------------------------------------------------|
| `DRAFT`    | All ebooks blocked — no listing, no download              |
| `READY`    | Ebook visibility is in full control (see below)           |
| `ARCHIVED` | Download blocked; PUBLISHED ebooks remain listed in store |

**ARCHIVED** implements a "vault" model: the title stays visible in the public
store as an out-of-print or temporarily unavailable listing, but customers cannot
download it. The author can pull a title from the vault by un-archiving (restoring
to READY) or remove it entirely by un-publishing the ebook first.

---

## Ebook Visibility

Author-controlled per ebook. Only meaningful when the manuscript is in READY state.

| Visibility    | Listed in store | Downloadable with link |
|---------------|-----------------|------------------------|
| `PRIVATE`     | No              | No                     |
| `UNLISTED`    | No              | Yes                    |
| `PUBLISHED`   | Yes             | Yes                    |

---

## Combined State Table

| Manuscript State | Ebook Visibility | Workflow moment                                        | Author                              | Customer                                    |
|------------------|------------------|--------------------------------------------------------|-------------------------------------|---------------------------------------------|
| `DRAFT`          | *(none)*         | Fresh upload, no ebook generated yet                   | Editing                             | Nothing to access                           |
| `DRAFT`          | `PRIVATE`        | Reverted to draft; ebook was staged but unreleased     | Editing                             | No access (same as before revert)           |
| `DRAFT`          | `UNLISTED`       | Reverted to draft; ebook was on a private link         | Editing                             | Temporarily blocked — brief outage          |
| `DRAFT`          | `PUBLISHED`      | Reverted to draft to fix an error; ebook was live      | Editing; expects brief outage       | Temporarily blocked — brief outage          |
| `READY`          | *(none)*         | Marked ready, ebook not yet generated                  | Ready to generate                   | Nothing to access                           |
| `READY`          | `PRIVATE`        | Ebook generated, not yet released                      | Staging / pre-launch review         | No access                                   |
| `READY`          | `UNLISTED`       | Selective distribution — ARC readers, book fair, promo | Distributed specific links          | Can download with link; not browseable      |
| `READY`          | `PUBLISHED`      | Live in store                                          | Normal ongoing sales                | Can browse and download                     |
| `ARCHIVED`       | `PRIVATE`        | Manuscript retired, ebook was never released           | Done                                | No access                                   |
| `ARCHIVED`       | `UNLISTED`       | Manuscript retired; old private links still resolve    | Done; links lead to unavailable page | Cannot download                            |
| `ARCHIVED`       | `PUBLISHED`      | Title in the vault — listed but out of print           | Deliberate scarcity / teaser        | Can browse listing; download blocked        |

---

## State Transitions

### ManuscriptState

```
DRAFT ── mark_ready() ──► READY ── archive() ──► ARCHIVED
  ▲                        │ ▲                       │
  └───── mark_draft() ─────┘ │        unarchive() ───┘
                             └─────────────┘
```

- `mark_draft()`: READY → DRAFT only. Raises `InvalidStateTransition` from DRAFT or ARCHIVED.
- `mark_ready()`: DRAFT → READY only.
- `archive()` / `unarchive()`: READY ↔ ARCHIVED.
- `update_source()`: implicitly resets to DRAFT (source change invalidates ready status).

### Ebook Visibility

Transitions are unrestricted — author can move between PRIVATE, UNLISTED, and
PUBLISHED in any direction at any time, subject to the manuscript state gate.

---

## Key Design Decisions

**Ebook links are permanent.** Once an ebook is generated and a link distributed,
that link should never be silently invalidated by an editorial action (e.g.
reverting to draft, replacing the source file). If an author fixes an error and
regenerates, the new ebook gets a new link; the old one remains valid. The author
may explicitly un-publish the old version if they choose.

**`update_source()` does not touch ebook visibility.** Replacing the source file
resets manuscript state to DRAFT (blocking all ebooks temporarily) but does not
delete or suppress existing ebooks. The author generates a new ebook from the
corrected source and publishes it deliberately.

**ARCHIVED is not the same as deleted.** Archiving withdraws a title from
download while keeping its store presence. An author who wants to fully remove a
title un-publishes its ebooks first, then archives the manuscript.
