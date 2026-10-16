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
VERSION='publicity-rules-2.0'
PUBLIC_FIELDS=('as_of_date','domain','external_id','name','rank','score','daily_index','weekly_index','last_week_index','wow_delta','axis_scores','axis_status','observed_days','collection_ok_days','new_evidence_days','trust_grade','activity_points','activity_period','daily_activity_points','comparison_status','methodology_version','observation_window_end')
DOMAIN_LABELS={
    'CPR':{'scope':'기업','entity':'기업','distribution':'기업별','experience':'기업 경험 전반','ethics':'대상의 도덕성·윤리성'},
    'GOV':{'scope':'공공기관·지자체','entity':'대상','distribution':'공공 대상별','experience':'공공서비스 경험 전반','ethics':'기관의 윤리성·책무성'},
    'UNI':{'scope':'대학','entity':'대학','distribution':'대학별','experience':'대학 경험 전반','ethics':'기관의 윤리성·책무성'},
    'ENT':{'scope':'대중문화·인물','entity':'인물','distribution':'대중문화·인물별','experience':'활동 전반','ethics':'대상의 도덕성·윤리성'},
}

def korean_date(value):
    d=dt.date.fromisoformat(value)
    return f'{d.year}년 {d.month}월 {d.day}일'

def has_final_consonant(value):
    for char in reversed(value):
        code=ord(char)
        if 0xAC00<=code<=0xD7A3:return (code-0xAC00)%28!=0
    return False

def subject(value):
    return value+('이' if has_final_consonant(value) else '가')

