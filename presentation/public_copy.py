"""Public explanations aligned with BRIDGE methodology; no scoring internals."""
from presentation.editorial_standard import FOOTER_COPY

def card(tag,title,text):
    return f'<div class="dx-domain"><div class="dx-head"><span class="dx-tag">{tag}</span><h2 class="dx-title">{title}</h2></div><p class="dx-body">{text}</p></div>'

def hero(css,kicker,title,deck):
    return f'<header class="list-hero-photo {css}"><div class="wrap"><div class="about-kicker">{kicker}</div><h1 class="public-hero-title">{title}</h1><p class="list-note">{deck}</p></div></header>'

def wrap(body):return '<section class="section"><div class="wrap public-copy">'+body+'</div></section>'

AXIS_ROWS=[('B','도달','얼마나 널리 발견되는가','공중과 만나는 가시성'),('R','반응','공중은 어떻게 응답하는가','관측된 평가와 반응의 방향'),('I','정체성','무엇으로 기억되는가','브랜드 연상의 명확성과 지속성'),('D','경험','실제 접점은 어떠한가','제품·서비스·행정·교육 등 경험의 기반'),('G','행동유발','어떤 움직임을 만드는가','탐색·참여·추천 등으로 이어지는 행동'),('E','책임·지속','신뢰를 얼마나 지켜내는가','책임 이행과 신뢰 유지의 기반')]

INDEX = hero('hero-methodology','BRIDGE / INDEX','순위는 결과가 아니라,<br>해석의 출발점입니다.','점수와 순위, 여섯 축의 구성, 시간에 따른 변화와 근거 상태를 함께 읽는 BRIDGE의 공식 안내입니다.')+wrap(
card('01 / DEFINITION','공개자료로 확인되는 평판을 반복 관측합니다','BRIDGE는 브랜드가 얼마나 발견되는지, 어떤 반응을 얻는지, 무엇으로 기억되는지, 경험과 행동으로 어떻게 이어지는지, 책임과 신뢰가 어떻게 유지되는지를 여섯 축으로 관측합니다. 공중의 마음 전체를 직접 측정하거나 기업·기관·대학·공인의 절대적 가치와 능력을 판정하는 체계는 아닙니다.')+
'<div class="public-triptych"><div><small>POSITION</small><h2>현재 위치</h2><p>지수와 순위로 관측된 상대적 수준을 살핍니다.</p></div><div><small>RELATIONSHIP</small><h2>관계 구성</h2><p>여섯 축의 강점과 제약, 연결이 덜 확인된 접점을 읽습니다.</p></div><div><small>DIRECTION</small><h2>변화 방향</h2><p>비교 조건과 근거 범위를 확인하며 흐름을 해석합니다.</p></div></div>'+
card('02 / SIX AXES','하나의 총점 뒤에 여섯 개의 질문이 있습니다','도달이 높다고 반응까지 긍정적인 것은 아니며, 활동이 많다고 책임 이행이 충분한 것도 아닙니다. BRIDGE는 총점을 먼저 보여주되 여섯 축을 다시 펼쳐 무엇이 현재 결과를 설명하고 무엇은 추가 확인이 필요한지 구분합니다. 두 축이 함께 높거나 낮게 나타나도 직접적인 인과관계가 확인된 것은 아닙니다.')+
'<div class="public-table-scroll"><table class="idx-table"><thead><tr><th>축</th><th>핵심 질문</th><th>읽는 의미</th></tr></thead><tbody>'+''.join(f'<tr><td><b>{a}</b> {n}</td><td>{q}</td><td>{m}</td></tr>' for a,n,q,m in AXIS_ROWS)+'</tbody></table></div>'+
card('03 / TIME','오늘의 수준과 이번 주의 흐름을 나누어 봅니다','DAILY INDEX는 기준일의 관측 가능한 평판 수준입니다. WEEKLY INDEX는 월요일부터 현재까지 일별지수를 근거 신뢰도에 따라 가중한 평균이며, 주가 끝나기 전에는 잠정값입니다. Activity Points는 검증·귀속·중복 제거된 사건과 행동의 규모로, 평판점수와 단위도 의미도 다릅니다. 같은 사건의 반복 전재나 기존 근거의 재사용을 새로운 활동으로 더하지 않습니다.')+
card('04 / INTERPRETATION','점수 변화와 순위 이동은 같은 말이 아닙니다','점수는 대상 자체의 관측값이고 순위는 비교집합 안의 상대적 위치입니다. 점수가 올라도 주변 대상이 더 크게 움직이면 순위는 유지되거나 내려갈 수 있습니다. 새로운 축이나 출처가 추가된 회차에는 실제 평판 변화와 근거 범위 확대가 함께 나타날 수 있으므로 이를 분리해 표시합니다. 동일 조건의 이력이 부족하면 전주 대비 변화나 안정성을 확정하지 않습니다.')+
card('05 / ACCOUNTABILITY','공개할 기준과 보호할 방법을 구분합니다','공개 화면에는 개념, 기준기간, 축 상태, 비교 가능 여부, 근거 신뢰등급과 해석 한계를 제공합니다. 세부 변환식·가중치·임계값·수집 전략은 지식재산과 조작 방지를 위해 내부에서 관리합니다. 대상 식별, 자료 귀속, 기준일 또는 표시 오류가 의심되면 <a href="contact.html">문의·이의제기</a>에서 근거를 제출할 수 있습니다. 자료가 결과가 되는 과정은 <a href="data-extraction.html">DATA TRACE</a>, 근거 신뢰등급의 의미는 <a href="trust.html">신뢰등급</a>에서 확인할 수 있습니다.'))

