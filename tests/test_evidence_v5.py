import datetime as dt
import unittest
from bridge_pipeline.evidence_v5 import collection_states,valid_signal,unique_signals,profile,comparison,event_activity,weighted_level,carry_valid
from bridge_pipeline.verify_gov_channels import links
D=dt.date(2026,10,14)
class EvidenceV5Test(unittest.TestCase):
 def test_legacy_success_does_not_prove_target_absence(self):
  self.assertEqual(collection_states([{'source_id':'news','status':'success','finished_at':'x','window_start':'2026-10-14','window_end':'2026-10-15','diagnostics':{}}],D),{})
 def test_failed_latest_run_overrides_previous_success(self):
  runs=[{'source_id':'news','status':'success','started_at':'a','finished_at':'x','window_start':'2026-10-14','window_end':'2026-10-15','diagnostics':{'entity_results':{'e':{'status':'success'}}}},
        {'source_id':'news','status':'failed','started_at':'b','finished_at':'x','window_start':'2026-10-14','window_end':'2026-10-15','diagnostics':{'entity_results':{'e':{'status':'failed'}}}}]
  self.assertEqual(collection_states(runs,D)[('e','news')]['status'],'failed')
 def test_expired_and_future_evidence_rejected(self):
  self.assertFalse(valid_signal({'source_id':'google_news_rss','occurred_at':'2026-09-01'},D))
  self.assertFalse(valid_signal({'source_id':'google_news_rss','occurred_at':'2026-10-15'},D))
  self.assertFalse(valid_signal({'source_id':'google_news_rss','occurred_at':'2026-10-13','expires_at':'2026-10-14'},D))
 def test_same_title_syndication_not_extra_axis_event(self):
  raw={'a':{'title':'기업A 신제품 출시 - 신문A'},'b':{'title':'기업A 신제품 출시 - 신문B'}}
  signals=[{'entity_id':'e','axis':'B','signal_type':'visibility','raw_item_id':k,'occurred_at':'2026-10-14','confidence':.7} for k in raw]
  self.assertEqual(len(unique_signals(signals,raw)),1)
 def test_reference_profile_is_numeric_but_not_observed(self):
  p=profile([{'axis':'B','score':80,'status':'measured','diagnostics':{}},{'axis':'D','score':70,'status':'carried','diagnostics':{}}],D)
  self.assertEqual(len(p['axis_scores']),6);self.assertEqual(p['axis_scores']['R'],50)
  self.assertEqual(p['axes_available'],2);self.assertEqual(p['axis_status']['D'],'maintained');self.assertEqual(p['reference_axes_count'],4)
 def test_event_multi_axis_never_multiplies_activity(self):
  e={'entity_id':'e','event_key':'one','occurred_at':'2026-10-13T20:00:00Z','review_status':'auto','action_strength':10,'confidence':.6}
  self.assertEqual(event_activity([e,e],D),{'e':6})
  self.assertEqual(event_activity([dict(e,review_status='pending')],D),{})
 def test_quality_weighted_mean_and_missing_not_zero(self):
  self.assertEqual(weighted_level([{'score':80,'confidence_score':100},{'score':40,'confidence_score':50},{'score':None}]),66.67)
 def test_scope_and_method_changes_disclosed(self):
  a={'axes_used':['B','R','D'],'methodology_version':'5'};b={'axes_used':['B','R'],'methodology_version':'5'}
  self.assertEqual(comparison(a,b),'scope_expanded');self.assertEqual(comparison(a,dict(b,methodology_version='4')),'methodology_changed')
 def test_carry_never_refreshes_expiry(self):
  row={'entity_id':'e','axis':'B','score':60,'status':'carried','as_of_date':'2026-10-13','diagnostics':{'source_id':'google_news_rss','validity_anchor':'2026-09-01'}}
  self.assertEqual(carry_valid([row],D,set()),[])
 def test_ownership_links_exclude_watch_and_shorts(self):
  x=links('https://youtube.com/watch?v=x https://youtube.com/shorts/x https://youtube.com/@official/about')
  self.assertEqual(list(x),[('handle','@official')])
if __name__=='__main__':unittest.main()

class ScoreIntegrationV5Test(unittest.TestCase):
 def test_complete_score_metrics_and_lineage_with_real_contract_shape(self):
  from unittest.mock import patch
  from bridge_pipeline.run import score_day,load_methodology
  from bridge_pipeline.audit_v5 import audit
  import tempfile
  from pathlib import Path
  cfg=load_methodology()
  class DB:
   def __init__(self):
    self.data={'bridge_entities':[{'id':'e','external_id':'CPR-A','domain':'CPR','subcategory':'BC50','name':'기업A'}],
      'bridge_axis_observations':[{'entity_id':'e','axis':'D','score':80,'confidence':.95,'coverage':1,'source_families':1,'evidence_count':1,'freshness_days':2,'status':'carried','as_of_date':'2026-10-14','methodology_version':cfg['version'],'diagnostics':{'source_id':'opendart_financials','raw_item_id':'rawbase'}}],
      'bridge_raw_items':[{'id':'raw','title':'기업A 출시 - 매체A','published_at':'2026-10-14T00:00:00Z','payload':{}},{'id':'rawbase','title':'기초','payload':{'entity_id':'e'}}],
      'bridge_signals':[{'id':'sig','entity_id':'e','raw_item_id':'raw','axis':'B','signal_type':'qualified_visibility','direction':1,'magnitude':1,'confidence':.7,'occurred_at':'2026-10-14T00:00:00Z','source_id':'google_news_rss','review_status':'auto'}],
      'bridge_collection_runs':[{'source_id':'google_news_rss','started_at':'2026-10-14','finished_at':'2026-10-14','status':'success','window_start':'2026-10-14','window_end':'2026-10-15','diagnostics':{'entity_results':{'e':{'status':'success'}}}}],
      'bridge_event_ledger':[],'bridge_scores':[],'bridge_rankings':[],'bridge_index_metrics':[]}
   def select(self,t,q):
    data=self.data.get(t,[])
    if 'as_of_date=lt.2026-10-14' in q:return []
    return data
   def patch(self,*a):pass
   def upsert(self,t,rows,conflict):
    fields=conflict.split(',');data=self.data.setdefault(t,[])
    for row in rows:
     k=tuple(row.get(x) for x in fields)
     data[:]=[x for x in data if tuple(x.get(y) for y in fields)!=k];data.append(row)
    return rows
  db=DB();score_day(db,D)
  score=db.data['bridge_scores'][0]
  self.assertEqual(score['diagnostics']['axis_profile']['axis_status']['I'],'reference')
  self.assertIsNone(db.data['bridge_index_metrics'][0]['wow_delta'])
  self.assertEqual(db.data['bridge_index_metrics'][0]['activity_points'],0)
  with tempfile.TemporaryDirectory() as tmp, patch('bridge_pipeline.audit_v5.ROOT',Path(tmp)):
   self.assertTrue(audit(db,D)['ok'])
