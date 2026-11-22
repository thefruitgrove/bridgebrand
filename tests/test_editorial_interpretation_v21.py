from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class EditorialInterpretationV21Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js=(ROOT/'site/briefing.js').read_text()
        cls.css=(ROOT/'site/bridge-v2-final-polish.css').read_text()
        cls.html=(ROOT/'site/briefing.html').read_text()
    def test_source_has_shared_data_driven_interpretation(self):
        for phrase in ('fieldPulseStory=lines;', 'function kTopic(', 'function indexedSubjectBrief(', 'function pairInsight(', 'function renderPairAnalysis('):
            self.assertIn(phrase,self.js)
        self.assertIn('current',self.js.lower())
        self.assertIn('activityStoryWeb[1]=activityStory[0]',self.js)
    def test_selection_and_pair_contract(self):
        self.assertIn('position-row-mypick',self.js)
        self.assertIn('새로운 결합점수를 산출하기보다는',self.js)
        self.assertIn('실무적으로는',self.js)
        self.assertIn('활용 제안',self.js)
        self.assertIn('function reportDisplayName(',self.js)
        self.assertIn('20261122-editorial-v21',self.html)
        self.assertIn('#pickAnalysisCopy blockquote',self.css)
    def test_score_logic_not_replaced_by_editorial(self):
        self.assertIn("const valid=(e,a)=>",self.js)
        self.assertIn("data.dataStatus!=='published'",self.js)
        self.assertIn("const PAIR_RULES=[",self.js)
        self.assertIn("if(IS_ENGLISH){buildEnglishPrintReport();return;}",self.js)
        self.assertIn("reportMode==='basic'?18:(IS_ENGLISH?29:33)",self.js)
if __name__=='__main__':unittest.main()