TRACE = hero('hero-data-extraction','BRIDGE / DATA TRACE','결과가 된 자료를<br>끝까지 확인합니다.','출처·기준시점·대상 귀속·중복·유효기간을 확인하고, 실제 변화와 근거 범위의 변화를 구분합니다.')+wrap(
card('01 / SOURCES','빠른 신호와 오래 유지되는 기반','뉴스·공식 채널·공중 반응은 비교적 빠른 변화를, 공시·교육여건·공식 통계와 평가자료는 기준기간의 기반을 설명합니다. 이들은 같은 종류의 근거가 아닙니다. 자료 유형별 활용 범위가 다르고, 모든 대상에서 모든 출처가 확보되는 것은 아닙니다. 공식 홍보 문구도 공중의 긍정 반응으로 곧바로 바꾸어 읽지 않습니다.')+
'<ol class="public-flow"><li><b>자료</b><span>출처와 기준시점 확인</span></li><li><b>대상·사건</b><span>귀속과 중복 점검</span></li><li><b>축·기간</b><span>평가 목적과 유효성 확인</span></li><li><b>공개 결과</b><span>지수·근거 상태·해석</span></li></ol>'+
card('02 / VALIDITY','오래된 사건을 새 사건으로 만들지 않습니다','발생·발행 시점과 수집 시점, 자료의 기준기간을 구분합니다. 유효성은 영역·축·자료 유형에 맞춘 공통 규칙으로 관리하는 것이 원칙입니다. 유효한 공시가 다음 날에도 평가 기반이 될 수는 있지만 매일 새로운 활동으로 반복 가산되지는 않습니다. 책임 사건은 기간 경과만으로 후속 조치와 이력이 사라졌다고 해석하지 않습니다.')+
card('03 / DISTINCT EVENTS','사건의 수와 확산의 크기를 구분합니다','동일 자료의 재수집과 전재를 독립 사건처럼 반복 세지 않습니다. 실질적으로 새로운 사실이나 반응이 있는 후속 자료는 구분해 검토합니다. 한 사건이 여러 축을 설명하더라도 활동량은 사건 단위로 관리합니다. 영상의 누적 반응과 관측 시점 사이의 증분도 구별해야 합니다.')+
card('04 / OBSERVATION','발견하지 못한 것과 관측하지 못한 것은 다릅니다','정해진 수집 범위를 정상적으로 확인했으나 유효 언급을 찾지 못한 경우와, 실패·차단·실행 누락으로 확인하지 못한 경우를 구분합니다. 부분 관측은 확보된 근거만 해석하며 전체 무언급으로 확장하지 않습니다. 수집 실패를 대상의 소통 부재나 부정적 평판으로 바꾸지 않습니다.')+
card('05 / COVERAGE','일주일의 두께를 함께 읽습니다','수집이 정상 완료된 날과 새로운 근거가 발견된 날은 서로 다른 정보입니다. 유효 축의 범위, 자료의 최신성, 출처 구성, 기존 기준자료에 대한 의존도도 함께 살펴야 합니다. 하루의 자료가 있는 잠정 주간값을 일주일 전체를 관측한 결과처럼 표현하지 않습니다.')+
card('06 / COMPARABILITY','평판의 변화와 근거 범위의 변화를 나눠 봅니다','새로운 축·출처가 추가되거나 기존 근거가 만료되면 비교 조건이 달라집니다. 기준 변경과 근거 범위 확대·축소는 해석에 함께 표시해야 합니다. 공통 축이 있더라도 출처 구성까지 같다는 보장은 없으므로 점수 차이를 순수한 인과 효과로 설명하지 않습니다. <a href="trust.html">신뢰등급</a>은 이 판단을 돕는 근거 충실성 정보입니다.'))

