"""Run with python -m unittest discover -s tests -v"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate import ROOT,check,read_csv
from build_sqlite import build
from search import search
from export_json import export

class CatalogTest(unittest.TestCase):
    def test_core_validation(self):
        errors,stats=check()
        self.assertEqual(errors,[])
        self.assertGreaterEqual(stats['occupations'],800)
        self.assertEqual(stats['major_groups'],10)
    def test_no_unverified_official_codes(self):
        self.assertEqual(len(read_csv(ROOT/'data/kbji_mappings.csv')),0)
    def test_sqlite_search(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'test.sqlite3'
            build(db)
            found=search(db,'Perawat')
            self.assertTrue(any(x['preferred_name_id']=='Perawat' for x in found))
            self.assertTrue(all(x['kbji_verified_codes'] is None for x in found))
    def test_json_export(self):
        with tempfile.TemporaryDirectory() as d:
            count,path=export(output=Path(d)/'catalog.json')
            self.assertGreater(count,800)
            self.assertIn('Guru sekolah dasar',path.read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()
