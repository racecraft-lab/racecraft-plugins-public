# Tasks: Customer notifications feature

Multiple independent additive capabilities, each shippable on its own. Purely
additive work across three distinct production surfaces (a new database table, a
new API endpoint, a new UI panel) — no existing behavior is changed.

- [ ] T001 [P] Add the notifications store: `CREATE TABLE notifications` with a new
  nullable `read_at` column in `db/migrations/0007_create_notifications.sql`.
- [ ] T002 [P] Add a new read-only listing endpoint that returns notifications in
  `src/app/api/notifications/route.ts` (adds a new route, touches nothing existing).
- [ ] T003 [P] Add a new bell/inbox panel component in
  `src/components/NotificationBell.tsx` that renders the unread count.
