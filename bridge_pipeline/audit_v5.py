"""Validate entity/date/version lineage before public export; no repair by guesses."""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
from .core import SupabaseRest,load_methodology,now_kst,ROOT
from .evidence_v5 import AXES,profile

def raw_refs(diag):
    refs=set()
    if diag.get('raw_item_id'):refs.add(diag['raw_item_id'])
    for k in ('official','flow'):
        
        if diag.get(k):refs.update(raw_refs(diag[k]))
    return refs

def signal_refs(diag):
    refs=set(diag.get('signal_ids') or [])
    for k in ('official','flow'):
        if diag.get(k):refs.update(signal_refs(diag[k]))
    return refs

def audit(db,as_of):
    cfg=load_methodology();q=f'as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg["version"]}'
    entities={e['id']:e for e in db.select('bridge_entities','select=id,external_id,name,domain')}
    scores=db.select('bridge_scores','select=entity_id,score,axes_used,publish_status,confidence_score,trust_grade,diagnostics&'+q)
    obs=db.select('bridge_axis_observations','select=entity_id,axis,score,status,diagnostics&'+q)
    ranks=db.select('bridge_rankings','select=entity_id,domain,score,ranking_type,published_at&'+q)
    by={}
    for o in obs:by.setdefault(o['entity_id'],[]).append(o)
    all_signal_ids=set().union(*(signal_refs(o.get('diagnostics') or {}) for o in obs)) if obs else set()
    signals={}
    ids=sorted(all_signal_ids)
    for k in range(0,len(ids),300):
        for s in db.select('bridge_signals',f'select=id,entity_id,raw_item_id,axis& id=in.({",".join(ids[k:k+300])})'.replace('& id','&id')):signals[s['id']]=s
    all_raw_ids=set().union(*(raw_refs(o.get('diagnostics') or {}) for o in obs)) if obs else set()
    all_raw_ids.update(v['raw_item_id'] for v in signals.values())
    raw={};ids=sorted(all_raw_ids)
    for k in range(0,len(ids),300):
        for r in db.select('bridge_raw_items',f'select=id,payload,canonical_url&id=in.({",".join(ids[k:k+300])})'):raw[r['id']]=r
    errors=[];records=[];sm={s['entity_id']:s for s in scores}
    for s in scores:
        e=entities.get(s['entity_id'])
        if not e:errors.append({'code':'UNKNOWN_ENTITY','entity_id':s['entity_id']});continue
        rows=by.get(s['entity_id'],[]);p=profile(rows,as_of)
        actual={o['axis'] for o in rows if o.get('score') is not None and o.get('status') in {'measured','carried'}}
        if set(s.get('axes_used') or [])!=actual:errors.append({'code':'AXES_USED_MISMATCH','external_id':e['external_id']})
        for o in rows:
            diag=o.get('diagnostics') or {}
            for sid in signal_refs(diag):
                linked=signals.get(sid)
                if not linked or linked['entity_id']!=s['entity_id'] or linked['axis']!=o['axis']:
                    errors.append({'code':'SIGNAL_ENTITY_AXIS_MISMATCH','external_id':e['external_id'],'axis':o['axis']})
            for rid in raw_refs(diag):
                if rid not in raw:errors.append({'code':'RAW_EVIDENCE_MISSING','external_id':e['external_id'],'axis':o['axis']})
                elif (raw[rid].get('payload') or {}).get('entity_id') not in {None,s['entity_id']}:
                    errors.append({'code':'BASELINE_ENTITY_MISMATCH','external_id':e['external_id'],'axis':o['axis']})
        records.append({'domain':e['domain'],'external_id':e['external_id'],'name':e['name'],'publish_status':s['publish_status'],'axes_available':p['axes_available'],'axis_status':p['axis_status'],'trust_grade':s['trust_grade'],'collection_status':(s.get('diagnostics') or {}).get('collection_status'),'trust_basis':(s.get('diagnostics') or {}).get('trust_basis')})
    superseded_rankings=0
    for r in ranks:
        s=sm.get(r['entity_id']);e=entities.get(r['entity_id'],{})
        if s and s['publish_status'] in {'shadow','withheld'} and r.get('published_at') is None:
            superseded_rankings+=1
            continue  # preserved non-public history, not a current publish candidate
        if not s or s['publish_status'] not in {'eligible','published'} or abs(float(s['score'])-float(r['score']))>.001 or e.get('domain')!=r['domain']:
            errors.append({'code':'RANK_SCORE_LINK_MISMATCH','entity_id':r['entity_id']})
    out={'as_of_date':as_of.isoformat(),'methodology_version':cfg['version'],'generated_at':now_kst().isoformat(),'ok':not errors,'errors':errors,'records':records,'linked_signal_count':len(signals),'linked_raw_count':len(raw),'superseded_nonpublic_rankings':superseded_rankings}
    path=ROOT/'data/audit/v5_lineage_latest.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k not in {'records','errors'}},ensure_ascii=False))
    if errors:raise RuntimeError(f'V5 lineage audit blocked: {len(errors)} errors')
    return out
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--date');a=p.parse_args();audit(SupabaseRest(),dt.date.fromisoformat(a.date) if a.date else now_kst().date())
