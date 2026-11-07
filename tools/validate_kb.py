"""Check every knowledge-base file against kb/SCHEMA.md. Exit code 1 on any problem."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orca import kb as kbmod  # noqa: E402


def main() -> int:
    kb = kbmod.load()
    errs = kbmod.validate(kb)
    by_j = Counter(r["jurisdiction"] for r in kb.records.values())
    verified = sum(1 for r in kb.records.values() if r["verified"])
    print(f"records: {len(kb.records)} ({dict(by_j)}), verified quotes: {verified}, "
          f"gaps: {len(kb.gaps)}, sources: {len(kb.sources)}")
    unhashed = [s["id"] for s in kb.sources.values() if not s.get("sha256")]
    if unhashed:
        print(f"note: {len(unhashed)} sources not yet fetched (run tools/fetch_sources.py)")
    for e in errs:
        print("ERROR", e)
    print("OK" if not errs else f"{len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
