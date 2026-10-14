import datetime as dt
import unittest
from bridge_pipeline.run import publish_daily_beta
class PublicationGuardTest(unittest.TestCase):
 def test_only_current_eligible_entity_ids_are_published(self):
  class DB:
   def __init__(self):self.calls=[]
   def select(self,table,query):
    if table=='bridge_scores':return [{'entity_id':'current'}]
    if table=='bridge_rankings':
     assert 'entity_id=in.(current)' in query
     return [{'id':'rank'}]
   def patch(self,table,values,query):self.calls.append(query)
  db=DB();publish_daily_beta(db,dt.date(2026,10,14))
  self.assertEqual(len(db.calls),1);self.assertIn('entity_id=in.(current)',db.calls[0])
 def test_no_current_eligible_scores_blocks_publication(self):
  class DB:
   def select(self,*args):return []
   def patch(self,*args):raise AssertionError('must not publish')
  with self.assertRaises(RuntimeError):publish_daily_beta(DB(),dt.date(2026,10,14))
