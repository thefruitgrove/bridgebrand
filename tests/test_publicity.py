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
 def test_input_values_are_not_mutated(self):
  h=self.history();old=copy.deepcopy(h);articles_for(h,dt.date(2026,10,16));self.assertEqual(h,old)
if __name__=='__main__':unittest.main()
