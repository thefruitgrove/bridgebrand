"""Verify that the due PUBLICITY edition is prepared in the database.

This check uses service credentials only inside GitHub Actions. It never prints the
credential or article payload. Anonymous visibility is checked separately.
"""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

DOMAINS=("cpr","gov","uni","ent")
KST=ZoneInfo("Asia/Seoul")

def publication_date():
    raw=os.getenv("PUBLICATION_DATE","").strip()
    return dt.date.fromisoformat(raw) if raw else dt.datetime.now(KST).date()

def expected_ids(day):
    if day.weekday()==0:
        iso=(day-dt.timedelta(days=1)).isocalendar()
        return [f"{iso.year}-w{iso.week:02d}-overall-all"]
    if day.weekday() in (2,4):
        iso=day.isocalendar()
        slot="wed" if day.weekday()==2 else "fri"
        return [f"{iso.year}-w{iso.week:02d}-{slot}-{domain}" for domain in DOMAINS]
    return []

def fetch_row(base,key,article_id):
    query=urllib.parse.urlencode({
        "select":"id,status,scheduled_at,prepared_at",
        "id":f"eq.{article_id}",
        "limit":"1",
    })
    request=urllib.request.Request(
        f"{base.rstrip('/')}/rest/v1/bridge_publicity_articles?{query}",
        headers={"apikey":key,"Authorization":f"Bearer {key}"},
    )
    with urllib.request.urlopen(request,timeout=30) as response:
        rows=json.loads(response.read())
    return rows[0] if rows else None

def main():
    base=os.environ["SUPABASE_URL"]
    key=os.environ["SUPABASE_SECRET_KEY"]
    day=publication_date()
    expected=expected_ids(day)
    if not expected:
        print(json.dumps({"ok":True,"publication_date":day.isoformat(),"expected":0,"reason":"not a publication day"}))
        return
    failures=[]
    for article_id in expected:
        row=fetch_row(base,key,article_id)
        if not row:
            failures.append(f"{article_id}:missing")
        elif row.get("status")!="ready":
            failures.append(f"{article_id}:status={row.get('status')}")
        elif not row.get("prepared_at"):
            failures.append(f"{article_id}:prepared_at missing")
    if failures:
        raise SystemExit("Due PUBLICITY preparation failed: "+"; ".join(failures))
    print(json.dumps({"ok":True,"publication_date":day.isoformat(),"expected":len(expected),"ids":expected}))

if __name__=="__main__":
    main()
