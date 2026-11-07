"""Hash-chained, append-only audit log. Every step (alert, verdict, approval, rollout, rollback) is one entry whose hash covers the previous entry."""
