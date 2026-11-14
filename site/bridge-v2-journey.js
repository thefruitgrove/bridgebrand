/* BRIDGEBRAND 2.0 — progressive disclosure, no score or server mutations.
   Search -> MY PICK -> same-field near-rank peer suggestions -> live briefing ->
   service enquiry. All comparisons remain explicitly user-confirmed.
*/
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const onIntelligence = !!$('trioPick1');
  const onBriefing = !!$('trialConversion');

  function chooseNeighbours() {
    const select = $('trioPick1'), a = $('trioPick2'), b = $('trioPick3');
    const status = $('bridgePeerStatus');
    if (!select || !a || !b || !status) return;
    if (!select.value) {
      status.textContent='먼저 MY PICK을 선택해 주세요.';
      select.focus();
      return;
    }
    const choices = Array.from(select.options).filter(opt=>opt.value&&!opt.disabled&&opt.dataset?.example!=='true');
    const chosen = choices.findIndex(opt=>opt.value===select.value);
    if(chosen<0 || choices.length<3){
      status.textContent='현재 공개된 같은 분야 비교 후보가 부족합니다.';
      return;
    }
    const proposals=choices
      .map((option,index)=>({value:option.value,index,distance:Math.abs(index-chosen)}))
      .filter(opt=>opt.value!==select.value)
      .sort((x,y)=>x.distance-y.distance || x.index-y.index)
      .slice(0,2);
    if(proposals.length!==2 || proposals[0].value===proposals[1].value)return;
    // Disabling is managed by the unmodified Intelligence selection engine;
    // trigger its normal change callbacks after each real choice.
    a.value=proposals[0].value;
    a.dispatchEvent(new Event('change',{bubbles:true}));
    b.value=proposals[1].value;
    b.dispatchEvent(new Event('change',{bubbles:true}));
    status.textContent='같은 분야에서 가까운 순위의 두 대상을 넣었습니다. 실제 경쟁관계를 판정한 추천은 아닙니다. 원하면 자유롭게 변경하세요.';
  }

  if(onIntelligence){
    const button=$('bridgePeerSuggest');
    const status=$('bridgePeerStatus');
    if(button && status){
      button.addEventListener('click',chooseNeighbours);
      const pick=$('trioPick1');
      pick.addEventListener('change',()=>{
        status.textContent=pick.value?'비교 대상은 직접 선택하거나 아래 참고 후보를 적용할 수 있습니다.':'먼저 MY PICK을 선택해 주세요.';
      });
    }
    // The page already supports a preselected MY PICK from the public homepage.
    const params=new URLSearchParams(location.search);
    if(params.get('pick') && params.get('field')) {
      const banner=$('bridgePrefilledStatus');
      if(banner)banner.textContent='홈페이지에서 선택한 대상이 MY PICK에 연결됩니다. 비교 대상 두 곳을 추가해 분석을 시작하세요.';
    }
  }

  if(onBriefing){
    const conversion=$('trialConversion');
    conversion.addEventListener('click',ev=>{
      const link=ev.target.closest('a[href^="subscribe.html"]');
      if(!link)return;
      const params=new URLSearchParams(location.search);
      if(!['CPR','GOV','UNI','ENT'].includes(params.get('field')))return;
      const href=new URL(link.getAttribute('href'),location.href);
      href.searchParams.set('field',params.get('field'));
      const target=$('reportPick')?.textContent?.trim();
      if(target && !['—','-','불러오는 중','미확인'].includes(target)){
        href.searchParams.set('targets',target.slice(0,100));
      }
      if(params.get('language')==='영어' || params.get('language')==='English'){
        href.searchParams.set('language','영어');
      }
      // No payment/capture endpoints; the subscription configurator is not checkout.
      link.href=href.toString();
    });
  }
})();
