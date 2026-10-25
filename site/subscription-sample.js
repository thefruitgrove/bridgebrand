(function(){'use strict';
const AXES=['B','R','I','D','G','E'],N={B:'도달',R:'반응',I:'정체성',D:'경험',G:'행동유발',E:'책임·지속'};
const DATA={
 date:'2026-10-25',field:'ENT',pick:{name:'리센느',rank:6,previous_rank:5,daily:78.55,weekly:79.28,last:83.99,wow:-4.71,change:.07,activity:684,cumulative:1350,performance:81.63,trust:'D',axes:{B:68.2,R:100,I:100,D:40.2,G:73,E:15.3}},
 a:{name:'르세라핌',rank:40,previous_rank:40,daily:66.12,weekly:69.62,last:76.54,wow:-6.92,change:-.31,activity:240,cumulative:426,performance:73.08,trust:'D',axes:{B:68.3,R:100,I:41.6,D:15.9,G:32.5,E:28.2}},
 b:{name:'아일릿',rank:17,previous_rank:19,daily:70.09,weekly:72.24,last:78.15,wow:-5.91,change:-.51,activity:630,cumulative:702,performance:75.19,trust:'D',axes:{B:68,R:81.9,I:25.5,D:44.1,G:68.4,E:44.1}}
};
const q=new URLSearchParams(location.search),edition=['basic','standard','special'].includes(q.get('edition'))?q.get('edition'):'basic';
const pick=DATA.pick,entities=[pick,DATA.a,DATA.b],$=s=>document.querySelector(s),fmt=n=>Number(n).toFixed(2),sg=n=>`${n>=0?'▲':'▼'} ${Math.abs(n).toFixed(2)}`;
document.querySelectorAll('[data-edition]').forEach(a=>a.classList.toggle('active',a.dataset.edition===edition));
const config={basic:{meta:'BASIC BRIEFING',title:'리센느\nBRIDGE 기본 브리핑',deck:'한 대상의 핵심지표·6축·변화·활동량·근거 범위와 다음 질문을 빠르게 읽는 고정 샘플입니다.',contract:'BASIC · 단일 대상 독립 분석',copy:'이전 축약형의 정보 밀도를 계승하며 짧은 PUBLICITY까지 포함합니다.'},standard:{meta:'STANDARD · 23 PAGES',title:'리센느\nBRIDGE 일반 브리핑',deck:'리센느를 중심으로 르세라핌·아일릿을 동일 조건에서 비교하는 23페이지 기준본입니다.',contract:'STANDARD · MIN. 21 PAGES',copy:'POSITION READ 19개 해설, 활동량·평판 13개 해설과 주요 시각자료별 독립 설명을 포함합니다.'},special:{meta:'SPECIAL · 35 PAGES',title:'리센느\nBRIDGE 스페셜 브리핑',deck:'일반 브리핑 전체에 3일 동향·전략 제안·변화 원인 검증·이전 2주 PUBLICITY를 확장한 35페이지 고정 샘플입니다.',contract:'SPECIAL · MIN. 35 PAGES',copy:'향후 전략 제안을 핵심 가치로 두고, 사실·제한 해석·가설·권고를 구분합니다.'}}[edition];
document.title=`${pick.name} ${config.meta} 고정 샘플 — BRIDGE`;
$('#editionMeta').textContent=`ENT ${config.meta} · 2026.10.25`;$('#sampleTitle').innerHTML=config.title.replace('\n','<br>');$('#sampleDeck').textContent=config.deck;$('#contractName').textContent=config.contract;$('#contractCopy').textContent=config.copy;
$('#heroStats').innerHTML=[['ENT T100',`${pick.rank}위`,'동일 날짜 상대 위치'],['DAILY',fmt(pick.daily),'당일 관계 수준'],['WEEKLY',fmt(pick.weekly),'진행 중 주간'],['ACTIVITY',`${pick.activity}P`,'사건 활동량'],['근거 신뢰등급',pick.trust,'평판등급 아님']].map(x=>`<div><small>${x[0]}</small><strong>${x[1]}</strong><em>${x[2]}</em></div>`).join('');
function bars(e){return`<table class="axis-table"><thead><tr><th>축</th><th>관측값</th><th>상태</th><th>관계 질문</th></tr></thead><tbody>${AXES.map(a=>`<tr><td><b>${a} · ${N[a]}</b><div class="bar"><i style="width:${e.axes[a]}%"></i></div></td><td>${e.axes[a].toFixed(1)}</td><td>관측 · 반영</td><td>${{B:'얼마나 널리 발견되는가',R:'공중은 어떻게 응답하는가',I:'무엇으로 기억되는가',D:'실제 접점은 어떠한가',G:'어떤 움직임을 만드는가',E:'신뢰를 얼마나 지켜내는가'}[a]}</td></tr>`).join('')}</tbody></table>`}
function table(){return`<table class="compare-table"><thead><tr><th>대상</th><th>순위</th><th>DAILY</th><th>WEEKLY</th><th>활동량</th><th>신뢰</th></tr></thead><tbody>${entities.map(e=>`<tr><td>${e.name}</td><td>${e.rank}위</td><td>${fmt(e.daily)}</td><td>${fmt(e.weekly)}</td><td>${e.activity}P</td><td>${e.trust} · 평판등급 아님</td></tr>`).join('')}</tbody></table>`}
function seven(lines){return`<ol class="sentence-list">${lines.map(x=>`<li>${x}</li>`).join('')}</ol>`}
function sheet(n,kicker,title,body,total,part){return`<article class="sample-sheet" id="page-${n}" data-page="${String(n).padStart(2,'0')} / ${total}"><span class="sample-part-badge">${part}</span><br><span class="sample-kicker">${kicker}</span><h2>${title}</h2>${body}<div class="sample-footerline"><span>SIGNALBRIDGE · FIXED SAMPLE 20261025</span><span>${config.meta}</span></div></article>`}
const common=[
 ['SIGNAL GUIDE','BRIDGE는 무엇을 관측하는가',`<p class="lead">공개자료와 공중의 관측 신호를 바탕으로 브랜드와 공중 사이의 관계 상태·구성·변화 방향을 반복 관측합니다.</p><div class="reading-box"><b>생활 언어로 읽기</b><p>성적표라기보다 오늘의 관계 건강검진에 가깝습니다. 다만 사람의 마음을 직접 재거나 대상의 모든 가치를 판정하지 않습니다.</p></div>`],
 ['EVIDENCE CARD','점수와 신뢰등급을 분리해서 읽기',`<div class="sample-grid"><div class="sample-card"><small>DAILY</small><strong>78.55</strong><b>오늘의 관계 수준</b></div><div class="sample-card"><small>EVIDENCE</small><strong>D</strong><b>근거 신뢰등급</b></div><div class="sample-card"><small>COVERAGE</small><strong>6 / 6</strong><b>관측축</b></div></div><p>신뢰등급 D는 리센느의 평판이 D라는 뜻이 아닙니다. 현재 공개 근거의 범위와 다양성을 함께 확인하라는 감사 표기입니다.</p>`],
 ['B · R · I · D · G · E','리센느의 여섯 축 상태',bars(pick)],
 ['TIME WINDOWS','오늘·이번 주·직전 주를 나눠 읽기',`<div class="sample-grid"><div class="sample-card"><small>DAILY</small><strong>78.55</strong><b>2026.10.25</b></div><div class="sample-card"><small>WEEKLY</small><strong>79.28</strong><b>월요일부터 현재</b></div><div class="sample-card"><small>LAST WEEK</small><strong>83.99</strong><b>직전 완료 주간</b></div></div><p>WoW는 ${sg(pick.wow)}입니다. 진행 중 주간과 완료 주간의 차이이므로 축 커버리지와 관측일 수를 함께 확인해야 하며, 하락 원인을 숫자만으로 만들어내지 않습니다.</p>`],
 ['ACTIVITY ≠ REPUTATION','684P가 말하는 것과 말하지 않는 것',`<p class="lead">684P는 이번 주 검증·귀속·중복 제거된 사건 움직임의 크기입니다.</p><p>관심이 크게 움직였다는 사실은 보여주지만 긍정 반응의 비율이나 관계의 질을 자동으로 뜻하지 않습니다. 활동량은 DAILY 78.55와 나란히 읽되 서로 대체하지 않습니다.</p>`],
 ['NEXT QUESTION','다음 회차에서 확인할 것',seven([`R·반응과 I·정체성의 높은 관측값이 다음 회차에도 같은 방향으로 반복되는가?`,`G·행동유발이 현재의 발견과 반응을 실제 후속 행동으로 연결하는가?`,`E·책임·지속의 직접 근거가 확장될 때 전체 구조가 어떻게 달라지는가?`,`새로운 독립 사건과 동일 사건의 반복 전재가 구분되는가?`,`활동량 변화와 관계 수준 변화가 같은 방향인지 별도로 확인할 수 있는가?`])],
 ['PUBLICITY DIGEST','리센느 78.55점… 반응과 정체성이 이끄는 현재 구조',`<div class="publicity-block"><h3>순위보다 먼저 보이는 두 축</h3><p>2026년 10월 25일 ENT T100에서 리센느는 6위, DAILY 78.55를 기록했다. R·반응과 I·정체성은 각각 100.0으로 관측됐지만, 이것이 인기·능력·미래 성과 전체를 확정하는 것은 아니다.</p><p>이번 브리핑의 핵심은 강한 반응이 무엇으로 기억되는지와 연결돼 있다는 점, 그리고 그 연결이 경험·행동·지속으로 이어지는지를 다음 회차에서 검증해야 한다는 데 있다.</p></div>`]
];
function basicPages(){const pages=[...common];pages.splice(5,0,['POSITION READ','리센느의 현재 위치',`<p class="lead">당일 지수는 ${sg(pick.change)} 상승했지만 순위는 5위에서 6위로 이동했습니다.</p><p>점수는 리센느 자체의 관측값 변화를, 순위는 ENT T100 비교집합 전체 안의 상대적 위치를 보여줍니다. 주변 대상이 더 크게 움직일 수 있으므로 점수 상승과 순위 하락은 모순이 아닙니다.</p>`]);return pages}
const analysisSeven=(subject)=>[
 `${subject}은 동일한 2026년 10월 25일 ENT T100 공개 스냅샷에서 읽습니다.`,
 `순위는 전체 비교집합 안의 상대적 위치이며 세 대상만 놓고 다시 계산한 결과가 아닙니다.`,
 `점수 차이는 관측 구조의 간격이지만 통계적 유의성이나 절대적 우월성을 자동으로 뜻하지 않습니다.`,
 `축의 높은 값은 현재 근거가 선명한 지점이고 낮은 값은 실패나 부정 사건의 판정이 아닙니다.`,
 `활동량은 사건 움직임의 크기이므로 DAILY 지수와 분리해 읽습니다.`,
 `신뢰등급 D는 세 대상의 평판등급이 아니라 설명을 뒷받침하는 근거 범위 표기입니다.`,
 `다음 회차에서는 같은 구조가 반복되는지와 직접 근거가 확장되는지를 다시 확인합니다.`
];
function standardPages(){return[
 ...common.slice(0,4),
 ['PAIR READING','두 축을 연결해 질문을 만드는 법',`<p class="lead">리센느의 R＋I는 반응이 특정 이미지와 의미를 중심으로 모이는지를 묻는 조합입니다.</p><p>두 축이 모두 100.0이라는 사실은 현재 구조가 선명하다는 뜻이지만, 정체성이 반응의 원인이라고 단정하지 않습니다. 같은 사건에 귀속된 독립 근거와 반복 관측이 있어야 연결의 지속성을 말할 수 있습니다.</p>`],
 ['CONTEXT MAP','화제성과 관계 수준은 다릅니다',`<div class="sample-grid"><div class="sample-card"><b>ONLINE ACTIVITY</b><p>얼마나 크게 움직였는가</p></div><div class="sample-card"><b>BRIDGE RELATIONSHIP</b><p>어떤 관계 구조로 남았는가</p></div><div class="sample-card"><b>EVIDENCE STATUS</b><p>어디까지 설명 가능한가</p></div></div>`],
 ['SAME SCOPE','비교가 성립하는 조건',table()+`<p>세 대상은 같은 분야·같은 기준일·같은 T100 공개 범위에서만 비교합니다. 비교군은 리센느를 유리하게 보이게 하는 장치가 아니라 서로 다른 관계 경로를 발견하기 위한 기준점입니다.</p>`],
 ['FIELD PLAYBOOK','ENT 관계 환경',seven(['팬과 일반 공중의 신호를 구분합니다.','인기와 관계 평판을 같은 말로 사용하지 않습니다.','활동량과 관계 수준을 분리합니다.','신규 대상의 급격한 진입 가능성을 매일 확인합니다.','팬덤 반응을 전체 공중의 인식으로 확대하지 않습니다.','직군과 활동 형태의 차이를 해석에 반영합니다.','동일 사건의 반복 확산과 새로운 발견을 구분합니다.'])],
 ['FIELD PULSE','ENT 장기 성과 지형을 먼저 보는 이유',`<p class="lead">당일 등락 앞에 누적 주간 성과를 놓으면 오늘의 급격한 움직임과 반복되는 관계 구조를 분리할 수 있습니다.</p><p>리센느의 누적 성과는 81.63이며 관측 2주 기준입니다. 네 주가 채워지지 않았으므로 이를 4-WEEK AVERAGE라고 부르지 않습니다.</p>`],
 ['POSITION TABLE','세 대상의 현재 위치',table()],
 ['POSITION READ 01–07','점수와 순위의 다른 움직임',seven(analysisSeven('리센느'))],
 ['POSITION READ 08–13','당일·주간·장기 시간창',seven([`DAILY 78.55는 10월 25일의 관계 구조입니다.`,`WEEKLY 79.28은 월요일부터 현재까지의 진행 중 주간 값입니다.`,`LAST WEEK 83.99는 직전 완료 주간 값입니다.`,`WoW ${sg(pick.wow)}는 서로 다른 시간창의 차이이므로 관측 조건을 확인합니다.`,`누적 성과 81.63은 확보된 주간 대표값의 평균입니다.`,`STABILITY N/R은 불안정 판정이 아니라 완료 주간 부족입니다.`,`시간창을 구분하면 하루의 변화를 장기 추세로 오인하지 않게 됩니다.`])],
 ['POSITION READ 14–19','현재 위치의 실무적 의미',seven([`리센느의 점수는 ${sg(pick.change)} 움직였습니다.`,`순위는 5위에서 6위로 이동했습니다.`,`점수 상승과 순위 하락은 비교집합의 동시 움직임으로 함께 나타날 수 있습니다.`,`즉시 순위 방어 행동을 정하기보다 실제로 달라진 축을 먼저 확인합니다.`,`동일 사건의 반복 노출을 새로운 평판 변화로 중복 계산하지 않습니다.`,`비교 대상의 상승·하락도 같은 기준일 범위에서 함께 점검합니다.`,`다음 발표에서는 순위와 함께 점수 간격과 근거 상태를 설명합니다.`])],
 ['MY PICK','리센느 독립 분석',bars(pick)+seven(analysisSeven('리센느'))],
 ['COMPARE A','르세라핌 독립 분석',bars(DATA.a)+seven(analysisSeven('르세라핌'))],
 ['COMPARE B','아일릿 독립 분석',bars(DATA.b)+seven(analysisSeven('아일릿'))],
 ['SIX-AXIS MATRIX','세 대상의 구조 비교',`<table class="compare-table"><thead><tr><th>축</th>${entities.map(e=>`<th>${e.name}</th>`).join('')}</tr></thead><tbody>${AXES.map(a=>`<tr><td>${a} · ${N[a]}</td>${entities.map(e=>`<td>${e.axes[a].toFixed(1)}</td>`).join('')}</tr>`).join('')}</tbody></table>`+seven(analysisSeven('세 대상 비교'))],
 ['PAIR ATLAS','15개 결합 중 우선 해석',`<div class="sample-grid"><div class="sample-card"><small>R＋I</small><b>반응 정체성 결속</b><p>반응이 특정 이미지와 의미로 모이는가</p></div><div class="sample-card"><small>B＋G</small><b>발견 행동 전환</b><p>발견이 검색·참여로 이어지는가</p></div><div class="sample-card"><small>G＋E</small><b>행동 관계 지속</b><p>행동이 지속 관계로 남는가</p></div></div>`+seven(analysisSeven('축 결합'))],
 ['ACTIVITY 01–06','활동량과 관계 수준',table()+seven([`리센느의 684P는 이번 주 사건 활동량입니다.`,`아일릿 630P와 르세라핌 240P 역시 긍정성 점수가 아닙니다.`,`활동량이 큰 대상이 DAILY에서도 반드시 높지는 않습니다.`,`0P가 나오더라도 실제 활동 부재로 단정하지 않습니다.`,`사건의 귀속과 중복 제거를 통과한 범위만 합산합니다.`,`활동량은 관심의 온도이고 관계 수준은 그 움직임이 남긴 구조입니다.`,`두 값을 분리해야 화제성을 평판 전체로 오인하지 않습니다.`])],
 ['ACTIVITY 07–13','움직임 뒤에 남은 관계',seven([`활동이 어느 축의 직접 근거로 귀속됐는지 확인합니다.`,`긍정·부정 방향을 활동량만으로 추정하지 않습니다.`,`높은 반응이 경험과 행동으로 이어지는지 별도로 봅니다.`,`같은 사건의 반복 전재는 독립 발견과 구분합니다.`,`공식 일정과 제3자 반응의 출처를 분리합니다.`,`다음 회차에도 같은 관계 경로가 반복되는지 확인합니다.`,`실무에서는 노출 확대보다 강한 축을 만든 접점의 재현 가능성을 먼저 검토합니다.`])],
 ['NEXT QUESTIONS','다음 관측과 실무 과제',seven(analysisSeven('다음 관측'))],
 ['PUBLICITY BRIEF','리센느 78.55점… ENT 6위보다 먼저 읽히는 반응·정체성 구조',`<div class="publicity-block"><h3>01 · 기준 사실</h3><p>리센느는 2026년 10월 25일 ENT T100에서 6위, DAILY 78.55를 기록했다.</p></div><div class="publicity-block"><h3>02 · 비교 구조</h3><p>아일릿과 르세라핌을 같은 조건에서 비교하면 세 대상은 반응·정체성·경험·행동의 조합에서 서로 다른 경로를 보인다.</p></div><div class="publicity-block"><h3>03 · 해석의 경계</h3><p>순위는 관심의 입구이며, 활동량과 축값은 인기·능력·윤리성 전체를 판정하지 않는다.</p></div>`],
 ['REPORT NOTES','해석상 한계와 최종 명제',seven(['순위는 동일 날짜 공개 대상군의 상대적 위치입니다.','활동량은 긍정 평판이 아닙니다.','신뢰등급은 평판등급이 아닙니다.','참조값 50은 실제 평가점수가 아닙니다.','N/R은 0점이나 불안정 판정이 아닙니다.','BRIDGE는 미래 성과나 인격을 판정하지 않습니다.','순위는 해석의 입구이고 여섯 축은 관계 구조를 설명합니다.'])]
]}
function specialPages(){const p=standardPages();p.push(
 ['SPECIAL OVERVIEW','3일 관측을 하나의 흐름으로 읽기',`<span class="special-mark">3-DAY WINDOW</span><div class="day-grid"><article><b>목요일</b><p>직전 축 구조와 사건 귀속을 기준선으로 저장합니다.</p></article><article><b>금요일</b><p>새 근거와 반복 전재를 분리해 변화를 확인합니다.</p></article><article><b>토요일</b><p>주말 ENT 변동성과 팬·일반 공중의 신호를 함께 점검합니다.</p></article></div><p>샘플은 기준일 고정본이므로 실제 일별 미확인 값을 만들어 넣지 않습니다. 완성 서비스에서는 해당 세 날짜의 저장된 원장을 사용합니다.</p>`],
 ['THREE-DAY METHOD','요일별 자료의 비교 조건',seven(['세 날짜의 기준 시각을 동일하게 맞춥니다.','각 날짜의 T100 비교집합 크기를 확인합니다.','관측·유지·참조 상태 변화를 먼저 봅니다.','새 사건과 반복 전재를 구분합니다.','활동량과 관계 수준을 별도 계열로 표시합니다.','근거 범위 확대를 실제 평판 변화와 구분합니다.','조건이 맞지 않으면 원인 해석을 보류합니다.'])],
 ['CHANGE DIAGNOSIS','변화 원인을 확정하기 전의 네 단계',seven(['먼저 실제로 달라진 축을 확인합니다.','그 축의 신규 근거 날짜와 출처를 확인합니다.','동일 사건의 중복 노출 여부를 점검합니다.','비교집합 전체가 함께 움직였는지 확인합니다.','관측 범위 확대만으로 점수가 변했는지 분리합니다.','직접 확인되지 않은 사건을 원인으로 만들지 않습니다.','남은 가능성은 가설로 표시하고 다음 회차 검증 질문으로 넘깁니다.'])],
 ['STRATEGY 01','R＋I 강점을 설명 가능한 정체성으로 유지',`<div class="strategy-card"><b>향후 전략 제안</b><p>리센느의 R·반응과 I·정체성은 현재 가장 선명합니다. 실무에서는 더 큰 반응을 무조건 만드는 것보다 어떤 메시지와 콘텐츠가 같은 정체성 연상을 반복해서 형성했는지 원장 단위로 분리해야 합니다.</p></div>`+seven(analysisSeven('R＋I 전략'))],
 ['STRATEGY 02','B＋G 발견을 행동으로 연결하는 접점 설계',`<div class="strategy-card"><b>향후 전략 제안</b><p>B 68.2와 G 73.0은 발견 이후 행동의 경로를 점검할 수 있는 조합입니다. 검색·콘텐츠 소비·공식 채널 이동처럼 검증 가능한 후속 행동을 캠페인 목표와 연결하되 인과는 실험과 반복 관측으로 확인합니다.</p></div>`+seven(analysisSeven('B＋G 전략'))],
 ['STRATEGY 03','D＋E 경험과 지속 근거의 확장',`<div class="strategy-card"><b>향후 전략 제안</b><p>D 40.2와 E 15.3을 부정 상태로 규정하지 않습니다. 팬 경험과 책임·지속을 직접 보여주는 확인 가능한 접점이 어떤 자료로 남는지 설계하고, 확보된 근거가 기존 강점과 연결되는지를 봅니다.</p></div>`+seven(analysisSeven('D＋E 전략'))],
 ['SCENARIO MAP','실무 대응 시나리오',`<div class="sample-grid"><div class="sample-card"><b>신규 이슈 급증</b><p>활동량과 반응 방향을 분리하고 24시간 귀속을 점검합니다.</p></div><div class="sample-card"><b>순위 하락</b><p>점수·비교집합·축 커버리지 중 무엇이 달라졌는지 먼저 확인합니다.</p></div><div class="sample-card"><b>근거 확대</b><p>실제 관계 변화와 관측 범위 확대를 분리 표기합니다.</p></div></div>`],
 ['PUBLICITY ARCHIVE 01','WEEK 42 · WED ENT',`<div class="publicity-block"><h3>임영웅 85.7점… ENT, 선두의 수치 뒤에 남은 연결 과제</h3><p>ENT 공개 적격 100개 대상의 위치·관계 구성·관측 범위를 함께 읽은 회차입니다.</p></div>${seven(['당시 리센느는 82.37로 3위에 위치했습니다.','그 수치는 10월 14일 고정 입력이며 현재 값과 직접 합치지 않습니다.','당시 활동량은 252P로 기록됐습니다.','현재 샘플과 비교하면 순위와 활동량 모두 시간창이 다릅니다.','정체성과 반응 구조가 반복되는지 확인하는 기준점으로 사용할 수 있습니다.','변화 원인은 당시와 현재의 원장을 대조한 뒤에만 판단합니다.','과거 퍼블리시티는 장기 서사의 근거이지 현재 점수의 자동 원인이 아닙니다.'])}`],
 ['PUBLICITY ARCHIVE 02','WEEK 42 · FRI ENT',`<div class="publicity-block"><h3>방탄소년단 86.5점… ENT, 선두의 수치 뒤에 남은 연결 과제</h3><p>활동의 크기와 관계 구성의 차이를 함께 설명한 회차입니다.</p></div>${seven(['당시 리센느는 85.28로 2위였습니다.','해당 회차의 활동량은 552P였습니다.','현재 샘플의 684P와 기간 누적 방식이 같은지 먼저 확인해야 합니다.','순위 변화만으로 관계 약화를 단정하지 않습니다.','과거 높은 위치가 현재의 절대 기준선은 아닙니다.','두 회차에서 반복되는 강한 축과 새로 달라진 축을 분리합니다.','SPECIAL은 이런 과거 맥락을 전략 제안의 근거로 사용합니다.'])}`],
 ['PUBLICITY SYNTHESIS','이전 2주와 현재를 연결하는 법',seven(['퍼블리시티의 헤드라인은 관심을 여는 장치입니다.','본문은 순위보다 축 구조와 변화 조건을 설명합니다.','과거 회차 수치를 현재 값에 단순 누적하지 않습니다.','같은 대상의 반복 등장은 장기 관계 서사를 확인하게 합니다.','새 사건과 동일 사건의 재전재를 구분합니다.','사용자가 선택한 리센느의 주차별 특징을 5~7문장으로 별도 분석합니다.','그 분석은 확인된 근거와 제한 해석만 사용합니다.'])],
 ['EXECUTIVE ACTION','향후 2주 전략 우선순위',seven(['첫째, R＋I 강점을 만든 반복 연상과 콘텐츠 접점을 분류합니다.','둘째, B＋G 경로에서 발견 이후 검증 가능한 후속 행동을 정의합니다.','셋째, D와 E는 점수 상승 목표가 아니라 직접 근거 확보 계획으로 관리합니다.','넷째, 신규 이슈 발생 시 24시간 사건 귀속과 중복 제거를 우선합니다.','다섯째, 팬 반응과 일반 공중의 반응을 가능한 범위에서 분리합니다.','여섯째, 순위 변화 발표에는 점수 간격과 근거 신뢰등급을 함께 표기합니다.','일곱째, 다음 회차에서 이 제안의 관측 가능성과 실행 결과를 다시 검증합니다.'])],
 ['SPECIAL REPORT NOTES','스페셜 브리핑의 최종 경계',seven(['전략 제안은 관측값에 근거한 권고이며 미래 결과를 보장하지 않습니다.','3일 자료가 완전하지 않으면 미확인 값을 만들지 않습니다.','변화 원인은 사건 귀속이 확인된 범위에서만 설명합니다.','과거 퍼블리시티는 현재 점수의 직접 원인으로 자동 사용하지 않습니다.','비교 대상의 강점을 중심 대상을 폄하하는 근거로 사용하지 않습니다.','최소 35페이지보다 사실성이 우선이지만 확인된 사실은 충분히 설명합니다.','쉬운 해석은 전문 분석으로 들어가는 입구이며 전문 분석을 대체하지 않습니다.'])]
);return p}
const basicSet=basicPages().map(x=>[...x,'PART A · 리센느 기본 브리핑']);
const expandedSet=(edition==='standard'?standardPages():specialPages()).map(x=>[...x,edition==='standard'?'PART B · 리센느 일반 브리핑':'PART B · 리센느 스페셜 브리핑']);
let pages=edition==='basic'?basicSet:basicSet.concat(expandedSet);
const total=pages.length,partCopy=edition==='standard'?'BASIC 8개 장을 먼저 읽은 뒤, 기존 23페이지 일반 분석으로 이어집니다.':edition==='special'?'BASIC 8개 장을 먼저 읽은 뒤, 기존 35페이지 심층 분석으로 이어집니다.':'한 대상의 핵심 구조를 8개 장으로 읽습니다.';
let lastPart='';$('#samplePages').innerHTML=pages.map((x,i)=>{const heading=x[3]!==lastPart?`<header class="sample-part-heading"><small>${x[3].startsWith('PART A')?'FOUNDATION':'EXPANDED EDITION'}</small><h2>${x[3]}</h2><p>${x[3].startsWith('PART A')?'BASIC과 동일한 단일 대상 독립 분석입니다.':partCopy}</p></header>`:'';lastPart=x[3];return heading+sheet(i+1,x[0],x[1],x[2],total,x[3]);}).join('')+`<a class="sample-back" href="subscribe.html#serviceOverview">← 세 단계의 분석 깊이로 돌아가기</a>`;
$('#sampleToc').innerHTML=pages.map((x,i)=>`<a href="#page-${i+1}">${String(i+1).padStart(2,'0')} ${x[0]}</a>`).join('');
})();
