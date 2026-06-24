# Vault 1 — Client Intelligence Dashboard

Per doc section 4.4. Auto-updates as `fireflies_sync.py` and `gmail_sync.py` write `last_contact` and append to client files — no manual edits needed.

## All Active Clients — Last Contact Date
```dataview
TABLE WITHOUT ID link(file.link, client) AS Client, last_contact, status, products
FROM "Clients"
WHERE status = "Active"
SORT last_contact ASC
```

## Dormancy Alert (no contact in 7+ days)
```dataview
TABLE WITHOUT ID link(file.link, client) AS Client, last_contact, contact_name
FROM "Clients"
WHERE date(today) - date(last_contact) > dur(7 days)
SORT last_contact ASC
```

## All Open Issues
```dataview
TASK
FROM "Clients"
WHERE !completed
GROUP BY link(file.link, client) AS Client
```