TRUST = hero('hero-trust','BRIDGE / EVIDENCE QUALITY','평판의 수준과<br>근거의 충실성은 다릅니다.','신뢰등급은 대상의 평판등급이 아닙니다. 이번 결과를 뒷받침하는 자료의 범위·최신성·귀속과 비교 가능성을 알려주는 정보입니다.')+wrap(
card('01 / QUALITY','점수 옆의 등급을 읽는 법','높은 점수라도 관측기간이나 출처가 제한될 수 있습니다. 낮은 등급을 나쁜 평판으로 읽거나, 공식자료 하나가 있다는 이유만으로 모든 축의 판단을 충분하다고 보아서는 안 됩니다. 등급은 최신성·관측 범위·귀속의 명확성·자료 의존도와 함께 해석해야 합니다.')+
'<div class="public-table-scroll"><table class="trust-grade-table"><thead><tr><th>표시</th><th>공개 해석</th></tr></thead><tbody><tr><td>A</td><td>상대적으로 충실한 관측 기반. 모든 사실의 완전한 확인을 뜻하지 않습니다.</td></tr><tr><td>B</td><td>해석을 뒷받침할 근거가 있으나, 일부 범위·기간의 제약을 확인해야 합니다.</td></tr><tr><td>C</td><td>공개 최소 요건 안에서 제한적으로 읽어야 하는 근거 상태입니다.</td></tr><tr><td>D</td><td>근거가 제한된 예비 상태로, 공개 순위 적격성과 구분해 관리합니다.</td></tr><tr><td>N/R · 산출 보류</td><td>최소 요건을 충족하지 못했거나 산출 여부를 확인할 수 없는 상태입니다. 낮은 점수로 대체하지 않습니다.</td></tr></tbody></table></div>'+
card('02 / PROFILE','여섯 숫자의 근거 상태는 같지 않습니다','관측값은 유효한 직접 근거에, 유지값은 유효기간 안의 기존 근거에 기반합니다. 추정값은 검증된 모형이 있을 때만 평가값으로 활용할 수 있습니다. 현재 검증되지 않은 추정을 공식값으로 채우지 않습니다. 근거가 없는 축의 참조값은 시각적 기준이며, 중립 평가가 확인됐다는 뜻이 아닙니다. 참조 축은 순위 계산에서 제외하고 프로필에서 구별합니다.')+
card('03 / TWO DECISIONS','프로필 완성과 공개 순위는 별도 판단입니다','다이어그램에 여섯 숫자가 있어도 여섯 축을 모두 충분히 측정했다는 뜻은 아닙니다. 공개 대상 수가 모집단 수와 다를 수 있는 이유입니다. 점수·신뢰등급·근거 상태·관측기간을 함께 확인하고, 공개되지 않은 대상에 임의의 순위나 점수를 부여하지 않습니다.')+
card('04 / BETA','설계 원칙과 현재의 구현 범위를 구분합니다','현재 v5 예비 운영 결과는 실제 확보된 근거의 범위에서 제공합니다. 주간 충족도와 등급의 세부 경계값은 데이터 검증과 교정의 대상이며 보편적인 확정 기준으로 제시하지 않습니다. 진행 중인 주, 비교 이력 부족, 참조 축의 존재는 해석을 제한합니다. 세부 배점·경계값·수집 전략은 공개하지 않습니다.')+
card('05 / CORRECTION','정확성은 수정 가능성과 함께 지킵니다','대상 식별이나 자료 귀속, 기준기간과 표시 내용에 오류가 의심되면 <a href="contact.html">문의·이의제기</a>로 근거를 남겨 주세요. 근거 오류와 단순한 점수 조정 요청은 구분해 검토합니다. 결과를 읽는 전체 틀은 <a href="methodology.html">INDEX</a>, 자료 처리의 공개 원칙은 <a href="data-extraction.html">DATA TRACE</a>에서 확인할 수 있습니다.'))

