"""Bounded, read-only public-profile projection; never fetch evidence payloads."""
from __future__ import annotations

import re
import datetime as dt


def _date_bounded_fallback(db, start, end, versions, after_id):
    """Rescue a repeatedly timed-out broad ID scan using indexed dates.

    Runs only after the global read fails with SQLSTATE 57014 down to a
    32-row page. Previously yielded rows have IDs <= after_id, so each
    day must independently respect the original global cursor.
    """
    day = start
    while day <= end:
        base = (
            'select=id,entity_id,as_of_date,axis,score,status,methodology_version,'
            'evidence_date:diagnostics->>evidence_date,'
            'flow_evidence_date:diagnostics->flow->>evidence_date'
            f'&as_of_date=eq.{day.isoformat()}'
            f'&methodology_version=in.({",".join(versions)})&order=id.asc'
        )
        size, cursor = 500, after_id
        while True:
            query = base + f'&limit={size}' + (f'&id=gt.{cursor}' if cursor else '')
            try:
                page = db.select('bridge_axis_observations', query)
            except RuntimeError as exc:
                if not re.search(r'"code"\s*:\s*"57014"', str(exc)) or size <= 32:
                    raise
                size = max(32, size // 2)
                continue
            if not page:
                break
            ids = [row['id'] for row in page]
            if ids != sorted(set(ids)) or (cursor and ids[0] <= cursor):
                raise RuntimeError('public export blocked: non-monotonic daily observation IDs')
            if any(row.get('as_of_date') != day.isoformat() for row in page):
                raise RuntimeError('public export blocked: out-of-window observation date')
            for row in page:
                yield _public_projection(row)
            cursor = ids[-1]
            if len(page) < size:
                break
        day += dt.timedelta(days=1)


def _public_projection(source):
    row = dict(source)
    row['diagnostics'] = {
        'evidence_date': row.pop('evidence_date', None),
        'flow': {'evidence_date': row.pop('flow_evidence_date', None)},
    }
    row.pop('id')
    return row


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
            if not re.search(r'"code"\s*:\s*"57014"', str(exc)):
                raise
            if size <= 32:
                # A broad indexed-by-ID scan can still time out at 32 rows.
                # Switch to date-scoped reads without repeating past IDs.
                yield from _date_bounded_fallback(db, start, end, versions, cursor)
                return
            size = max(32, size // 2)
            continue  # same cursor; retry reads only, never skip a page
        if not page:
            return
        ids = [row['id'] for row in page]
        if ids != sorted(set(ids)) or (cursor and ids[0] <= cursor):
            raise RuntimeError('public export blocked: non-monotonic observation IDs')
        for row in page:
            yield _public_projection(row)
        cursor = ids[-1]
        if len(page) < size:
            return
