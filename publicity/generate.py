"""Freeze an allowlisted public snapshot and stage validated scheduled articles.
No LLM, private scoring formula or raw ledger is used by the writer.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import math
import statistics
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
KST=ZoneInfo('Asia/Seoul')
DOMAINS=('CPR','GOV','UNI','ENT')
AXES={'B':'도달','R':'반응','I':'정체성','D':'경험','G':'행동유발','E':'책임·지속'}
VERSION='publicity-rules-1.0'
PUBLIC_FIELDS=('as_of_date','domain','external_id','name','rank','score','daily_index','weekly_index','last_week_index','wow_delta','axis_scores','axis_status','observed_days','collection_ok_days','new_evidence_days','trust_grade','activity_points','activity_period','daily_activity_points','comparison_status','methodology_version','observation_window_end')

def edition(publication_date):
    if publication_date.weekday() not in (0,2,4):raise ValueError('PUBLICITY is issued on Monday, Wednesday and Friday only')
    overall=publication_date.weekday()==0
    end=publication_date-dt.timedelta(days=1) if overall else publication_date
    start=end-dt.timedelta(days=end.weekday())
    y,w,_=end.isocalendar()
    return {'week':f'{y}-W{w:02d}','slot':'OVERALL' if overall else 'WED' if publication_date.weekday()==2 else 'FRI','from':start,'through':end,'scheduled_at':dt.datetime.combine(publication_date,dt.time(12),KST)}

def freeze(history, spec):
    through=spec['through'].isoformat();start=spec['from'].isoformat()
    candidates=[r for r in history.get('rankings',[]) if start<=r.get('as_of_date','')<=through and r.get('domain') in DOMAINS and r.get('ranking_type')=='T100' and r.get('history_type')!='historical_weekly_backfill' and 'v5' in r.get('methodology_version','')]
    rows=[{k:r.get(k) for k in PUBLIC_FIELDS} for r in candidates]
    rows.sort(key=lambda r:(r['as_of_date'],r['domain'],r['external_id']))
    if not rows:raise ValueError('No verified v5 public observation data in issue period')
    versions={r['methodology_version'] for r in rows}
    if len(versions)!=1:raise ValueError('Mixed methodologies require editorial review')
    keys=set()
    for r in rows:
        key=(r['domain'],r['external_id'],r['as_of_date'])
        if key in keys:raise ValueError('Duplicate target/date in editorial input')
        keys.add(key)
        if r['score'] is None or not math.isfinite(float(r['score'])) or not 0<=float(r['score'])<=100:raise ValueError('Invalid public score')
        if set(r.get('axis_status') or {})!=set(AXES):raise ValueError('Missing evidence-state contract')
        if any(state not in ('observed','maintained','reference') for state in r['axis_status'].values()):raise ValueError('Unvalidated estimated axis requires editorial review')
        for axis in AXES:
            value=(r.get('axis_scores') or {}).get(axis)
            if not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=100:raise ValueError('Invalid axis value')
        for field in ('weekly_index','last_week_index'):
            value=r.get(field)
            if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=100):raise ValueError('Invalid period level')
        value=r.get('activity_points')
        if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value) or value<0):raise ValueError('Invalid activity amount')
    # Do not turn yesterday's snapshot into today's scheduled analysis.
    for domain in DOMAINS:
        if not any(r['domain']==domain and r['as_of_date']==through for r in rows):raise ValueError(f'{domain}: required observation date {through} missing; publication held')
    snapshot={'schema':'publicity-input-1','period_from':start,'period_through':through,'methodology_version':next(iter(versions)),'rows':rows}
    digest=hashlib.sha256(json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return snapshot,digest

def usable(row,axis):
    return row.get('axis_status',{}).get(axis) in ('observed','maintained') and isinstance(row.get('axis_scores',{}).get(axis),(int,float))

def summary(rows,domain,through):
    members=sorted([r for r in rows if r['domain']==domain and r['as_of_date']==through],key=lambda r:(-float(r['score']),r['external_id']))
    if not members:raise ValueError('No public members')
    coverage={a:sum(usable(r,a) for r in members) for a in AXES}
    mean=round(statistics.mean(float(r['score']) for r in members),1)
    return members,coverage,mean

def domain_content(snapshot,domain):
    members,coverage,mean=summary(snapshot['rows'],domain,snapshot['period_through']);leader=members[0]
    weak=min(AXES,key=lambda a:coverage[a]);strong=max(AXES,key=lambda a:coverage[a])
    dates=sorted({r['as_of_date'] for r in snapshot['rows'] if r['domain']==domain})
    axes=[a for a in AXES if usable(leader,a)]
    high=max(axes,key=lambda a:leader['axis_scores'][a]) if axes else None
    low=min(axes,key=lambda a:leader['axis_scores'][a]) if axes else None
    title=f"{leader['name']} {leader['score']:.1f}점… {domain}, 순위 너머 {AXES[strong]}의 근거를 읽다"
    sections=[{'heading':'현재 위치 — 높은 점수와 충분한 관측은 다른 질문이다','paragraphs':[
      f"{snapshot['period_through']} 기준 {domain} 공개 적격 대상은 {len(members)}개다. 선두 {leader['name']}의 일별 지수는 {leader['score']:.1f}점이며, 공개 대상의 일별 지수 평균은 {mean:.1f}점이다. 이 평균은 공개 적격 집합의 설명값으로, 전체 분야나 비공개 대상을 대표하지 않는다.",
      f"이번 기사는 {snapshot['period_from']}부터 {snapshot['period_through']}까지 중 실제 자료가 확보된 {len(dates)}개 날짜를 바탕으로 작성했다. 일별 순위를 주간 확정 순위로 바꾸어 소개하지 않으며, 분석 주차와 자료 마감일을 구분한다."]},
      {'heading':'여섯 축의 관계 — 강점과 관측 공백을 함께 보기','paragraphs':[
      f"{leader['name']}의 프로필에서는 유효 근거가 있는 축 중 {AXES[high]} {leader['axis_scores'][high]:.1f}점이 가장 높고, {AXES[low]} {leader['axis_scores'][low]:.1f}점이 가장 낮다. 이는 이 대상의 관측된 프로필 안에서 읽는 차이이며, 특정 행위가 다른 축을 변화시켰다는 인과관계는 아니다." if high else '대상별 축 해석에 필요한 근거를 추가 확인해야 한다.',
      f"공개 대상 가운데 {AXES[strong]}은 {coverage[strong]}개, {AXES[weak]}은 {coverage[weak]}개 대상에서 관측·유지 근거가 확인된다. 근거가 적다는 사실은 그 관계 요소가 나쁘다는 뜻이 아니다. 확보하지 못한 반응을 부정 반응으로, 경험 자료의 부재를 나쁜 경험으로 해석하지 않는다."]},
      {'heading':'순위 밖의 관찰 지점 — 다른 관계 구성을 찾다','paragraphs':[]},
      {'heading':'활동과 지속성 — 많이 발생한 일과 높은 평판을 분리하다','paragraphs':[
      f"이번 공개 대상에서 당주 활동 포인트가 가장 큰 대상은 {max(members,key=lambda r:float(r.get('activity_points') or 0))['name']}이다. 활동 포인트는 새로 포착한 유효 사건·행동의 총량이며, 일별·주간 지수의 평균 수준과 단위가 다르다. 활동이 많다는 이유만으로 긍정 평가나 책임 이행을 의미하지 않는다.",
      '새 기준에서 동일한 비교 조건과 충분한 주간 이력이 확보되기 전에는 전주 대비 상승·하락이나 장기 안정성을 단정하지 않는다. 다음 관측에서는 같은 축의 근거가 유지되는지, 새로운 축의 유입으로 평가 범위가 바뀌는지를 함께 확인할 필요가 있다.']}]
    lower=members[max(1,len(members)//2):] or members
    candidates=[r for r in lower if usable(r,'D') and usable(r,'E')]
    if candidates:
        other=max(candidates,key=lambda r:(r['axis_scores']['D']+r['axis_scores']['E'],r['external_id']))
        sections[2]['paragraphs']=[f"공개 순위 {other['rank']}위인 {other['name']}은 경험 {other['axis_scores']['D']:.1f}점, 책임·지속 {other['axis_scores']['E']:.1f}점의 프로필을 보인다. 선두권에 들지 않았더라도 이처럼 확인된 관계 요소를 별도로 읽을 수 있다. 이러한 축별 수치만으로 미래 순위 상승을 예측하지는 않는다."]
    else:
        other=members[-1]
        sections[2]['paragraphs']=[f"공개 순위 {other['rank']}위인 {other['name']} 역시 유효 근거가 있는 축의 구성과 관측 범위를 함께 보아야 한다. 현재 자료에서는 경험과 책임을 함께 비교할 하위권 사례가 충분하지 않아, 순위를 보완할 강점을 임의로 부여하지 않았다."]
    if max(float(r.get('activity_points') or 0) for r in members)<=0:
        sections[3]['paragraphs'][0]='이번 공개 대상에서는 당주 유효 활동 포인트가 기록되지 않았다. 이는 실제 활동이 전혀 없었다는 증명이 아니라, 설정된 관측·검수 범위에서 포인트로 인정된 활동이 없다는 뜻이다. 기존 공시나 공식 기초자료를 유지하는 것은 새로운 활동 포인트를 만들지 않는다.'
    profiles=[]
    for r in [leader,other]:
        profiles.append({'name':r['name'],'axes':r['axis_scores'],'states':r['axis_status']})
    table=[{'rank':r['rank'],'name':r['name'],'daily':r['score'],'weekly':r.get('weekly_index'),'activity':r.get('activity_points'),'trust':r['trust_grade']} for r in members[:5]]
    return {'title':title,'standfirst':f"{domain} 공개 적격 {len(members)}개 대상의 위치·관계 구성·관측 범위를 함께 읽는 BRIDGE 분석.",'sections':sections,'table':table,'profiles':profiles,'coverage':coverage,'eligible_count':len(members),'observation_days':len(dates)}

def articles_for(history,publication_date,example=False):
    spec=edition(publication_date);snapshot,digest=freeze(history,spec)
    if example:
        snapshot['rows']=[r for r in snapshot['rows'] if r['domain']=='CPR']
        digest=hashlib.sha256(json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    domains=('CPR',) if example else ('ALL',) if spec['slot']=='OVERALL' else DOMAINS
    articles=[]
    for domain in domains:
        if domain=='ALL':
            parts={d:domain_content(snapshot,d) for d in DOMAINS}
            content={'title':'한 주의 BRIDGE — 같은 순위표보다 다른 관계 구성을 읽다','standfirst':f"{spec['week']} CPR·GOV·UNI·ENT 통합 분석. 서로 다른 분야의 점수를 단순 우열로 바꾸지 않는다.",'sections':[], 'table':[], 'profiles':[], 'coverage':{},'eligible_count':sum(x['eligible_count'] for x in parts.values()),'observation_days':len({r['as_of_date'] for r in snapshot['rows']})}
            for d,p in parts.items():
                content['sections'].append({'heading':d+' — '+p['title'],'paragraphs':[p['sections'][0]['paragraphs'][0],p['sections'][1]['paragraphs'][1],p['sections'][2]['paragraphs'][0]]})
                content['table'].append({'domain':d,'eligible':p['eligible_count'],'observation_days':p['observation_days']})
            content['sections'].append({'heading':'다음 주에 확인할 신호','paragraphs':['네 영역은 관측 대상과 자료의 성격이 달라 점수의 단순 비교로 분야의 우열을 판단할 수 없다. 공통으로 살펴볼 것은 관심이 반응·경험·행동과 어떤 구성을 보이는지, 그리고 근거 범위가 유지되는지다.','이번 종합본은 전주에 실제로 관측된 자료만 사용한다. 날짜가 비어 있거나 새 방법론의 비교 이력이 짧은 경우에는 한 주 전체의 변화나 지속성을 확정하지 않는다.']})
        else:content=domain_content(snapshot,domain)
        payload={**content,'template_version':VERSION,'data_from':snapshot['period_from'],'data_through':snapshot['period_through'],'methodology_version':snapshot['methodology_version'],'limitations':['공개 적격 대상만 포함하며, 비공개 대상이나 전체 공중을 대표하지 않습니다.','참조 축의 숫자는 대상별 평가값이 아니며 기사에서 강점·약점 판정에 사용하지 않습니다.','자료 유형과 관측 범위에 따른 대리변수의 한계가 있습니다. 인과관계나 미래 성과를 확정하지 않습니다.'],'source_url':'https://bridgebrand.co.kr','frozen_at':dt.datetime.now(KST).isoformat()}
        if example:payload['revision_note']='예시 문장 검수본입니다. 표현을 교정했으며 수치와 입력 스냅샷은 동일합니다.'
        if example:payload['standfirst']='샘플 · 실제 10월 14일 공개 데이터를 바탕으로 구성한 형식 예시입니다. 정식 발행본이 아닙니다. '+payload['standfirst']
        article={'id':f"{spec['week'].lower()}-{spec['slot'].lower()}-{domain.lower()}"+('-example' if example else ''),'issue_week':spec['week'],'slot':spec['slot'],'domain':domain,'scheduled_at':(dt.datetime.now(KST) if example else spec['scheduled_at']).isoformat(),'is_example':example,'payload':payload,'snapshot_hash':digest}
        articles.append(article)
    return articles,snapshot

def main():
    p=argparse.ArgumentParser();p.add_argument('--date');p.add_argument('--example',action='store_true');p.add_argument('--dry-run',action='store_true');p.add_argument('--output');a=p.parse_args()
    today=dt.datetime.now(KST).date();pub=dt.date.fromisoformat(a.date) if a.date else today
    if not a.example and pub.weekday() not in (0,2,4):print('No PUBLICITY issue today');return
    if not a.example and pub<dt.date(2026,10,16):raise ValueError('Formal launch begins 2026-10-16')
    history=json.loads((ROOT/'site/data/history.json').read_text())
    articles,snapshot=articles_for(history,pub,a.example)
    if a.output:Path(a.output).write_text(json.dumps({'articles':articles,'snapshot':snapshot},ensure_ascii=False))
    if not a.dry_run:
        from bridge_pipeline.core import SupabaseRest
        result=SupabaseRest().request('POST','rpc/bridge_stage_publicity',{'p_articles':articles,'p_snapshot':snapshot})
        print(json.dumps(result))
    else:print(json.dumps({'ids':[r['id'] for r in articles],'snapshot_hash':articles[0]['snapshot_hash'],'dry_run':True}))
if __name__=='__main__':main()