ABOUT = (hero('hero-about about-hero-big','SIGNALBRIDGE / COMPANY','순위를 제시하고,<br>그 이유를 설명합니다.','시그널브릿지는 공개자료에서 확인되는 평판 신호를 구조화해 현재 수준, 축별 구성, 변화와 근거의 범위를 함께 설명합니다.')+wrap(
'<div class="public-statement"><small>OUR PERSPECTIVE</small><p>얼마나 많이 보이는가에서 시작해,<br><b>어떤 관계를 만들고 있는가</b>를 묻습니다.</p></div>'+
card('01 / PURPOSE','하나의 순위를 넘어서는 분석','화제성과 규모는 브랜드를 읽는 중요한 신호지만 그것만으로 모든 관계를 설명할 수는 없습니다. 시그널브릿지는 현재의 상대적 위치와 여섯 축의 구성, 관측 가능한 변화의 방향을 함께 살핍니다. 상위 대상의 제약도, 다른 대상에서 근거로 확인되는 강점도 같은 기준으로 이야기하는 것이 우리의 분석 방향입니다.'))+
'<div class="about-figure"><img src="img/about_bridge.jpg" alt="관계를 잇는 다리" loading="lazy"><div class="about-figure-cap">FROM SIGNALS TO RELATIONSHIPS</div></div>'+wrap(
card('02 / CONTEXT','네 영역의 맥락, 여섯 축의 공통 질문','BRIDGE는 기업(CPR)과 소비자·고객·사회, 공공기관(GOV)과 주민·정책 수요자, 대학(UNI)과 지원자·학생·졸업생·사회, 공인(ENT)과 대중 사이의 관계를 살핍니다. 공통 질문을 유지하면서 자료의 성격과 해석의 접점을 구분합니다. 분야 사이의 점수 차이를 곧바로 우열로 바꾸지 않습니다.')+
'<div class="public-triptych"><div><small>OBSERVE</small><h2>관측</h2><p>출처·시점·대상 귀속을 확인하며 공개 신호를 구조화합니다.</p></div><div><small>INTERPRET</small><h2>해석</h2><p>관심·반응·경험·행동·신뢰의 구성을 읽습니다.</p></div><div><small>COMMUNICATE</small><h2>전달</h2><p>수치의 의미와 관측 범위를 독자가 이해할 언어로 설명합니다.</p></div></div>')+
'<div class="about-figure about-figure-split"><img src="img/about_ripple.jpg" alt="확산되는 신호의 파동" loading="lazy"><div class="about-figure-overlay"><div class="about-figure-title">Evidence before interpretation.</div><div class="about-figure-lead">해석의 출발점은 근거입니다.</div></div></div>'+wrap(
card('03 / COMMITMENT','근거에 따라 판단하고 한계를 함께 말합니다','광고나 홍보성 요청을 이유로 점수를 임의 조정하지 않는 것을 운영 원칙으로 둡니다. 오류에 대한 근거 있는 검토와 이해관계에 따른 점수 조정은 구별합니다. 관측하지 못한 것을 대상의 잘못으로 돌리지 않으며, 분석이 입증하지 않은 인격·본질적 가치·미래 성과를 확정하지 않습니다.')+
card('04 / PUBLICITY','순위표에서 끝나지 않는 이야기','PUBLICITY는 공개 지수를 기사형 분석으로 연결합니다. 수요일과 금요일에는 네 영역의 신호를, 다음 주 월요일에는 전주의 흐름을 종합해 읽습니다. 기사마다 해당 기간의 실제 공개자료를 바탕으로 관계의 차이와 추가 관찰 지점을 설명합니다. <a href="publicity.html">PUBLICITY 읽기 →</a>')+
'<div class="about-arch"><div class="about-arch-row"><div class="about-arch-k">운영 주체</div><div class="about-arch-n">SIGNALBRIDGE</div><div class="about-arch-d">서비스 운영과 데이터 관리</div></div><div class="about-arch-row"><div class="about-arch-k">분석 체계</div><div class="about-arch-n">BRIDGE</div><div class="about-arch-d">여섯 축으로 읽는 브랜드평판지수</div></div><div class="about-arch-row"><div class="about-arch-k">공개 서비스</div><div class="about-arch-n">INDEX / PUBLICITY</div><div class="about-arch-d">현재 위치와 근거에 기반한 해석</div></div></div><p class="about-contact"><a href="contact.html">문의·이의제기 →</a></p>')
)
