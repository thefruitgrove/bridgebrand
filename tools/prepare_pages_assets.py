"""Prepare Cloudflare Pages artifacts without deleting the historical source in Git.

Cloudflare Pages rejects individual assets above 25 MiB. The historical
snapshot may exceed that limit. During the Pages build only, divide its
rankings into bounded JSON shards and remove the oversized combined file
from the *build workspace*. The checked-in source remains untouched.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"
HISTORY = DATA / "history.json"
MANIFEST = DATA / "history-manifest.json"
PART_PREFIX = "history-part-"
TARGET_BYTES = 5 * 1024 * 1024
MAX_BYTES = 20 * 1024 * 1024


def encoded(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def main():
    if not HISTORY.exists():
        if MANIFEST.exists():
            print("History already sharded for deployment")
            return
        raise RuntimeError("Missing history.json; cannot prepare historical records")

    history = json.loads(HISTORY.read_text(encoding="utf-8"))
    if not isinstance(history, dict) or not isinstance(history.get("rankings"), list):
        raise RuntimeError("Unexpected history archive schema; keeping original")

    rankings = history["rankings"]
    metadata = {k: v for k, v in history.items() if k != "rankings"}
    chunks = []
    current = []
    current_size = 2
    for entry in rankings:
        raw = encoded(entry)
        if len(raw) + 2 >= MAX_BYTES:
            raise RuntimeError("Single history record exceeds safe deployment size")
        if current and current_size + len(raw) + 1 > TARGET_BYTES:
            chunks.append(current)
            current, current_size = [], 2
        current.append(entry)
        current_size += len(raw) + 1
    if current:
        chunks.append(current)

    files = []
    for i, part in enumerate(chunks, 1):
        name = f"{PART_PREFIX}{i:03d}.json"
        payload = encoded(part)
        if len(payload) >= MAX_BYTES:
            raise RuntimeError(f"Unsafe shard size: {name}")
        (DATA / name).write_bytes(payload)
        files.append(name)

    manifest = {"meta": metadata, "parts": files, "recordCount": len(rankings)}
    MANIFEST.write_bytes(encoded(manifest))
    assert sum(len(part) for part in chunks) == len(rankings)
    # Delete only from the ephemeral Cloudflare Pages build workspace.
    HISTORY.unlink()
    print(f"Pages assets ready: {len(rankings)} history records in {len(files)} shards")


if __name__ == "__main__":
    main()
