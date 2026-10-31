/* BRIDGE bilingual interface layer — Korean source, English reading edition.
   T100 entity names, scores and source records are deliberately preserved. */
(()=>{
  const params=new URLSearchParams(location.search);
  const saved=localStorage.getItem('bridge-ui-language');
  const lang=params.get('lang')==='en'?'en':params.get('lang')==='ko'?'ko':saved==='en'?'en':'ko';
  const isEn=lang==='en';
  const path=(location.pathname.split('/').pop()||'index.html').toLowerCase();
  const PUBLICITY=new Set(['publicity.html','publicity-article.html']);
  if(PUBLICITY.has(path))return;

  const FOOTER_KO='시그널브릿지(SIGNALBRIDGE)는 공개자료에서 확인되는 신호를 바탕으로 브랜드와 공중 사이의 관계 상태와 변화의 흐름을 반복 관측합니다. BRIDGE 브랜드평판지수는 기업(CPR), 공공기관(GOV), 대학(UNI), 공인(ENT)을 각 분야의 맥락 안에서 살피고, 도달·반응·정체성·경험·행동유발·책임과 지속의 여섯 축으로 관계의 현재 위치와 구성을 설명합니다. BRIDGE는 순위뿐 아니라 관측된 근거, 아직 충분히 확인되지 않은 영역, 실제 변화와 근거 범위의 차이를 함께 제시합니다. 관측할 수 있는 것과 아직 단정할 수 없는 것의 경계를 먼저 밝히고 순위 뒤의 관계를 설명하는 것, 그것이 BRIDGE가 지키는 관계 평판 인텔리전스의 기준입니다.';
  const FOOTER_EN='SignalBridge repeatedly observes the state and direction of relationships between a subject and its publics through signals verified in public data. The BRIDGE Brand Reputation Index reads companies (CPR), public institutions (GOV), universities (UNI) and public figures (ENT) within their own fields. Six dimensions—Reach, Response, Identity, Experience, Action and Responsibility & Continuity—describe the current level and composition of each relationship. BRIDGE presents not only rank, but also the evidence observed, areas not yet sufficiently verified, and the difference between a real signal change and a change in evidence coverage. Stating what can be observed and what cannot yet be concluded, then explaining the relationship behind the rank, is the standard of relationship-reputation intelligence that BRIDGE follows.';

  const TEXT={
    '신뢰등급':'EVIDENCE GRADE','시그널브릿지 회사소개':'ABOUT SIGNALBRIDGE','문의 | 이의제기':'CONTACT | REVIEW REQUEST',
    '서비스 안내':'SERVICE GUIDE','이전':'PREVIOUS','다음':'NEXT','닫기':'CLOSE','비교 시작':'START COMPARISON',
    '관측':'OBSERVED','유지':'CARRIED','참조':'REFERENCE','반영':'INCLUDED','제외':'EXCLUDED',
    '기업':'COMPANY','공공기관':'PUBLIC INSTITUTION','대학':'UNIVERSITY','공인':'PUBLIC FIGURE',
    '이번 주 화면이 보여주는 것':'What this week’s view shows','지수와 차트를 읽는 법':'How to read the index and charts',
    '영역별 장기 평판 성과':'Long-term relationship performance by field',
    '세 단계의 분석 깊이':'Three levels of analytical depth','관측 주기와 목적에 맞춘 다섯 가지':'Five plans by observation cycle and purpose',
    '대상과 분야를 선택합니다':'Choose fields and subjects','한 번의 분석도 가능합니다':'One-time analysis is also available',
    '필요한 분석을 단계별로 선택하세요.':'Build the analysis you need, step by step.',
    '기본 브리핑':'Basic Briefing','일반 브리핑':'Standard Briefing','스페셜 브리핑':'Special Briefing',
    '정기적으로 관측하기':'Observe regularly','한 번 분석받기':'Request one analysis','T100 맞춤 분석':'Custom T100 analysis',
    '한국어':'Korean','영어':'English','제공 언어':'Delivery language','관측 분야':'Observation field','분석 대상':'Subjects',
    '선택을 시작하세요':'Start your selection','이용 방식':'Service mode','서비스 구성이 완료되었습니다.':'Your service configuration is complete.',
    '6단계 웹 브리핑 보기 →':'Open the six-stage web briefing →','서비스 설명으로 돌아가기':'Return to service overview',
    '일반 브리핑 샘플 PDF 보기 →':'View a Standard Briefing sample PDF →','샘플 PDF 바로 보기':'Open sample PDF',
    '관계 환경을 먼저 선택하세요.':'Choose a relationship environment first.',
    '한 대상을 고르고, 같은 분야의 두 대상과 비교해 보세요.':'Choose one subject and compare it with two subjects in the same field.',
    '기업 관계를 읽는 엔진':'Read company–public relationships','공공 커뮤니케이션을 읽는 엔진':'Read public communication relationships',
    '대학 관계를 읽는 엔진':'Read university relationships','공인 관계를 읽는 엔진':'Read public-figure relationships',
    '필요한 판단의 깊이에 맞춰 선택합니다':'Choose the depth that matches the decision you need',
    '여섯 단계로 구성을 완성합니다.':'Complete your configuration in six steps.',
    '기간 단위와 조회 구간을 선택하면 해당 기간 안에서 가장 최근에 공개된 검증 스냅샷을 표시합니다. 실제 관측 기록이 없는 기간은 임의 보간하지 않고 ‘N/R’로 안내합니다. 평판 수준은 기간평균으로, 활동 발생량은 누적 총량으로 구분해 제공합니다.':'Select a time unit and date range to display the latest verified snapshot published within that period. A period without an actual observation record is shown as N/R rather than interpolated. Relationship-reputation level is reported as a period average, while activity volume is reported as a cumulative total.',
    '기업의 규모나 재무성과가 아니라, 고객·시장·사회와 만나는 과정에서 확인된 도달·반응·경험·행동·책임의 상태를 같은 분야 안에서 비교합니다.':'This is not a comparison of corporate size or financial performance. It compares observed Reach, Response, Experience, Action and Responsibility across companies within the same field.',
    '정책 성과나 기관의 우열 전체를 평가하지 않습니다. 주민·민원인·정책 수요자에게 정책이 어떻게 발견되고 이해되며 경험과 신뢰로 이어지는지를 관측합니다.':'This does not evaluate total policy performance or the overall superiority of an institution. It observes how policy is discovered and understood by residents, service users and policy stakeholders, and how that contact relates to experience and trust.',
    '교육·연구 역량 전체의 서열이 아니라, 대학이 지원자·학생·졸업생·사회와 형성하는 발견·정체성·경험·행동·책임의 상태를 관측합니다.':'This is not a ranking of total teaching or research capability. It observes how a university is discovered and identified, and how it forms experience, action and responsibility with applicants, students, graduates and society.',
    '인기투표나 팬덤 경쟁이 아닙니다. 공인이 대중에게 발견되고 반응을 얻으며, 어떤 이미지와 경험·행동·책임의 흐름으로 이어지는지를 관측합니다.':'This is not a popularity vote or a fandom contest. It observes how a public figure is discovered, how the public responds, and how that attention connects with image, experience, action and responsibility.',
    '기간 단위와 조회 구간을 선택하면 해당 기간 안에서 가장 최근에 공개된 검증 스냅샷을 표시합니다. 실제 관측 기록이 없는 기간은 임의 보간하지 않고 ‘N/R’로 안내합니다. 평판 수준은 기간평균으로, 활동 발생량은 누적 총량으로 구분해 제공합니다. UNI는 공시·대학 데이터의 갱신 주기를 고려해 기본 단위를 월간으로 표시합니다.':'Select a time unit and date range to display the latest verified snapshot published within that period. A period without an actual observation record is shown as N/R rather than interpolated. Relationship-reputation level is reported as a period average, while activity volume is a cumulative total. UNI uses a monthly default to reflect the update cycle of university disclosures and institutional data.',
    '‘THIS WEEK’는 월요일부터 현재까지 공개된 CPR·GOV·UNI·ENT의 변화를 한 화면에 모읍니다. 카드의 점수는 기준일의 관측 가능한 평판 수준이고, 화살표는 동일한 비교 조건이 확보됐을 때의 변화를 나타냅니다. 새로 관측된 대상과 축 상태가 달라진 대상은 점수 변화만으로 설명하지 않습니다. 이 페이지는 누가 더 가치 있는지를 판정하는 목록이 아니라, 이번 주에 어느 대상과 어느 축을 다시 살펴볼 필요가 있는지 알려주는 관측 요약입니다.':'THIS WEEK brings together changes published from Monday to the current day across CPR, GOV, UNI and ENT. A card score is the observable relationship-reputation level on the reference date; an arrow indicates change only when comparable conditions are available. Newly observed subjects and changes in dimension coverage are not explained by score movement alone. This page is not a list of who is more valuable. It is an observation digest showing which subjects and dimensions merit another look this week.',
    '순위를 보여주되, 순위로 평판을 단정하지 않습니다':'Show the rank, but do not reduce reputation to rank',
    'BRIDGE 브랜드평판지수는 공개자료와 공중의 관측 신호를 바탕으로 브랜드와 공중 사이의 관계 상태, 구성과 변화 방향을 반복 관측하는 관계 기반 평판지수입니다.':'The BRIDGE Brand Reputation Index repeatedly observes the state, composition and direction of relationships between a subject and its publics through verified public data and observable public signals.',
    'BRIDGE는 언급량을 평판 전체로 보지 않습니다. 도달·반응·정체성·경험·행동유발·책임과 지속을 나누어 보고, 결과를 뒷받침하는 근거의 충실성도 함께 제시합니다.':'BRIDGE does not treat mention volume as the whole of reputation. It separates Reach, Response, Identity, Experience, Action and Responsibility & Continuity, and reports the sufficiency of evidence supporting the result.',
    '순위는 정해진 기간과 공개자료 범위에서 관측된 상대적 위치입니다. 대상의 절대적 가치·능력·윤리성 전체를 판정하지 않습니다.':'Rank is a relative position observed within a defined period and public-data scope. It is not a judgement of a subject’s absolute value, total capability or morality.',
    [FOOTER_KO]:FOOTER_EN
  };

  const PAGE={
    'index.html':{
      title:'BRIDGEBRAND | Relationship Reputation Intelligence',
      exact:{'순위 뒤의 관계를 읽습니다.':'Read the relationship behind the rank.','오늘의 관계 신호를 분야별로 확인하세요.':'Explore today’s relationship signals by field.'}
    },
    'this-week.html':{
      title:'BRIDGE — THIS WEEK',
      exact:{'이번 주 관측 흐름을 한 화면에서 읽습니다.':'Read this week’s observation flow in one view.','이번 주의 대표 지수와 장기 성과는 서로 다른 시간창을 설명합니다.':'The weekly representative index and cumulative performance describe different time windows.'}
    },
    'cpr.html':{title:'CPR — Company–Public Relationship Index',hero:'CPR — Read reputation between companies and their publics'},
    'gov.html':{title:'GOV — Government Public Communication Index',hero:'GOV — Read public communication and stakeholder response'},
    'uni.html':{title:'UNI — University Relationship Reputation Index',hero:'UNI — Read the relationship between universities and their publics'},
    'star.html':{title:'ENT — Public Figure Relationship Reputation Index',hero:'ENT — Read fast-moving public attention and relationship reputation'},
    'methodology.html':{title:'BRIDGE INDEX — Methodology',hero:'Rank is not the conclusion. It is the start of interpretation.',exact:{
      '점수와 순위, 여섯 축의 구성, 시간에 따른 변화와 근거 상태를 함께 읽는 BRIDGE의 공식 안내입니다.':'The official guide to reading BRIDGE through score and rank, six-dimensional composition, change over time and evidence status.',
      '공개자료로 확인되는 평판을 반복 관측합니다':'Repeated observation of reputation supported by public data',
      'BRIDGE는 브랜드가 얼마나 발견되는지, 어떤 반응을 얻는지, 무엇으로 기억되는지, 경험과 행동으로 어떻게 이어지는지, 책임과 신뢰가 어떻게 유지되는지를 여섯 축으로 관측합니다. 공중의 마음 전체를 직접 측정하거나 기업·기관·대학·공인의 절대적 가치와 능력을 판정하는 체계는 아닙니다.':'BRIDGE uses six dimensions to observe how widely a subject is discovered, how the public responds, what the subject is remembered for, how contact becomes experience and action, and how responsibility and trust are sustained. It does not directly measure the whole of public sentiment or judge the absolute value and capability of a company, institution, university or public figure.',
      '현재 위치':'Current position','지수와 순위로 관측된 상대적 수준을 살핍니다.':'Read the relative level observed through index and rank.',
      '관계 구성':'Relationship composition','여섯 축의 강점과 제약, 연결이 덜 확인된 접점을 읽습니다.':'Read strengths, constraints and less-verified connections across six dimensions.',
      '변화 방향':'Direction of change','비교 조건과 근거 범위를 확인하며 흐름을 해석합니다.':'Interpret the flow after checking comparison conditions and evidence scope.',
      '하나의 총점 뒤에 여섯 개의 질문이 있습니다':'Six questions sit behind one composite score',
      '도달이 높다고 반응까지 긍정적인 것은 아니며, 활동이 많다고 책임 이행이 충분한 것도 아닙니다. BRIDGE는 총점을 먼저 보여주되 여섯 축을 다시 펼쳐 무엇이 현재 결과를 설명하고 무엇은 추가 확인이 필요한지 구분합니다. 두 축이 함께 높거나 낮게 나타나도 직접적인 인과관계가 확인된 것은 아닙니다.':'High Reach does not guarantee positive Response, and high activity does not prove sufficient Responsibility. BRIDGE shows the composite score, then reopens the six dimensions to distinguish what supports the current result from what still needs verification. Two dimensions appearing high or low together does not establish direct causality.',
      '오늘의 수준과 이번 주의 흐름을 나누어 봅니다':'Separate today’s level from this week’s flow',
      '점수 변화와 순위 이동은 같은 말이 아닙니다':'Score change and rank movement are not the same signal',
      '공개할 기준과 보호할 방법을 구분합니다':'Separate public criteria from protected methodology'
    }},
    'data-extraction.html':{title:'BRIDGE DATA TRACE — Evidence and Processing',hero:'Follow the evidence from source to result.',exact:{
      '출처·기준시점·대상 귀속·중복·유효기간을 확인하고, 실제 변화와 근거 범위의 변화를 구분합니다.':'Verify source, reference time, subject attribution, duplication and validity period, then separate real change from a change in evidence coverage.',
      '빠른 신호와 오래 유지되는 기반':'Fast signals and longer-lasting foundations',
      '뉴스·공식 채널·공중 반응은 비교적 빠른 변화를, 공시·교육여건·공식 통계와 평가자료는 기준기간의 기반을 설명합니다. 이들은 같은 종류의 근거가 아닙니다. 자료 유형별 활용 범위가 다르고, 모든 대상에서 모든 출처가 확보되는 것은 아닙니다. 공식 홍보 문구도 공중의 긍정 반응으로 곧바로 바꾸어 읽지 않습니다.':'News, official channels and public response describe relatively fast movement; disclosures, educational conditions, official statistics and evaluation records describe a period foundation. They are not the same kind of evidence. Each source type has a different analytical range, and not every source is available for every subject. Official promotional copy is not automatically read as positive public response.',
      '오래된 사건을 새 사건으로 만들지 않습니다':'An old event is not counted as a new event',
      '사건의 수와 확산의 크기를 구분합니다':'Separate event count from diffusion scale',
      '발견하지 못한 것과 관측하지 못한 것은 다릅니다':'Not finding a signal differs from not completing observation',
      '일주일의 두께를 함께 읽습니다':'Read the depth of the week as well as its score',
      '평판의 변화와 근거 범위의 변화를 나눠 봅니다':'Separate reputation change from evidence-scope change'
    }},
    'trust.html':{title:'BRIDGE EVIDENCE GRADE',hero:'Relationship level and evidence sufficiency are different.',exact:{
      '신뢰등급은 대상의 평판등급이 아닙니다. 이번 결과를 뒷받침하는 자료의 범위·최신성·귀속과 비교 가능성을 알려주는 정보입니다.':'Evidence grade is not a reputation grade. It reports the scope, recency, attribution and comparability of the material supporting the current result.',
      '점수 옆의 등급을 읽는 법':'How to read the grade beside a score',
      '높은 점수라도 관측기간이나 출처가 제한될 수 있습니다. 낮은 등급을 나쁜 평판으로 읽거나, 공식자료 하나가 있다는 이유만으로 모든 축의 판단을 충분하다고 보아서는 안 됩니다. 등급은 최신성·관측 범위·귀속의 명확성·자료 의존도와 함께 해석해야 합니다.':'Even a high score may rest on a limited observation period or source set. A lower grade does not mean bad reputation, and one official source does not make every dimension sufficient. Read the grade with recency, observation coverage, attribution clarity and source dependence.',
      '여섯 숫자의 근거 상태는 같지 않습니다':'The six values do not necessarily share one evidence state',
      '프로필 완성과 공개 순위는 별도 판단입니다':'Profile completion and public ranking are separate decisions',
      '설계 원칙과 현재의 구현 범위를 구분합니다':'Separate design principles from current implementation limits',
      '정확성은 수정 가능성과 함께 지킵니다':'Accuracy includes a transparent correction path'
    }},
    'about.html':{title:'About SignalBridge',hero:'We publish the rank and explain the reasons behind it.',exact:{
      '시그널브릿지는 공개자료에서 확인되는 평판 신호를 구조화해 현재 수준, 축별 구성, 변화와 근거의 범위를 함께 설명합니다.':'SignalBridge structures reputation signals verified in public data to explain current level, dimensional composition, change and evidence scope together.',
      '얼마나 많이 보이는가에서 시작해,어떤 관계를 만들고 있는가를 묻습니다.':'We begin with visibility, then ask what kind of relationship is being formed.',
      '하나의 순위를 넘어서는 분석':'Analysis beyond a single rank',
      '화제성과 규모는 브랜드를 읽는 중요한 신호지만 그것만으로 모든 관계를 설명할 수는 없습니다. 시그널브릿지는 현재의 상대적 위치와 여섯 축의 구성, 관측 가능한 변화의 방향을 함께 살핍니다. 상위 대상의 제약도, 다른 대상에서 근거로 확인되는 강점도 같은 기준으로 이야기하는 것이 우리의 분석 방향입니다.':'Attention and scale are important signals, but they cannot explain every relationship. SignalBridge reads relative position, six-dimensional composition and observable direction of change together. We apply the same standards to a leading subject’s constraints and to strengths supported by evidence in other subjects.',
      '랭킹 산업이 압축해서 버린 맥락을 복원합니다':'Restore the context compressed out of conventional rankings',
      'BRIDGE가 묻는 질문은 다릅니다':'BRIDGE asks a different question',
      '구분':'Distinguish','추적':'Trace','설명':'Explain',
      '공개 근거 기반 관계 평판 인텔리전스':'Public-evidence relationship reputation intelligence',
      '네 영역의 맥락, 여섯 축의 공통 질문':'Four field contexts, six common questions',
      '관측':'Observe','해석':'Interpret','전달':'Communicate',
      '근거에 따라 판단하고 한계를 함께 말합니다':'Make evidence-led judgements and state the limits',
      '순위표에서 끝나지 않는 이야기':'A story that does not end at the ranking table',
      '운영 주체':'Operator','분석 체계':'Analytical framework','공개 서비스':'Public service','서비스 운영과 데이터 관리':'Service operation and data governance','여섯 축으로 읽는 브랜드평판지수':'A brand reputation index read through six dimensions','현재 위치와 근거에 기반한 해석':'Interpretation based on current position and evidence'
    }},
    'intelligence.html':{
      title:'BRIDGE INTELLIGENCE — Explain the reasons behind score and rank',
      exact:{
        '점수와 순위가 달라진 이유를':'Why score and rank changed,','여섯 축으로 설명합니다.':'explained through six dimensions.',
        '선택한 대상의 현재 지수와 순위, 비교 대상과의 차이, 강하게 관측된 축과 추가 확인이 필요한 축을 한 흐름으로 읽습니다. 쉬운 해석은 숫자의 뜻을 풀어주고, 전문가 분석은 기준일·비교조건·근거 상태와 해석 범위를 함께 제시합니다.':'Read the selected subject’s current index and rank, differences from comparison subjects, strongly observed dimensions and dimensions requiring more evidence in one continuous flow. The plain-language view explains what the numbers mean; the professional view adds the reference date, comparison conditions, evidence status and interpretive limits.',
        'BRIDGE 6단계 브리핑 체험하기':'Try the BRIDGE six-stage briefing','BRIDGE 구독 구성하기':'Configure a BRIDGE subscription',
        '분야별 T100 안에서 나의 선택과 비교 대상 두 개를 같은 날짜·같은 공개 범위로 읽습니다.':'Within one field’s T100, read your selected subject and two comparison subjects using the same date and public-data scope.',
        '같은 기준일과 공개 범위에서 종합지수, 여섯 축, 활동량과 근거 상태를 나란히 봅니다. 이 비교는 인기투표나 승패 판정이 아닙니다. 어디에서 차이가 나타났고 현재 자료로 어디까지 설명할 수 있는지를 확인하는 체험입니다.':'Compare the composite index, six dimensions, activity volume and evidence status under the same date and scope. This is not a popularity vote or a contest. It shows where differences appear and how far the current evidence supports an explanation.'
      }
    },
    'subscribe.html':{
      title:'Configure a BRIDGE Subscription — Relationship Reputation Intelligence',
      exact:{
        '한 번의 결과보다':'Beyond a single result,','변화가 이어지는 과정을 관측합니다.':'observe how change continues over time.',
        '설명의 깊이, 관측 주기, 분야와 대상을 순서대로 선택하세요. 서로 다른 분야의 점수를 직접 비교하지 않으며, 각 분야의 기준과 근거 상태를 유지한 채 하나의 서비스로 구성합니다.':'Choose analytical depth, observation cycle, field and subjects in order. Scores from different fields are not directly compared; each field keeps its own criteria and evidence state within one service.',
        '기본은 한 대상의 현재 상태를 빠르게 설명합니다. 일반은 중심 대상과 비교 대상 두 개를 같은 조건에서 분석합니다. 스페셜은 일반 브리핑에 3일 흐름, 이전 PUBLICITY와 전략 선택지를 더합니다. 각 카드에서 2026년 10월 25일 기준 고정 샘플을 읽을 수 있습니다.':'Basic quickly explains one subject’s current state. Standard analyses a focal subject and two comparison subjects under the same conditions. Special adds a three-day flow, prior publicity and strategic options. Each card opens a fixed sample dated 25 October 2026.',
        '한국어와 영어 두 버전으로 제공하며 영문판의 T100 대상명은 한글 원본을 유지합니다.':'Available in Korean and English. T100 subject names remain in their original Korean form in the English edition.'
      }
    }
  };

  function replaceText(root=document.body,map={}){
    const merged={...TEXT,...map};
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(n){
      return n.parentElement&&/^(SCRIPT|STYLE|NOSCRIPT|TEXTAREA)$/.test(n.parentElement.tagName)?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT;
    }});
    const nodes=[]; while(walker.nextNode())nodes.push(walker.currentNode);
    nodes.forEach(n=>{const raw=n.nodeValue,trim=raw.trim();if(trim&&merged[trim])n.nodeValue=raw.replace(trim,merged[trim]);});
  }

  function addToggle(){
    const holder=document.querySelector('.nav-right'); if(!holder||holder.querySelector('.language-switch'))return;
    const wrap=document.createElement('div'); wrap.className='language-switch'; wrap.setAttribute('aria-label','Language');
    const make=(code,label)=>{const a=document.createElement('a');a.href='#';a.textContent=label;a.dataset.lang=code;a.className=lang===code?'active':'';a.setAttribute('aria-current',lang===code?'true':'false');a.addEventListener('click',e=>{e.preventDefault();localStorage.setItem('bridge-ui-language',code);const u=new URL(location.href);if(code==='en')u.searchParams.set('lang','en');else u.searchParams.delete('lang');location.href=u.toString();});return a;};
    wrap.append(make('ko','KR'),document.createTextNode(' | '),make('en','EN'));
    const toggle=holder.querySelector('.nav-toggle');holder.insertBefore(wrap,toggle||null);
  }

  function preserveLanguageLinks(){
    if(!isEn)return;
    document.querySelectorAll('a[href]').forEach(a=>{
      const raw=a.getAttribute('href');if(!raw||raw.startsWith('#')||/^(mailto:|tel:|javascript:|https?:)/.test(raw))return;
      const base=raw.split(/[?#]/)[0].split('/').pop().toLowerCase();if(PUBLICITY.has(base)||raw.endsWith('.pdf'))return;
      const u=new URL(raw,location.href);u.searchParams.set('lang','en');a.setAttribute('href',u.pathname.split('/').pop()+u.search+u.hash);
    });
  }

  function run(){
    document.documentElement.lang=isEn?'en':'ko';document.body.classList.toggle('language-en',isEn);addToggle();
    if(!isEn)return;
    const page=PAGE[path]||{};if(page.title)document.title=page.title;
    if(page.hero){const h=document.querySelector('h1');if(h)h.textContent=page.hero;}
    replaceText(document.body,page.exact||{});preserveLanguageLinks();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
})();
