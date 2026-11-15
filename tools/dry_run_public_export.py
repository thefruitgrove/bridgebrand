"""Read-only production export dry-run for a fixed, previously published date.

Examples (in an isolated checkout with BRIDGE Supabase credentials):
    python tools/dry_run_public_export.py --date 2026-11-14

Only SELECT requests are available. Generated artifacts are saved in a
temporary directory, never in site/data, the working tree or production.
No scoring, SQL writes, workflow dispatch, publication or deployment.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import tempfile
import time
from pathlib import Path

from bridge_pipeline import run as pipeline
from bridge_pipeline.core import SupabaseRest, load_methodology


class ReadOnlyDB:
    def __init__(self, client):
        self.client = client
        self.queries = 0

    def select(self, table, query):
        if table not in {
            "bridge_rankings", "bridge_index_metrics", "bridge_entities",
            "bridge_axis_observations",
        }:
            raise RuntimeError("Dry-run forbids access to unrelated table: " + table)
        self.queries += 1
        return self.client.select(table, query)

    def __getattr__(self, name):
        raise RuntimeError("Production write operation is forbidden: " + name)


def validate(payload, db, as_of):
    cfg = load_methodology()
    method = cfg["version"]
    expected_date = as_of.isoformat()
    if payload["asOfDate"] != expected_date or payload["methodologyVersion"] != method:
        raise RuntimeError("Fixed-date or methodology mismatch in generated export")
    labels = cfg.get("release_policy", {}).get("public_domain_labels", {})
    source = db.select("bridge_rankings",
        "select=entity_id,domain,ranking_type,rank,score,trust_grade,methodology_version"
        f"&as_of_date=eq.{expected_date}&methodology_version=eq.{method}"
        "&ranking_type=eq.T100&published_at=not.is.null")
    entities = {r["id"]: r["external_id"] for r in db.select(
        "bridge_entities", "select=id,external_id")}
    expected = {(labels.get(r["domain"],r["domain"]),entities[r["entity_id"]]): r
                for r in source}
    actual = {(r["domain"],r["external_id"]): r for r in payload["rankings"]}
    if len(expected) != len(source) or len(actual) != payload["recordCount"]:
        raise RuntimeError("Duplicate DB or generated public entity IDs")
    if set(expected) != set(actual):
        raise RuntimeError("DB/public target mismatch: " + str({
            "missing": len(set(expected)-set(actual)),
            "additional": len(set(actual)-set(expected))}))
    diffs=[]
    for key, orig in expected.items():
        pub=actual[key]
        if (abs(float(orig["score"])-float(pub["score"])) > .001
                or orig["trust_grade"] != pub["trust_grade"]
                or int(orig["rank"]) != int(pub["rank"])):
            diffs.append({"id":key[1],"domain":key[0],"rank_from_db":orig["rank"],
                          "rank_from_export":pub["rank"]})
    if diffs:
        raise RuntimeError(f"Public export score/grade/rank mismatch: {len(diffs)}. "
                           +json.dumps(diffs[:5],ensure_ascii=False))
    if payload["recordCount"] != 400:
        raise RuntimeError(f"Expected four T100 panels of 100, got {payload['recordCount']}")
    for domain in ("CPR", "GOV", "UNI", "ENT"):
        rows=[r for r in payload["rankings"] if r["domain"]==domain
              and r["ranking_type"]=="T100"]
        if len(rows)!=100 or sorted(r["rank"] for r in rows)!=list(range(1,101)):
            raise RuntimeError("Incomplete or non-contiguous T100 panel: "+domain)
        for r in rows:
            if r["axes_available"]<cfg["minimum_publishable_axes"]:
                raise RuntimeError("Unpublishable axis coverage: "+r["external_id"])
    canonical=hashlib.sha256(
        json.dumps(payload["rankings"],sort_keys=True,ensure_ascii=False).encode()
    ).hexdigest()[:20]
    if payload["snapshotId"]!=canonical:
        raise RuntimeError("Reproducible snapshot identifier mismatch")
    return {"as_of_date":expected_date,"snapshot_id":canonical,
            "row_count":payload["recordCount"],"domains":4,"diff_count":0}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",required=True)
    args=p.parse_args()
    as_of=dt.date.fromisoformat(args.date)
    if as_of>dt.date.today():
        raise ValueError("Future observation date not allowed")
    db=ReadOnlyDB(SupabaseRest())
    original_root=pipeline.ROOT
    t0=time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="bridge-export-readonly-") as tmp:
            root=Path(tmp)
            (root/"site/data").mkdir(parents=True)
            (root/"data").mkdir()
            pipeline.ROOT=root
            pipeline.export_latest(db,as_of)
            data=json.loads((root/"site/data/latest.json").read_text(encoding="utf-8"))
            result=validate(data,db,as_of)
    finally:
        pipeline.ROOT=original_root
    result.update({"read_queries":db.queries,
                   "elapsed_sec":round(time.monotonic()-t0,2),
                   "mode":"READ_ONLY_TEMPORARY_FILES",
                   "status":"PASS"})
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