def topic(value):
    return value+('은' if has_final_consonant(value) else '는')

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
        if sum(state in ('observed','maintained') for state in r['axis_status'].values())<2:raise ValueError('Insufficient measured axes in public input')
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
    lower=members[max(1,len(members)//2):] or members
    candidates=[r for r in lower if usable(r,'D') and usable(r,'E')]
    other=max(candidates,key=lambda r:(r['axis_scores']['D']+r['axis_scores']['E'],r['external_id'])) if candidates else members[-1]
    activity=max(members,key=lambda r:float(r.get('activity_points') or 0))
    total=float(activity.get('activity_points') or 0)
    labels=DOMAIN_LABELS[domain]
    date_count=len(dates)
    date_word='날짜' if date_count==1 else '개 날짜'
    title=f"{leader['name']} {leader['score']:.1f}점… {domain}, 선두의 수치 뒤에 남은 연결 과제"
    if candidates:
        d_score=other['axis_scores']['D'];e_score=other['axis_scores']['E']
        relation=(f"경험은 {d_score:.1f}점인 반면, 책임·지속은 {e_score:.1f}점으로 더 높게 나타났다." if e_score>d_score else
                  f"경험은 {d_score:.1f}점인 반면, 책임·지속은 {e_score:.1f}점에 머물렀다." if e_score<d_score else
                  f"경험과 책임·지속은 각각 {d_score:.1f}점으로 같은 수준을 보였다.")
        profile_text=(f"공개 순위 {other['rank']}위인 {other['name']}에서는 또 다른 성격의 관계 구성이 나타났다. {relation} "
                      f"이 두 수치를 나란히 비교하면 총점이라는 단일 지표에 가려진 대외 접점의 결을 읽을 수 있다. 다만 이는 공개 자료로 포착한 관계의 프로필일 뿐, 실제 {labels['experience']}이나 {labels['ethics']}을 직접 판정한 결과는 아님을 유의해야 한다.")
    else:
        profile_text=(f"공개 순위 하위권인 {other['name']} 역시 총점 하나의 수치만으로 설명되지 않는다. 다만 현재 확보된 자료상으로는 경험과 책임·지속의 근거를 함께 비교할 하위권 표본이 충분하지 않다. "
                      "순위가 낮다는 이유로 모든 대외 접점이 취약하다고 속단하거나, 반대로 객관적으로 확인되지 않은 잠재력을 임의로 부여해서는 안 된다.")
    sections=[{'heading':'현상 제시와 순위 이면의 구성','paragraphs':[
      f"{subject(leader['name'])} {korean_date(snapshot['period_through'])} 기준 {domain}({labels['scope']}) 공개 순위에서 선두에 올랐다. 시그널브릿지(SignalBridge) BRIDGE 브랜드평판지수 INDEX에 따르면, {leader['name']}의 일별 지수는 {leader['score']:.1f}점이다. 이번에 공개 요건을 충족한 {len(members)}개 대상의 평균은 {mean:.1f}점으로 집계됐다. 단, 이 평균은 이번 공개 집합에 한정된 값일 뿐, 해당 분야 전체의 절대적 수준을 대변하지 않는다.",
      f"눈길을 끄는 대목은 순위 그 자체보다 그 내부의 구성이다. {topic(leader['name'])} 유효 근거가 확인된 축 중에서 {AXES[high]} {leader['axis_scores'][high]:.1f}점, {AXES[low]} {leader['axis_scores'][low]:.1f}점을 기록했다. 이처럼 같은 선두권이라도 공중과 만나는 접점의 결은 서로 다르다. 단순히 ‘선두’라는 위치만으로 관심·반응·경험·신뢰가 고르게 연결되어 있다고 단정하기 어려운 이유가 여기에 있다."]},
      {'heading':'선두 밖에서도 읽히는 관계의 차이','paragraphs':[
      profile_text,
      '이러한 데이터의 차이는 순위라는 단편적 서사를 지우기보다, 오히려 현상을 입체적으로 읽는 시야를 넓혀준다. 상위권 안에서도 연결 고리가 덜 확인된 지점을 발견할 수 있고, 개별 대상마다 주목해야 할 고유한 관계 구성이 있음을 알 수 있다. 결국 한 축의 수치만으로 다른 축의 변화 원인을 단정하거나 향후 순위 상승을 예고하는 것은 경계해야 한다.']},
      {'heading':'활동의 크기와 평판의 방향은 다른 신호','paragraphs':[
      f"활동량 측면에서는 {subject(activity['name'])} 이번 공개 집합에서 가장 높은 수치({total:,.1f}P)를 기록했다. 이는 새롭게 포착된 유효 사건과 행동이 특정 {labels['entity']}에 얼마나 집중되었는지를 보여주는 지표다. 그러나 활동량이 많다는 사실 자체가 곧 우호적이거나 긍정적인 반응이 많았음을 의미하지는 않는다. 평판의 질적 수준과 활동의 양적 총량을 함께 고찰할 때 비로소 동일한 점수 뒤에 숨겨진 입체적 움직임이 포착된다." if total>0 else '이번 공개 대상에서는 당주 유효 활동 포인트가 기록되지 않았다. 이는 실제 활동이 전혀 없었다는 증명이 아니라, 설정된 관측·검수 범위에서 포인트로 인정된 활동이 없다는 뜻이다. 기존 자료가 평가 기반으로 유지되는 것과 새로운 활동이 발생하는 것은 구분된다.',
      f"향후 관찰의 초점은 지표의 숫자가 채워지는 속도가 아니라, 그 연결의 실질적 내용에 맞춰져야 한다. 현재 {AXES[strong]} 축은 {coverage[strong]}개 대상에서 유효 근거가 확인되는 반면, {AXES[weak]} 축은 {coverage[weak]}개에 그친다. 그렇다고 데이터가 확보되지 않은 접점을 곧바로 ‘부정적 상태’로 해석해서는 곤란하다. 새로운 근거 데이터가 유입될 때는 실제 평판의 변화와 시스템적 평가 범위의 확대를 엄밀히 구분해 고찰할 필요가 있다.",
      f"이번 분석은 {korean_date(snapshot['period_from'])}부터 {korean_date(snapshot['period_through'])}까지 실제 유효 데이터가 확보된 {date_count}{date_word}의 시계열적 흐름을 다루고 있다. 따라서 현재의 일별 위치를 곧바로 주간 확정 결과로 일반화해서는 안 된다. {leader['name']}의 선두 기록과 {labels['distribution']} 분포는 단순한 우열을 가리기 위한 것이 아니라, {domain} 영역에서 데이터 유입 속도와 관계 범위(B·R·I·D·G·E)가 어떻게 드러나는지를 보여주는 하나의 단면이다. 동일한 기준의 관측이 누적될 때 오늘의 관계 구성이 이어지는지, 어느 접점이 달라지는지를 추적하는 것이 BRIDGE PUBLICITY가 지향하는 데이터 해석의 핵심이다."]}]
    profiles=[]
    for r in [leader,other]:
        profiles.append({'name':r['name'],'axes':r['axis_scores'],'states':r['axis_status']})
    table=[{'rank':r['rank'],'name':r['name'],'daily':r['score'],'weekly':r.get('weekly_index'),'activity':r.get('activity_points'),'trust':r['trust_grade']} for r in members[:5]]
    return {'title':title,'standfirst':f"{domain} 공개 적격 {len(members)}개 대상의 위치·관계 구성·관측 범위를 함께 읽는 BRIDGE 분석.",'sections':sections,'table':table,'profiles':profiles,'coverage':coverage,'eligible_count':len(members),'observation_days':len(dates)}

def articles_for(history,publication_date,example=False,example_domain='CPR'):
    spec=edition(publication_date);snapshot,digest=freeze(history,spec)
    return articles_from_snapshot(snapshot,digest,spec,example,example_domain)

def articles_from_snapshot(snapshot,digest,spec,example=False,example_domain='CPR'):
    """Render a previously frozen and verified input without changing its facts.

    This recovery path exists for explicit editorial corrections. The caller must
    provide the original snapshot digest; it does not fetch or infer missing data.
    """
    snapshot=json.loads(json.dumps(snapshot,ensure_ascii=False))
    if example:
        snapshot['rows']=[r for r in snapshot['rows'] if r['domain']==example_domain]
        digest=hashlib.sha256(json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    domains=(example_domain,) if example else ('ALL',) if spec['slot']=='OVERALL' else DOMAINS
    articles=[]
    for domain in domains:
        if domain=='ALL':
            parts={d:domain_content(snapshot,d) for d in DOMAINS}
            content={'title':'한 주의 BRIDGE — 같은 순위표보다 다른 관계 구성을 읽다','standfirst':f"{spec['week']} CPR·GOV·UNI·ENT 통합 분석. 서로 다른 분야의 점수를 단순 우열로 바꾸지 않는다.",'sections':[], 'table':[], 'profiles':[], 'coverage':{},'eligible_count':sum(x['eligible_count'] for x in parts.values()),'observation_days':len({r['as_of_date'] for r in snapshot['rows']})}
            for d,p in parts.items():
                content['sections'].append({'heading':d+' — '+p['title'],'paragraphs':[p['sections'][0]['paragraphs'][0],p['sections'][1]['paragraphs'][1],p['sections'][1]['paragraphs'][0]]})
                content['table'].append({'domain':d,'eligible':p['eligible_count'],'observation_days':p['observation_days']})
            content['sections'].append({'heading':'다음 주에 확인할 신호','paragraphs':['네 영역은 관측 대상과 자료의 성격이 달라 점수의 단순 비교로 분야의 우열을 판단할 수 없다. 공통으로 살펴볼 것은 관심이 반응·경험·행동과 어떤 구성을 보이는지, 그리고 근거 범위가 유지되는지다.','이번 종합본은 전주에 실제로 관측된 자료만 사용한다. 날짜가 비어 있거나 새 방법론의 비교 이력이 짧은 경우에는 한 주 전체의 변화나 지속성을 확정하지 않는다.']})
        else:content=domain_content(snapshot,domain)
        payload={**content,'template_version':VERSION,'data_from':snapshot['period_from'],'data_through':snapshot['period_through'],'methodology_version':snapshot['methodology_version'],'limitations':['공개 적격 대상만 포함하며, 비공개 대상이나 전체 공중을 대표하지 않습니다.','참조 축의 숫자는 대상별 평가값이 아니며 기사에서 강점·약점 판정에 사용하지 않습니다.','자료 유형과 관측 범위에 따른 대리변수의 한계가 있습니다. 인과관계나 미래 성과를 확정하지 않습니다.'],'source_url':'https://bridgebrand.co.kr','frozen_at':dt.datetime.now(KST).isoformat()}
        if example:payload['revision_note']='기사체로 다듬은 샘플입니다. 10월 14일의 공개 수치를 사용했습니다.'
        if example:payload['standfirst']='샘플 · 실제 10월 14일 공개 데이터를 바탕으로 구성한 형식 예시입니다. 정식 발행본이 아닙니다. '+payload['standfirst']
        article={'id':f"{spec['week'].lower()}-{spec['slot'].lower()}-{domain.lower()}"+('-example' if example else ''),'issue_week':spec['week'],'slot':spec['slot'],'domain':domain,'scheduled_at':(dt.datetime.now(KST) if example else spec['scheduled_at']).isoformat(),'is_example':example,'payload':payload,'snapshot_hash':digest}
        articles.append(article)
    return articles,snapshot

def main():
    p=argparse.ArgumentParser();p.add_argument('--date');p.add_argument('--example',action='store_true');p.add_argument('--domain',choices=DOMAINS,default='CPR');p.add_argument('--dry-run',action='store_true');p.add_argument('--output');a=p.parse_args()
    today=dt.datetime.now(KST).date();pub=dt.date.fromisoformat(a.date) if a.date else today
    if not a.example and pub.weekday() not in (0,2,4):print('No PUBLICITY issue today');return
    if not a.example and pub<dt.date(2026,10,16):raise ValueError('Formal launch begins 2026-10-16')
    history=json.loads((ROOT/'site/data/history.json').read_text())
    articles,snapshot=articles_for(history,pub,a.example,a.domain)
    if a.output:Path(a.output).write_text(json.dumps({'articles':articles,'snapshot':snapshot},ensure_ascii=False))
    if not a.dry_run:
        from bridge_pipeline.core import SupabaseRest
        result=SupabaseRest().request('POST','rpc/bridge_stage_publicity',{'p_articles':articles,'p_snapshot':snapshot})
        print(json.dumps(result))
    else:print(json.dumps({'ids':[r['id'] for r in articles],'snapshot_hash':articles[0]['snapshot_hash'],'dry_run':True}))
if __name__=='__main__':main()
