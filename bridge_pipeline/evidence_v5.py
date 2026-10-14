"""V5 evidence contract. Reference display values never enter ranking scores."""
from __future__ import annotations
import datetime as dt
import math
from .core import AXES, KST, stable_hash

POLICY_VERSION = 'v5.0-beta1'
# Source-specific renewal windows; annual baseline remains distinct from news.
SOURCE_TTL = {'google_news_rss':28, 'youtube_data_api':2, 'opendart':90,
              'opendart_financials':400, 'academyinfo':400,
              'gov_official_evaluations':400, 'ent_public_interest':28}

def day(value):
    if not value: return None
    try:
        s=str(value)
        if len(s)==10: return dt.date.fromisoformat(s)
        t=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
        return t.astimezone(KST).date() if t.tzinfo else t.date()
    except (ValueError,TypeError): return None

def collection_states(runs, as_of):
    """Newest completed target-level run wins. Legacy success is not target proof."""
    states={}
    for run in sorted(runs,key=lambda r:str(r.get('started_at') or ''),reverse=True):
        if not run.get('finished_at') or run.get('status') not in {'success','partial','failed'}: continue
        start,end=day(run.get('window_start')),day(run.get('window_end'))
        if (run.get('diagnostics') or {}).get('observation_as_of')!=as_of.isoformat() and (not start or not end or not start<=as_of<end): continue
        for entity_id, state in (run.get('diagnostics') or {}).get('entity_results',{}).items():
            states.setdefault((entity_id,run.get('source_id')),state)
    return states

def valid_signal(signal, as_of):
    occurred=day(signal.get('occurred_at'))
    expiry=day(signal.get('expires_at'))
    ttl=SOURCE_TTL.get(signal.get('source_id'),28)
    return bool(occurred and occurred<=as_of and (as_of-occurred).days<ttl and (not expiry or as_of<expiry))

def unique_signals(signals, raw_by_id):
    """One source content/axis/type. Syndicated titles share an event signature."""
    import re
    unique={}
    for s in signals:
        raw=raw_by_id.get(s.get('raw_item_id'),{})
        title=re.sub(r'\s+-\s+[^-]{2,40}$','',raw.get('title') or '').casefold()
        title=re.sub(r'[^0-9a-z가-힣]+',' ',title).strip()
        content=stable_hash(title,day(s.get('occurred_at'))) if title else s.get('raw_item_id') or s.get('id')
        key=(s.get('entity_id'),content,s.get('axis'),s.get('signal_type'))
        if key not in unique or float(s.get('confidence') or 0)>float(unique[key].get('confidence') or 0):
            unique[key]={**s,'event_content_key':content}
    return list(unique.values())

def profile(observations, as_of):
    by_axis={o['axis']:o for o in observations if o.get('axis') in AXES}
    values={}; states={}; dates={}
    for axis in AXES:
        o=by_axis.get(axis,{})
        diag=o.get('diagnostics') or {}
        value=o.get('score')
        valid=value is not None and o.get('status') in {'measured','carried'} and math.isfinite(float(value))
        values[axis]=round(float(value),1) if valid else 50.0
        states[axis]='maintained' if valid and o.get('status')=='carried' else 'observed' if valid else 'reference'
        dates[axis]=diag.get('evidence_date') or (diag.get('flow') or {}).get('evidence_date')
    return {'axis_scores':values,'axis_status':states,'axis_evidence_dates':dates,
            'axes_available':sum(v!='reference' for v in states.values()),
            'reference_axes_count':sum(v=='reference' for v in states.values())}

def comparison(current, previous):
    if not previous: return 'baseline_pending'
    if current.get('methodology_version')!=previous.get('methodology_version'): return 'methodology_changed'
    a,b=set(current.get('axes_used') or []),set(previous.get('axes_used') or [])
    if a==b: return 'same_scope'
    if b<a: return 'scope_expanded'
    if a<b: return 'scope_reduced'
    return 'scope_changed'

def event_activity(events, as_of, window_start=None, window_end=None):
    """Only accepted event units, once; platform level snapshots are not events."""
    unique={}
    for e in events:
        if e.get('review_status') not in {'auto','approved'}:continue
        if window_start and window_end:
            try:occurred=dt.datetime.fromisoformat(str(e.get('occurred_at')).replace('Z','+00:00'))
            except (ValueError,TypeError):continue
            if not occurred.tzinfo:continue
            if not window_start<=occurred<window_end:continue
        elif day(e.get('occurred_at'))!=as_of:continue
        key=(e.get('entity_id'),e.get('event_key'))
        amount=max(0,float(e.get('action_strength') or 0))*max(0,float(e.get('confidence') or 0))
        unique[key]=max(unique.get(key,0),amount)
    out={}
    for (eid,_),value in unique.items():out[eid]=out.get(eid,0)+value
    return out

def weighted_level(rows):
    valid=[r for r in rows if r.get('score') is not None]
    pairs=[(float(r['score']),max(.01,float(r.get('confidence_score') or 0)/100)) for r in valid]
    return round(sum(v*w for v,w in pairs)/sum(w for _,w in pairs),2) if pairs else None

def carry_valid(observations, as_of, current_keys):
    """Carry only last observed values; a carried date never restarts its TTL."""
    chosen={}
    for o in sorted(observations,key=lambda r:r['as_of_date'],reverse=True):
        k=(o['entity_id'],o['axis'])
        if k in chosen or k in current_keys or o.get('score') is None or o.get('status') not in {'measured','carried'}:continue
        diag=o.get('diagnostics') or {}
        source=diag.get('source_id')
        if not source:continue  # merged news/official rows cannot become new baselines
        anchor=day(diag.get('evidence_date') or diag.get('validity_anchor') or o['as_of_date'])
        ttl=SOURCE_TTL.get(source,28)
        expires=day(diag.get('valid_until')) or anchor+dt.timedelta(days=ttl)
        if as_of>=expires:continue
        chosen[k]={**o,'as_of_date':as_of.isoformat(),'status':'carried',
                   'freshness_days':max(0,(as_of-anchor).days),
                   'diagnostics':{**diag,'validity_anchor':anchor.isoformat(),'valid_until':expires.isoformat(),'policy_version':POLICY_VERSION}}
    return list(chosen.values())
