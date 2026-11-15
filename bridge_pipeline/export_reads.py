"""Bounded, read-only public-profile projection; never fetch evidence payloads."""
from __future__ import annotations

import re


def public_observations(db, start, end, versions):
    # profile() needs only these two dates from potentially huge diagnostics.
    # Keyset pagination avoids increasingly expensive OFFSET plans and retains
    # a unique, stable cursor even for multiple methodology versions.
    base = (
        'select=id,entity_id,as_of_date,axis,score,status,methodology_version,'
        'evidence_date:diagnostics->>evidence_date,'
        'flow_evidence_date:diagnostics->flow->>evidence_date'
        f'&as_of_date=gte.{start.isoformat()}&as_of_date=lte.{end.isoformat()}'
        f'&methodology_version=in.({",".join(versions)})&order=id.asc'
    )
    size, cursor = 500, None
    while True:
        query = base + f'&limit={size}' + (f'&id=gt.{cursor}' if cursor else '')
        try:
            page = db.select('bridge_axis_observations', query)
        except RuntimeError as exc:
            if not re.search(r'"code"\s*:\s*"57014"', str(exc)) or size <= 32:
                raise
            size = max(32, size // 2)
            continue  # same cursor; retry reads only, never skip a page
        if not page:
            return
        ids = [row['id'] for row in page]
        if ids != sorted(set(ids)) or (cursor and ids[0] <= cursor):
            raise RuntimeError('public export blocked: non-monotonic observation IDs')
        for row in page:
            row = dict(row)
            row['diagnostics'] = {
                'evidence_date': row.pop('evidence_date', None),
                'flow': {'evidence_date': row.pop('flow_evidence_date', None)},
            }
            row.pop('id')
            yield row
        cursor = ids[-1]
        if len(page) < size:
            return
