"""Integration tests of public REST endpoints using a temporary SQLite snapshot."""
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from nor_id.api import build_app
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_sqlite import build
from validate import ROOT


class APIIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path = Path(cls.tmp.name) / 'catalog.sqlite3'
        build(path)
        cls.client = TestClient(build_app('sqlite+pysqlite:///' + str(path)))
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls.tmp.cleanup()

    def test_health_and_meta(self):
        self.assertEqual(self.client.get('/healthz').json()['status'], 'ok')
        meta = self.client.get('/v1/meta').json()
        self.assertEqual(meta['occupations'], 811)
        self.assertEqual(meta['sectors'], 39)
        self.assertEqual(meta['verified_kbji_mappings'], 0)
        self.assertEqual(meta['published_occupations'], 0)

    def test_search_pagination_and_validation(self):
        resp = self.client.get('/v1/occupations', params={'q': 'Perawat', 'limit': 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data['pagination']['total'], 1)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['record_status'], 'draft')
        self.assertEqual(data['data'][0]['kbji_mappings'], [])
        self.assertEqual(self.client.get('/v1/occupations?limit=101').status_code, 422)
        self.assertEqual(self.client.get('/v1/occupations?offset=-1').status_code, 422)
        self.assertEqual(self.client.get('/v1/occupations?q=%25').json()['pagination']['total'], 0)
        self.assertEqual(self.client.get('/v1/occupations?status=official').status_code, 422)
        self.assertEqual(self.client.get('/v1/occupations?q=%27%20OR%201%3D1%20--').json()['pagination']['total'], 0)

    def test_sector_and_missing_detail(self):
        sections = self.client.get('/v1/sectors').json()['data']
        self.assertEqual(len(sections), 39)
        self.assertEqual(sum(s['occupations_count'] for s in sections), 811)
        self.assertEqual(self.client.get('/v1/occupations/invalid').status_code, 404)
        self.assertEqual(self.client.get('/v1/occupations/ID-OCC-000001').json()['data']['occupation_id'],
                         'ID-OCC-000001')

    def test_titles_and_contexts(self):
        titles = self.client.get('/v1/job-titles').json()
        self.assertEqual(titles['pagination']['total'], 3)
        contexts = self.client.get('/v1/employment-contexts').json()['data']
        self.assertGreater(len(contexts), 0)

    def test_no_fabricated_kbji(self):
        codes = self.client.get('/v1/kbji/codes').json()
        self.assertEqual(codes['pagination']['total'], 0)
        self.assertEqual(codes['data'], [])

    def test_exports_include_all_records(self):
        export = self.client.get('/v1/exports/occupations.json')
        self.assertEqual(export.status_code, 200)
        self.assertEqual(len(export.json()['data']), 811)
        self.assertIn('attachment', export.headers['content-disposition'])
        sheet = self.client.get('/v1/exports/occupations.csv')
        self.assertEqual(sheet.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(sheet.content.decode('utf-8-sig'))))
        self.assertEqual(len(rows), 811)
        self.assertTrue(all(r['record_status'] == 'draft' for r in rows))


if __name__ == '__main__':
    unittest.main()
