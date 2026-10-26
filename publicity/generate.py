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
from reporting.interpretation import (
    PUBLICITY_BLOCKS, PUBLICITY_EDITORIAL_REFERENCES, assert_publishable, coverage_change, rank_movement,
    set_change,
)
from presentation.editorial_standard import audit_public_copy

ROOT=Path(__file__).resolve().parents[1]
KST=ZoneInfo('Asia/Seoul')
DOMAINS=('CPR','GOV','UNI','ENT')
AXES={'B':'도달','R':'반응','I':'정체성','D':'경험','G':'행동유발','E':'책임·지속'}
VERSION='publicity-rules-4.0-editorial'
EDITORIAL_STYLE_EFFECTIVE=dt.date(2026,10,21)
WEEK_CALENDAR_EFFECTIVE=dt.date(2026,10,19)
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
    calendar_end=start+dt.timedelta(days=6)
    y,w,_=end.isocalendar()
    return {'week':f'{y}-W{w:02d}','slot':'OVERALL' if overall else 'WED' if publication_date.weekday()==2 else 'FRI','from':start,'through':end,'calendar_from':start,'calendar_through':calendar_end,'scheduled_at':dt.datetime.combine(publication_date,dt.time(12),KST)}

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

def editorial_style(publication_date):
    """Alternate Sample 1 and Sample 3 on every Monday/Wednesday/Friday issue."""
    if publication_date<EDITORIAL_STYLE_EFFECTIVE:
        return 'legacy'
    issue_days=sum(
        1 for offset in range((publication_date-EDITORIAL_STYLE_EFFECTIVE).days+1)
        if (EDITORIAL_STYLE_EFFECTIVE+dt.timedelta(days=offset)).weekday() in (0,2,4)
    )
    return 'sample-1' if issue_days%2 else 'sample-3'

def axis_diagram(row):
    return {
        'title':f"{row['name']} BRIDGE 6축 프로필",
        'items':[
            {'axis':axis,'label':AXES[axis],'value':round(float(row['axis_scores'][axis]),1),
             'state':row['axis_status'][axis]}
            for axis in AXES if usable(row,axis)
        ],
    }

def editorial_block_content(content, limitations):
    """Bind the eight editorial functions to actual prose, not metadata labels."""
    paragraphs=[p for section in content.get('sections',()) for p in section.get('paragraphs',())]
    if not paragraphs:
        raise ValueError('PUBLICITY requires explanatory prose')
    def at(index):
        return paragraphs[min(index, len(paragraphs)-1)]
    return {
        'attention_headline':content.get('title',''),
        'fact_lead':' '.join(filter(None,(content.get('standfirst',''),at(0)))),
        'relationship_structure':at(1),
        'movement_reason':at(2),
        'evidence_scope':at(max(0,len(paragraphs)-3)),
        'domain_context':at(3),
        'interpretation_boundary':' '.join(limitations),
        'next_checkpoint':at(len(paragraphs)-1),
    }

def relationship_change(snapshot,leader):
    """Describe comparable axis movement without inventing an unavailable baseline."""
    prior=sorted(
        (r for r in snapshot['rows']
         if r['domain']==leader['domain']
         and r['external_id']==leader['external_id']
         and r['as_of_date']<leader['as_of_date']),
        key=lambda r:r['as_of_date'],
    )
    if not prior:
        return ('직전 비교 가능한 동일 대상의 축별 관측값이 이번 확인 범위에 포함되지 않아, '
                '이 회차는 현재 관계 구성과 근거 상태를 중심으로 읽는다.')
    previous=prior[-1]
    deltas=[]
    for axis in AXES:
        if usable(leader,axis) and usable(previous,axis):
            delta=round(float(leader['axis_scores'][axis])-float(previous['axis_scores'][axis]),1)
            deltas.append((axis,delta))
    state_changes=[
        axis for axis in AXES
        if leader.get('axis_status',{}).get(axis)!=previous.get('axis_status',{}).get(axis)
    ]
    if deltas:
        notable=sorted(deltas,key=lambda item:(-abs(item[1]),item[0]))[:2]
        movement=', '.join(
            f"{AXES[axis]} {'+' if delta>0 else ''}{delta:.1f}점"
            for axis,delta in notable
        )
        axis_text=f"직전 비교 가능한 관측값({korean_date(previous['as_of_date'])})과 대조한 주요 축 변화는 {movement}이다."
    else:
        axis_text='직전 회차와 직접 대조할 수 있는 동일 상태의 축이 없어 수치 변화를 확정하지 않는다.'
    if state_changes:
        scope_text=(
            f"동시에 {len(state_changes)}개 축의 근거 상태가 달라져, 실제 관계 변화와 확인 범위의 변화를 분리해 해석해야 한다."
        )
    else:
        scope_text='비교된 축의 근거 상태는 유지되어, 이번 변화는 동일한 확인 조건 안에서 읽을 수 있다.'
    return axis_text+' '+scope_text

