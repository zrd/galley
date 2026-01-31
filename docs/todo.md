### TODO: For MVP
- Make POST /manuscripts atomic
  * Wrap filesystem operation + db operation in a transaction, something like
    1. Upload to a holding area
    2. Create database transaction
    3. Copy to permanent storage
    4. Commit transaction
  * Make idempotent
- Make DELETE /manuscript mark db records deleted but don't actually delete anything
- Make POST /sample actually create a Manuscript excerpt (currently just makes a db entry)

### TODO: Future Roadmap
- Make Author and Customer children of User -- consider use case of a single user with multiple roles (e.g. Customer becomes an Author or vice versa)
