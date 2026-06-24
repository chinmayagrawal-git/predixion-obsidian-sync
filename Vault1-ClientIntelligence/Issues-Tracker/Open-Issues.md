# Open Issues — All Clients

```dataview
TASK
FROM "Clients"
WHERE !completed
GROUP BY link(file.link, client) AS Client
```
