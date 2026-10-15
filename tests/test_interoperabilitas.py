"""Pengujian RPI v0.4: interoperabilitas, integritas, dan kompatibilitas."""
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.dialects import mysql, mssql, oracle, postgresql
from sqlalchemy.schema import CreateTable
from nor_id.api import build_app
from nor_id.basis_data import periksa_url, sql_berhalaman
from nor_id.skema_portabel import metadata

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from impor_multibasis import impor
from sinkronisasi_data import siapkan
from build_release import create_release
from validate import read_csv


class TesRPI04(unittest.TestCase):
    def test_enam_database_didukung_tanpa_membuka_koneksi(self):
        urls = {
           'sqlite':'sqlite+pysqlite:///:memory:',
           'postgresql':'postgresql+psycopg://u:secret@localhost/rpi',
           'mysql':'mysql+pymysql://u:secret@localhost/rpi',
           'mariadb':'mariadb+pymysql://u:secret@localhost/rpi',
           'mssql':'mssql+pyodbc://u:secret@localhost/rpi?driver=ODBC+Driver+18+for+SQL+Server',
           'oracle':'oracle+oracledb://u:secret@localhost:1521/?service_name=x',
        }
        for jenis, url in urls.items():
            with self.subTest(jenis=jenis):
                self.assertEqual(periksa_url(url).get_backend_name(), jenis)
        with self.assertRaises(ValueError): periksa_url('mongodb://localhost/rpi')
        with self.assertRaises(ValueError): periksa_url('mysql+unknown://localhost/rpi')
        with self.assertRaises(RuntimeError): periksa_url('sqlite+pysqlite:////tmp/rpi-file-tidak-ada.sqlite3')

    def test_ddl_compiles_for_supported_sql_dialects(self):
        for name,d in [('postgresql',postgresql.dialect()),('mysql',mysql.dialect()),
                       ('mariadb',__import__('sqlalchemy.dialects.mysql.mariadb',fromlist=['MariaDBDialect']).MariaDBDialect()),('mssql',mssql.dialect()),
                       ('oracle',oracle.dialect())]:
            for t in metadata.sorted_tables:
                with self.subTest(database=name,table=t.name):
                    ddl=str(CreateTable(t).compile(dialect=d))
                    self.assertIn('CREATE TABLE',ddl)

    def test_pagination_sql_has_offset_fetch_for_enterprise(self):
        class C:
            def __init__(self,name): self.dialect=type('D',(),{'name':name})()
        self.assertIn('FETCH NEXT',sql_berhalaman(C('mssql'),'SELECT 1 ORDER BY x'))
        self.assertIn('FETCH NEXT',sql_berhalaman(C('oracle'),'SELECT 1 ORDER BY x'))
        self.assertIn('LIMIT',sql_berhalaman(C('postgresql'),'SELECT 1 ORDER BY x'))

    def test_portable_seed_twice_stable(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'rpi.db'
            engine=create_engine('sqlite+pysqlite:///'+str(db))
            try:
                metadata.create_all(engine)
                with engine.begin() as c: first=impor(c)
                with engine.begin() as c: second=impor(c)
                self.assertEqual(first,second)
                with engine.connect() as c:
                    self.assertEqual(c.execute(text('SELECT COUNT(*) FROM occupations')).scalar_one(),811)
                    self.assertEqual(c.execute(text('SELECT COUNT(*) FROM jabatan_nasional')).scalar_one(),3)
                    self.assertEqual(c.execute(text('SELECT COUNT(*) FROM pemetaan_internasional')).scalar_one(),0)
                    self.assertEqual(c.execute(text('PRAGMA foreign_key_check')).fetchall(),[])
                    self.assertEqual(c.execute(text('SELECT COUNT(*) FROM occupation_aliases')).scalar_one(),
                                     len({(r['occupation_id'],a.strip()) for r in read_csv(ROOT/'data/occupations.csv') for a in r['alternative_names'].split('|') if a.strip()}))
            finally: engine.dispose()

    def test_api_baru_dan_lama(self):
        with tempfile.TemporaryDirectory() as d:
            from build_sqlite import build
            db=Path(d)/'rpi.db';build(db)
            with TestClient(build_app('sqlite+pysqlite:///'+str(db))) as c:
                self.assertEqual(c.get('/healthz').json()['api_version'],'0.4.0')
                result=c.get('/v1/cari-pekerjaan',params={'kata':'guru'}).json()
                self.assertGreater(result['jumlah_ditemukan'],0)
                self.assertEqual(c.get('/v1/cari-pekerjaan?kata=%25').json()['data'],[])
                self.assertEqual(c.get('/v1/cari-pekerjaan?kata=x&batas=51').status_code,422)
                self.assertEqual(c.get('/v1/pemetaan-internasional').json()['data'],[])
                self.assertFalse(c.get('/v1/analisis/pengupahan').json()['data_tersedia'])
                self.assertEqual(c.get('/v1/occupations?limit=2').json()['pagination']['limit'],2)
                self.assertEqual(c.get('/v1/status-registri').json()['jumlah_upah_minimum'],0)

    def test_sinkronisasi_gagal_checksum_dan_dryrun_valid(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            original=(ROOT/'data'/'pemetaan_internasional.csv').read_bytes()
            (folder/'pemetaan_internasional.csv').write_bytes(original)
            manifest={'versi':'0.4.0-uji','asal_sumber':'Berkas kurasi lokal untuk tes',
                      'berkas':{'pemetaan_internasional.csv':hashlib.sha256(original).hexdigest()}}
            (folder/'manifest-sumber.json').write_text(json.dumps(manifest))
            result=siapkan(folder)
            self.assertEqual(result['modus'],'simulasi')
            self.assertEqual(result['jumlah']['occupations'],811)
            (folder/'pemetaan_internasional.csv').write_text('rusak')
            with self.assertRaisesRegex(ValueError,'Checksum'):
                siapkan(folder)

    def test_rilis_manifest_tidak_mengarang_data(self):
        with tempfile.TemporaryDirectory() as d:
            mf=create_release(output=Path(d))
            self.assertEqual(mf['version'],'0.4.0')
            self.assertEqual(mf['counts']['pemetaan_internasional'],0)
            self.assertEqual(mf['counts']['statistik_upah'],0)
            self.assertIn('pemetaan_internasional.json',mf['files'])
            for name, meta in mf['files'].items():
                self.assertEqual(hashlib.sha256((Path(d)/name).read_bytes()).hexdigest(),meta['sha256'])


if __name__=='__main__': unittest.main()
