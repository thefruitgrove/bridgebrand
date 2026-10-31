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
    'methodology.html':{title:'BRIDGE INDEX — Methodology',exact:{'BRIDGE는 무엇을 측정하는가':'What BRIDGE measures','여섯 축의 공식 정의':'Official definitions of the six dimensions','지수 산출 구조':'Index calculation structure'}},
    'data-extraction.html':{title:'BRIDGE DATA TRACE — Evidence and Processing',exact:{'데이터는 어떻게 수집되고 정제되는가':'How data are collected and processed','근거 원장과 중복 제거':'Evidence ledger and deduplication','관측·유지·참조':'Observed, Carried and Reference'}},
    'trust.html':{title:'BRIDGE EVIDENCE GRADE',exact:{'신뢰등급은 평판등급이 아닙니다':'Evidence grade is not a reputation grade','근거의 범위와 품질을 함께 읽습니다':'Read evidence scope and quality together'}},
    'about.html':{title:'About SignalBridge',exact:{'순위 뒤의 관계를 설명합니다':'We explain the relationship behind the rank','시그널브릿지는 무엇을 하는가':'What SignalBridge does','운영 주체':'Operator','분석 체계':'Analytical framework','공개 서비스':'Public service','서비스 운영과 데이터 관리':'Service operation and data governance','여섯 축으로 읽는 브랜드평판지수':'A brand reputation index read through six dimensions','현재 위치와 근거에 기반한 해석':'Interpretation based on current position and evidence'}},
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