def rank_and_set_change(snapshot,leader):
    dates=sorted({r['as_of_date'] for r in snapshot['rows'] if r['domain']==leader['domain']})
    if len(dates)<2:
        return '직전 동일 분야 비교집합이 없어 순위 이동의 원인을 확정하지 않는다.'
    previous_date=dates[-2]
    current=[r for r in snapshot['rows'] if r['domain']==leader['domain'] and r['as_of_date']==leader['as_of_date']]
    previous=[r for r in snapshot['rows'] if r['domain']==leader['domain'] and r['as_of_date']==previous_date]
    prior=next((r for r in previous if r['external_id']==leader['external_id']),None)
    movement=rank_movement(leader,prior)
    movement_text={
        'score_and_rank_rise':'대상 자체의 점수 상승과 상대 순위 상승이 함께 확인됐다.',
        'score_rise_without_rank_rise':'대상 점수는 상승했지만 상대 순위 상승으로 이어지지는 않았다.',
        'rank_rise_despite_score_fall':'대상 점수는 낮아졌지만 비교 대상의 움직임으로 상대 순위는 상승했다.',
        'score_and_rank_fall':'대상 점수와 상대 순위가 함께 낮아졌다.',
        'relative_move_with_static_score':'대상 점수는 같지만 비교 대상의 움직임으로 순위가 달라졌다.',
        'mixed_or_static':'점수와 순위는 서로 다른 방향 또는 정지 상태를 보였다.',
        'no_baseline':'동일 대상의 직전 비교값이 없어 이동 유형을 확정하지 않는다.',
    }[movement['type']]
    change=set_change(current,previous)
    set_text=(f"동시에 공개 비교집합은 {change['previous_size']}개에서 {change['current_size']}개로 달라져 집합 효과를 함께 확인해야 한다."
              if change['current_size']!=change['previous_size'] or change['entered'] or change['exited']
              else '공개 비교집합의 구성과 크기는 유지됐다.')
    coverage=coverage_change(current,previous)
    changed=[axis for axis,values in coverage.items() if values['delta']]
    coverage_text=(f"축별 유효 대상 수가 달라진 축은 {', '.join(changed)}이며, 해당 축의 변화는 관측 범위 효과와 분리해 읽는다."
                   if changed else '축별 유효 대상 수에는 변화가 확인되지 않았다.')
    return movement_text+' '+set_text+' '+coverage_text

