"""Pre-commit documentation lint (no security)."""

from __future__ import annotations
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    (r"if\s+timestamp\s*==\s*\d+", "hard-coded timestamps are forbidden"),
    (r"if\s+activity\s*==\s*[\"'].*[\"']\s*:\s*return\s+[\"']brand_", "hard-coded brand mappings are forbidden"),
    (r"score\s*-=\s*0\.\d+", "soft-penalty brand scoring is forbidden; use hard blocks"),
]

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    py_files = list((root / "app").rglob("*.py"))
    bad = []
    for f in py_files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for pat, reason in FORBIDDEN_PATTERNS:
            if re.search(pat, text):
                bad.append((str(f), pat, reason))
    if bad:
        for f, p, r in bad:
            print(f"  {f}\n    pattern: {p}\n    reason:  {r}")
        print(f"\n{len(bad)} anti-pattern matches — fix before pushing.")
        return 1
    print(f"✓ {len(py_files)} Python files clean of anti-patterns.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
