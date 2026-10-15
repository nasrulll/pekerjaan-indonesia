"""Regression tests for offline snapshots and PostgreSQL loader query creation."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_release import create_release
from load_postgres import rows_for, statements
from validate import ROOT


class MultiplatformTests(unittest.TestCase):
    def test_release_has_all_formats_and_verified_sha256(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            manifest = create_release(output=out)
            self.assertEqual(manifest['counts']['occupations'], 811)
            for name, info in manifest['files'].items():
                actual = (out / name).read_bytes()
                self.assertEqual(hashlib.sha256(actual).hexdigest(), info['sha256'])
                self.assertEqual(len(actual), info['size_bytes'])
            self.assertEqual(json.loads((out/'occupations.json').read_text()) [0]['status'], 'draft')

    def test_pg_sql_upsert_is_parameterized(self):
        rows = rows_for('occupations', ROOT / 'data/occupations.csv')
        statement, values = statements('occupations', rows, 'occupation_id')
        self.assertEqual(len(values), 811)
        self.assertIn('ON CONFLICT (occupation_id) DO UPDATE', statement)
        self.assertNotIn('Analis kebijakan', statement)
        self.assertEqual(statement.count('%s'), len(rows[0]))

    def test_pg_loader_rejects_unexpected_columns(self):
        with self.assertRaises(ValueError):
            statements('occupations', [{'occupation_id': 'ID-OCC-999999', 'unexpected': 'x'}],
                       'occupation_id')


if __name__ == '__main__':
    unittest.main()
