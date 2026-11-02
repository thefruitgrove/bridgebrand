"""Read PUBLICITY as an anonymous visitor, never with service credentials."""
import json
import re
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 config=json.loads(re.search(r'=(.*);', (ROOT/'site/publicity-config.js').read_text()).group(1))
 headers=['-H','apikey: '+config['key']]
 if config['key'].startswith('eyJ'):headers+=['-H','Authorization: Bearer '+config['key']]
 url=config['url']+'/rest/v1/bridge_publicity_articles?select=id,scheduled_at,is_example,payload&order=scheduled_at.desc&limit=240'
 result=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30',*headers,url],capture_output=True,check=True)
 rows=json.loads(result.stdout)
 assert isinstance(rows,list),'PUBLICITY response is not a list'
 launch_ids={f'2026-w42-{slot}-{domain}' for slot in ('wed','fri') for domain in ('cpr','gov','uni','ent')}
 visible_ids={r['id'] for r in rows}
 assert launch_ids<=visible_ids,'Formal Wednesday/Friday launch articles are incomplete'
 assert not any(r.get('is_example') for r in rows),'Legacy sample article is still public'
 import datetime as dt
 from zoneinfo import ZoneInfo
 now=dt.datetime.now(dt.timezone.utc)
 assert all(dt.datetime.fromisoformat(r['scheduled_at'].replace('Z','+00:00'))<=now for r in rows),'Future article leaked'
 kst=ZoneInfo('Asia/Seoul')
 now_kst=now.astimezone(kst)
 due=set()
 if now_kst.time()>=dt.time(12,0):
  if now_kst.weekday()==0:
   iso=(now_kst.date()-dt.timedelta(days=1)).isocalendar()
   due.add(f'{iso.year}-w{iso.week:02d}-overall-all')
  elif now_kst.weekday() in (2,4):
   iso=now_kst.date().isocalendar()
   slot='wed' if now_kst.weekday()==2 else 'fri'
   due={f'{iso.year}-w{iso.week:02d}-{slot}-{domain}' for domain in ('cpr','gov','uni','ent')}
 assert due<=visible_ids,'Due PUBLICITY edition is not anonymously visible after 12:00 KST: '+','.join(sorted(due-visible_ids))
 print(json.dumps({'ok':True,'visible_articles':len(rows),'launch_articles':len(launch_ids),'due_articles':len(due),'examples_visible':False,'future_articles_visible':False}))
if __name__=='__main__':main()
