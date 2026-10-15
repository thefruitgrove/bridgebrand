import json
import tempfile
import unittest
from pathlib import Path
from presentation.home import published_rows,render_home
from presentation.public_copy import FOOTER_COPY

class PublicCopyTests(unittest.TestCase):
 def test_home_uses_only_published_date_and_t100(self):
  row={'as_of_date':'2026-10-15','ranking_type':'T100','domain':'CPR','name':'공개 대상','score':71.58,'rank':1,'previous_rank':None}
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'latest.json'
   path.write_text(json.dumps({'asOfDate':'2026-10-15','rankings':[row,{**row,'name':'과거값','as_of_date':'2026-10-14'},{**row,'name':'다른 모집단','ranking_type':'BC50'}]}))
   output=render_home(published_rows(path))
   self.assertIn('공개 대상',output);self.assertIn('71.6',output)
   self.assertNotIn('과거값',output);self.assertNotIn('다른 모집단',output)
  self.assertIn('공개 적격 자료를 확인 중입니다.',render_home([]))
 def test_shared_footer_on_every_generated_page(self):
  root=Path(__file__).resolve().parents[1]/'site'
  for path in list(root.glob('*.html'))+list((root/'site_fix').glob('*.html')):
   content=path.read_text()
   if '<footer>' in content:
    self.assertIn(FOOTER_COPY,content,str(path))
    self.assertNotIn('왜곡 없는 브랜드의 본연의 가치',content,str(path))
if __name__=='__main__':unittest.main()
