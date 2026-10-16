import copy
import datetime as dt
import json
import unittest
from pathlib import Path
from publicity.generate import edition,freeze,articles_for,domain_content,DOMAINS,PUBLIC_FIELDS

class PublicityTests(unittest.TestCase):
 def history(self,date='2026-10-16'):
  records=[]
  for d in DOMAINS:
   for i in range(3):
    records.append({'domain':d,'ranking_type':'T100','as_of_date':date,'external_id':d+str(i),'name':'대상'+str(i),'rank':i+1,'score':70-i,'daily_index':70-i,'weekly_index':70-i,'trust_grade':'B','activity_points':0,'axis_scores':dict(B=65,R=50,I=50,D=70,G=60,E=80),'axis_status':dict(B='observed',R='reference',I='reference',D='maintained',G='observed',E='maintained'),'methodology_version':'2026.10-v5-beta1','history_type':'daily_observation','secret_formula':'NEVER EXPOSE'})
  return {'rankings':records}
 def test_kst_dates_and_week_42_monday_belongs_to_previous_week(self):
  f=edition(dt.date(2026,10,16));m=edition(dt.date(2026,10,19))
  self.assertEqual(f['scheduled_at'].isoformat(),'2026-10-16T12:00:00+09:00')
  self.assertEqual(m['week'],'2026-W42');self.assertEqual(m['through'],dt.date(2026,10,18));self.assertEqual(m['slot'],'OVERALL')
 def test_friday_four_and_monday_one(self):
  a,s=articles_for(self.history(),dt.date(2026,10,16));self.assertEqual({x['domain'] for x in a},set(DOMAINS))
  b,t=articles_for(self.history('2026-10-18'),dt.date(2026,10,19));self.assertEqual(len(b),1);self.assertEqual(b[0]['domain'],'ALL')
 def test_old_data_cannot_be_published_as_friday(self):
  with self.assertRaisesRegex(ValueError,'required observation date'):articles_for(self.history('2026-10-15'),dt.date(2026,10,16))
 def test_snapshot_is_allowlisted_and_order_independent(self):
  h=self.history();a,s=articles_for(h,dt.date(2026,10,16));h['rankings'].reverse();b,t=articles_for(h,dt.date(2026,10,16))
  self.assertEqual(a[0]['snapshot_hash'],b[0]['snapshot_hash']);self.assertNotIn('secret_formula',json.dumps(s));self.assertNotIn('NEVER EXPOSE',json.dumps(a))
 def test_duplicates_and_mixed_methodology_block(self):
  h=self.history();h['rankings'].append(h['rankings'][0])
  with self.assertRaisesRegex(ValueError,'Duplicate'):articles_for(h,dt.date(2026,10,16))
  h=self.history();h['rankings'][0]['methodology_version']='2026.10-v5-beta2'
  with self.assertRaisesRegex(ValueError,'Mixed'):articles_for(h,dt.date(2026,10,16))
 def test_reference_values_are_not_strength_or_weakness(self):
  a,s=articles_for(self.history(),dt.date(2026,10,16));text=json.dumps(a,ensure_ascii=False)
  self.assertNotIn('반응 50.0점이',text);self.assertNotIn('평판이 상승',text)
  self.assertIn('활동이 전혀 없었다는 증명이 아니라',text)
 def test_example_is_distinct_from_formal(self):
  a,s=articles_for(self.history('2026-10-14'),dt.date(2026,10,14),True)
  self.assertEqual(len(a),1);self.assertTrue(a[0]['is_example']);self.assertTrue(a[0]['id'].endswith('-example'));self.assertEqual({r['domain'] for r in s['rows']},{'CPR'})
 def test_invalid_axes_and_unvalidated_estimates_block(self):
  h=self.history();h['rankings'][0]['axis_scores']['E']=float('nan')
  with self.assertRaisesRegex(ValueError,'Invalid axis'):articles_for(h,dt.date(2026,10,16))
  h=self.history();h['rankings'][0]['axis_status']['E']='estimated'
  with self.assertRaisesRegex(ValueError,'Unvalidated estimated'):articles_for(h,dt.date(2026,10,16))
 def test_low_responsibility_not_described_as_high(self):
  h=self.history()
  for r in h['rankings']:r['axis_scores']['E']=13.3
  a,s=articles_for(h,dt.date(2026,10,16))
  self.assertNotIn('두 축의 값이 높다는',json.dumps(a,ensure_ascii=False))
 def test_reference_only_profile_cannot_be_interpreted_as_public_score(self):
  h=self.history();h['rankings'][0]['axis_status']={a:'reference' for a in 'BRIDGE'}
  with self.assertRaisesRegex(ValueError,'Insufficient measured axes'):articles_for(h,dt.date(2026,10,16))
 def test_ent_sample_and_news_attribution(self):
  a,s=articles_for(self.history('2026-10-14'),dt.date(2026,10,14),True,'ENT')
  self.assertEqual(a[0]['domain'],'ENT');self.assertEqual({r['domain'] for r in s['rows']},{'ENT'})
  prose=' '.join(t for section in a[0]['payload']['sections'] for t in section['paragraphs'])
  self.assertEqual(prose.count('시그널브릿지(SignalBridge) BRIDGE 브랜드평판지수 INDEX에 따르면'),1)
 def test_editorial_standard_has_exactly_seven_paragraphs(self):
  articles,_=articles_for(self.history(),dt.date(2026,10,16))
  for article in articles:
   payload=article['payload']
   self.assertEqual(payload['template_version'],'publicity-rules-2.0')
   self.assertEqual(sum(len(s['paragraphs']) for s in payload['sections']),7)
   self.assertEqual([len(s['paragraphs']) for s in payload['sections']],[2,2,3])
   self.assertIn('2026년 10월 16일',payload['sections'][0]['paragraphs'][0])
   self.assertIn('해당 분야 전체의 절대적 수준을 대변하지 않는다',payload['sections'][0]['paragraphs'][0])
   self.assertIn('향후 순위 상승을 예고하는 것은 경계해야 한다',payload['sections'][1]['paragraphs'][1])
 def test_korean_particles_do_not_repeat_known_errors(self):
  h=self.history()
  names={'CPR':'디어유','GOV':'진주시','UNI':'고려대학교','ENT':'방탄소년단'}
  for row in h['rankings']:
   if row['rank']==1:row['name']=names[row['domain']]
  articles,_=articles_for(h,dt.date(2026,10,16))
  prose=json.dumps(articles,ensure_ascii=False)
  for bad in ('디어유이','디어유은','진주시이','고려대학교이','고려대학교은','방탄소년단가'):
   self.assertNotIn(bad,prose)
 def test_public_article_hides_internal_snapshot_identifier(self):
  source=(Path(__file__).resolve().parents[1]/'site/publicity.js').read_text()
  self.assertNotIn('입력 식별:',source);self.assertNotIn('작성 시점의 입력본',source)
 def test_input_values_are_not_mutated(self):
  h=self.history();old=copy.deepcopy(h);articles_for(h,dt.date(2026,10,16));self.assertEqual(h,old)
if __name__=='__main__':unittest.main()
