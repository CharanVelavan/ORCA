"""ORCA-NTN dashboard: reads run files (audit/trace JSON Lines) and shows them in a browser.

Offline by design. No LLM, no network, no build step. Start it with:
    python -m dashboard --run runs/mock-s1.jsonl
Every satellite or NTN link shown here is emulated.
"""