def domain_content(snapshot,domain,style='legacy'):
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
    change_text=relationship_change(snapshot,leader)+' '+rank_and_set_change(snapshot,leader)
    title=(f"{leader['name']} 1위·{leader['score']:.1f}점… {domain}, 여섯 축이 설명한 이번 위치"
           if style=='sample-1' else
           f"{leader['name']} 1위, 같은 총점 안에서도 달랐던 {domain}의 여섯 축"
           if style=='sample-3' else
           f"{leader['name']} 1위·{leader['score']:.1f}점… {domain}, 강한 축과 추가 확인할 축")
    if candidates:
        d_score=other['axis_scores']['D'];e_score=other['axis_scores']['E']
        relation=(f"경험은 {d_score:.1f}점인 반면, 책임·지속은 {e_score:.1f}점으로 더 높게 나타났다." if e_score>d_score else
                  f"경험은 {d_score:.1f}점인 반면, 책임·지속은 {e_score:.1f}점에 머물렀다." if e_score<d_score else
                  f"경험과 책임·지속은 각각 {d_score:.1f}점으로 같은 수준을 보였다.")
        profile_text=(f"공개 순위 {other['rank']}위인 {other['name']}은 선두와 다른 6축 프로필을 보였다. {relation} "
                      f"두 수치를 함께 보면 총점만으로는 드러나지 않는 대외 접점의 차이를 확인할 수 있다. 다만 이는 공개자료로 관측한 프로필이며, 실제 {labels['experience']}이나 {labels['ethics']} 전체를 직접 판정한 결과는 아니다.")
    else:
        profile_text=(f"공개 순위 하위권인 {other['name']} 역시 총점 하나의 수치만으로 설명되지 않는다. 다만 현재 확인 범위에서는 경험과 책임·지속을 같은 조건으로 나란히 제시할 하위권 사례가 확인되지 않았다. "
                      "순위가 낮다는 이유로 모든 대외 접점이 취약하다고 속단하거나, 반대로 객관적으로 확인되지 않은 잠재력을 임의로 부여해서는 안 된다.")
    sections=[{'heading':'이번 순위와 비교 조건','paragraphs':[
      f"{subject(leader['name'])} {korean_date(snapshot['period_through'])} 기준 {domain}({labels['scope']}) 공개 순위 1위로 관측됐다. 시그널브릿지(SignalBridge) BRIDGE 브랜드평판지수 INDEX에 따르면, {leader['name']}의 일별 지수는 {leader['score']:.1f}점이다. 이번 회차 T100 공개 요건을 충족한 비교 집합은 {len(members)}개 대상이며 평균은 {mean:.1f}점으로 집계됐다. 대상 구성은 기준일과 관측 상태에 따라 달라질 수 있다. 단, 이 평균은 이번 공개 집합에 한정된 값일 뿐, 해당 분야 전체의 절대적 수준을 대변하지 않는다.",
      f"순위 안쪽에서는 축별 차이가 먼저 보인다. {topic(leader['name'])} 유효 근거가 확인된 축 중에서 {AXES[high]} {leader['axis_scores'][high]:.1f}점, {AXES[low]} {leader['axis_scores'][low]:.1f}점을 기록했다. {change_text} 같은 선두권 안에서도 공중에게 발견되고 반응을 얻으며 경험과 행동으로 이어지는 방식은 다를 수 있다. 따라서 ‘선두’라는 위치만으로 모든 축이 고르게 높다고 해석하지 않는다."]},
      {'heading':'상위권 안에서 달라지는 6축 프로필','paragraphs':[
      profile_text,
      '이 차이는 순위를 무의미하게 만들지 않는다. 오히려 같은 순위표 안에서도 대상별 강점과 확인이 덜 된 축이 다르다는 사실을 보여준다. 따라서 한 축의 수치만으로 다른 축의 변화 원인을 단정하거나 다음 순위를 예측해서는 안 된다.']},
      {'heading':'활동의 크기와 평판의 방향은 다른 신호','paragraphs':[
      f"활동량에서는 {subject(activity['name'])} 이번 공개 집합에서 가장 높은 {total:,.1f}P를 기록했다. 이 값은 검증·귀속·중복 제거를 거친 사건과 행동의 규모다. 많고 적음은 움직임의 크기를 설명하지만 그 방향이 긍정적인지는 말해주지 않는다. 따라서 Activity Points와 BRIDGE INDEX를 함께 보되 서로 대신하는 값으로 사용하지 않는다." if total>0 else '이번 공개 대상에서는 당주 유효 활동 포인트가 기록되지 않았다. 이는 실제 활동이 전혀 없었다는 증명이 아니라, 설정된 관측·검수 범위에서 포인트로 인정된 활동이 없다는 뜻이다. 0P만으로 긍정 또는 부정의 방향을 판단하지 않으며, 기존 평가 기반의 유지와 새로운 활동의 발생을 구분해 읽는다.']},
      {'heading':'관측 범위와 다음 해석의 경계','paragraphs':[
      f"현재 {AXES[strong]} 축은 {coverage[strong]}개 대상에서 유효 근거가 확인됐고, {AXES[weak]} 축은 {coverage[weak]}개에서 확인됐다. 이 차이는 대상의 좋고 나쁨보다 이번 회차에서 축별 근거가 얼마나 확보됐는지를 먼저 설명한다. 새 자료가 유입된 다음 회차에는 실제 평판 변화와 관측 범위 확대를 나누어 확인해야 한다.",
      f"이번 분석은 {korean_date(snapshot['period_from'])}부터 {korean_date(snapshot['period_through'])}까지 유효 데이터가 확보된 {date_count}{date_word}을 다룬다. 현재의 일별 위치를 주간 확정 결과로 일반화하지 않는 이유다. {leader['name']}의 선두 기록과 {labels['distribution']} 분포는 우열 판정이 아니라, {domain}에서 어떤 축의 근거가 빠르게 들어왔고 어떤 접점이 아직 덜 관측됐는지를 보여주는 한 장면이다. 같은 기준의 관측이 쌓일수록 일시적 움직임과 반복되는 평판 특성을 더 정확히 구분할 수 있다."]}]
    if style in ('sample-1','sample-3'):
        sections.append({'heading':'BRIDGE가 남기는 다음 질문','paragraphs':[
          f"이번 {domain} 순위는 독자의 시선을 여는 출발점이다. 다음 회차에서는 {leader['name']}의 숫자뿐 아니라, 현재 높게 관측된 {AXES[high]} 축과 상대적으로 낮은 {AXES[low]} 축이 같은 방향으로 움직이는지 확인한다. 두 축이 다르게 움직이면 종합점수 하나만으로 설명하기 어려운 변화가 있다는 뜻이므로, 새 근거와 사건 귀속을 다시 살펴봐야 한다.",
          f"BRIDGE는 누가 더 많이 언급됐는지에 머물지 않고, 발견·반응·기억·경험·행동·책임이 어떤 연결을 이루는지 반복해서 관찰한다. 다음 분석에서는 새 사건의 발생, 기존 사건의 반복 노출, 실제 축 변화, 확인 범위의 확대를 분리해 살필 예정이다. 이 구분이 유지될 때 {leader['name']}의 1위는 단순한 서열이 아니라 관계를 이해하기 위한 정보가 된다."]})
    profiles=[]
    for r in [leader,other]:
        profiles.append({'name':r['name'],'axes':r['axis_scores'],'states':r['axis_status']})
    table=[{'rank':r['rank'],'name':r['name'],'daily':r['score'],'weekly':r.get('weekly_index'),'activity':r.get('activity_points'),'trust':r['trust_grade']} for r in members[:5]]
    return {'title':title,'standfirst':f"{domain} 공개 적격 {len(members)}개 대상의 순위·6축 프로필·활동량·관측 범위를 같은 기준에서 읽은 BRIDGE 분석.",'sections':sections,'table':table,'profiles':profiles,'diagram':axis_diagram(leader),'coverage':coverage,'eligible_count':len(members),'observation_days':len(dates),'leader':leader}

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
    style=editorial_style(spec['scheduled_at'].date())
    domains=(example_domain,) if example else ('ALL',) if spec['slot']=='OVERALL' else DOMAINS
    articles=[]
    for domain in domains:
        if domain=='ALL':
            parts={d:domain_content(snapshot,d,style) for d in DOMAINS}
            overall_title=('한 주의 BRIDGE — 같은 순위표보다 다른 관계 구성을 읽다'
                           if style=='sample-1' else
                           "‘1위’는 같았지만 이유는 달랐다 — 한 주의 네 가지 관계")
            content={'title':overall_title,'standfirst':f"{spec['week']} CPR·GOV·UNI·ENT 통합 분석. 순위는 주목의 입구로, 축별 구조와 변화 원인은 해석의 본체로 읽는다.",'sections':[], 'table':[], 'profiles':[], 'diagram':{'title':'영역별 선두 관계 구조','items':[]}, 'coverage':{},'eligible_count':sum(x['eligible_count'] for x in parts.values()),'observation_days':len({r['as_of_date'] for r in snapshot['rows']})}
            for d,p in parts.items():
                paragraphs=[p['sections'][0]['paragraphs'][0],p['sections'][1]['paragraphs'][1],p['sections'][1]['paragraphs'][0]]
                if style in ('sample-1','sample-3'):
                    paragraphs.append(p['sections'][-1]['paragraphs'][0])
                content['sections'].append({'heading':d+' — '+p['title'],'paragraphs':paragraphs})
                content['table'].append({'domain':d,'eligible':p['eligible_count'],'observation_days':p['observation_days']})
                content['profiles'].append({'name':d+' · '+p['profiles'][0]['name'],'axes':p['profiles'][0]['axes'],'states':p['profiles'][0]['states']})
                lead=p['leader'];valid=[a for a in AXES if usable(lead,a)]
                strongest=max(valid,key=lambda a:lead['axis_scores'][a])
                content['diagram']['items'].append({'axis':d,'label':lead['name']+' · '+AXES[strongest],'value':round(float(lead['axis_scores'][strongest]),1),'state':lead['axis_status'][strongest]})
            content['sections'].append({'heading':'다음 주에 확인할 신호','paragraphs':['네 영역은 관측 대상과 자료의 성격이 달라 점수의 단순 비교로 분야의 우열을 판단할 수 없다. 공통으로 살펴볼 것은 관심이 반응·경험·행동과 어떤 구성을 보이는지, 그리고 근거 범위가 유지되는지다.','이번 종합본은 전주에 실제로 관측된 자료만 사용한다. 날짜가 비어 있거나 새 방법론의 비교 이력이 짧은 경우에는 한 주 전체의 변화나 지속성을 확정하지 않는다.']})
        else:content=domain_content(snapshot,domain,style)
        limitations=['공개 적격 대상만 포함하며, 비공개 대상이나 전체 공중을 대표하지 않습니다.','참조 축의 숫자는 대상별 평가값이 아니며 기사에서 강점·약점 판정에 사용하지 않습니다.','자료 유형과 관측 범위에 따른 대리변수의 한계가 있습니다. 인과관계나 미래 성과를 확정하지 않습니다.']
        payload={**content,'editorial_style':style,'editorial_blocks':list(PUBLICITY_BLOCKS),'editorial_block_content':editorial_block_content(content,limitations),'editorial_reference_ids':list(PUBLICITY_EDITORIAL_REFERENCES),'visual_contract':['table','profile-figure','relationship-diagram'],'template_version':VERSION,'data_from':snapshot['period_from'],'data_through':snapshot['period_through'],'methodology_version':snapshot['methodology_version'],'limitations':limitations,'source_url':'https://bridgebrand.co.kr','frozen_at':dt.datetime.now(KST).isoformat()}
        if example:payload['revision_note']='기사체로 다듬은 샘플입니다. 10월 14일의 공개 수치를 사용했습니다.'
        if example:payload['standfirst']='샘플 · 실제 10월 14일 공개 데이터를 바탕으로 구성한 형식 예시입니다. 정식 발행본이 아닙니다. '+payload['standfirst']
        assert_publishable(payload)
        language_warnings=audit_public_copy(json.dumps(payload,ensure_ascii=False))
        fatal=[warning for warning in language_warnings if warning.startswith('과장·모호 표현:')]
        if fatal:raise ValueError('PUBLICITY language validation failed: '+'; '.join(fatal))
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

