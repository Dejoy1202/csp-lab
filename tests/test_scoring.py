import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("scoring",Path(__file__).resolve().parents[1]/"worker/scoring.py")
scoring=importlib.util.module_from_spec(spec);spec.loader.exec_module(scoring)

class ScoringTests(unittest.TestCase):
    def test_bundle_requires_all_cases_and_awards_once(self):
        cases=[{"status":"AC","score":20,"subtask_key":None},
               {"status":"AC","score":0,"subtask_key":"s1"},
               {"status":"WA","score":0,"subtask_key":"s1"}]
        self.assertEqual(scoring.score_results(cases,[{"subtask_key":"s1","score":80}])[1],20)
        cases[-1]["status"]="AC"
        status,score,groups=scoring.score_results(cases,[{"subtask_key":"s1","score":80}])
        self.assertEqual((status,score),("AC",100));self.assertEqual(groups[0]["score"],80)
    def test_empty_group_is_never_free_points(self):
        self.assertEqual(scoring.score_results([],[{"subtask_key":"s1","score":100}])[1],0)

if __name__=="__main__":unittest.main()
