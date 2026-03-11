# Finterm Worker

Background worker scaffolding for scheduled ingestion and alerts.

Phase 5 status:
- executes periodic alert-rule evaluations via backend alert service
- generates one daily brief per UTC day when missing
- writes notification records for alert triggers and brief generation
- still intentionally lightweight (single-process polling loop, no external scheduler)

Run:

```bash
python3 -m worker.main
```

Note:
- Worker imports backend app modules from `apps/api`.
- Configure cadence with `WORKER_POLL_SECONDS` (default `60`).
