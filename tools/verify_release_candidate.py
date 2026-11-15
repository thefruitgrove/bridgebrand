"""Release-candidate offline rebuild guard: no credentials, no DB writes.

Run inside an isolated checkout:
  python tools/verify_release_candidate.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA_PATHS = (SITE / "data/latest.json", SITE / "data/history.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_contains(path: str, *needles: str) -> None:
    page = (SITE / path).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in page:
            raise AssertionError(f"{path} missing after rebuild: {needle}")


def run() -> None:
    before = {str(p): digest(p) for p in DATA_PATHS}
    snapshot = json.loads(DATA_PATHS[0].read_text(encoding="utf-8"))
    assert snapshot["recordCount"] == len(snapshot["rankings"])
    commands = (
        ["build.py"],
        ["tools/apply_brand_shell.py"],
        ["build_spa.py"],
        ["tools/apply_brand_shell.py"],
    )
    for args in commands:
        subprocess.run([sys.executable, *args], cwd=ROOT, check=True)
    after = {str(p): digest(p) for p in DATA_PATHS}
    if before != after:
        raise AssertionError("Static rebuild changed published JSON or lossless history")
    for page in ("bridge-v2.html", "index.html"):
        assert_contains(page, "REPUTATION IS A SIGNAL.", "EVIDENCE MAKES IT MEANINGFUL.",
                        "BRIDGE는 그 신호의 근거와 의미를 분석합니다.", 'id="v2SearchForm"')
    assert_contains("methodology.html", "EVIDENCE-BASED REPUTATION INTELLIGENCE",
                    "Reputation is a signal.")
    assert_contains("about.html", "WHAT NEXT", "근거")
    assert_contains("trust.html", "Evidence makes it meaningful.")
    assert_contains("briefing.html", 'id="bridgePublicEvidence"',
                    'id="bridgeActionChecks"', 'id="printReportDocument"')
    print("BRIDGE offline site rebuild passed; published JSON/history hashes unchanged.")


if __name__ == "__main__":
    run()
