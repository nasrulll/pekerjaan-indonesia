"""Pengujian kontrak berbahasa Indonesia dan pembatasan data pengupahan."""
import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from nor_id.api import build_app

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_sqlite import build
from build_release import create_release
from validate import check


class TesPengembanganBahasaIndonesia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbfile = Path(self.tmp.name) / 'rpi.sqlite3'
        build(self.dbfile)
        self.client = TestClient(build_app('sqlite+pysqlite:///' + str(self.dbfile)))
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None,None,None)
        self.tmp.cleanup()

    def test_tabel_baru_tidak_merusak_data_awal(self):
        with sqlite3.connect(self.dbfile) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM occupations').fetchone()[0],811)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM jabatan_nasional').fetchone()[0],3)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM wilayah_administratif').fetchone()[0],0)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM statistik_upah').fetchone()[0],0)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM upah_minimum').fetchone()[0],0)
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_api_jabatan_indonesia_dan_kompatibilitas_lama(self):
        jabatan=self.client.get('/v1/jabatan').json()
        self.assertEqual(jabatan['pagination']['total'],3)
        self.assertTrue(all(x['status_verifikasi']=='draf' for x in jabatan['data']))
        self.assertEqual(self.client.get('/v1/jabatan',params={'nama':'%'}).json()['pagination']['total'],0)
        self.assertEqual(self.client.get('/v1/jabatan?batas=101').status_code,422)
        self.assertEqual(self.client.get('/v1/job-titles').json()['pagination']['total'],3)
        self.assertEqual(self.client.get('/v1/meta').json()['occupations'],811)
        lokal = self.client.get('/v1/pekerjaan',params={'nama':'guru','batas':5}).json()
        self.assertIn('nama_pekerjaan',lokal['data'][0])
        self.assertIn('status_data',lokal['data'][0])
        self.assertEqual(self.client.get('/v1/pekerjaan/ID-OCC-000001').status_code,200)
        self.assertEqual(self.client.get('/v1/pekerjaan/tidak-ada').status_code,404)
        self.assertEqual(self.client.get('/v1/pekerjaan?nama=%25').json()['pagination']['total'],0)
        self.assertEqual(self.client.get('/v1/status-registri').json()['jumlah_upah_minimum'],0)
        self.assertEqual(self.client.get('/healthz').json()['api_version'],'0.3.0')

    def test_tidak_menciptakan_angka_upah(self):
        for uri in ('/v1/wilayah','/v1/upah-minimum?tahun=2026','/v1/statistik-upah?tahun=2026'):
            hasil=self.client.get(uri)
            self.assertEqual(hasil.status_code,200)
            self.assertEqual(hasil.json()['data'],[])
            self.assertFalse(hasil.json()['data_tersedia'])
        self.assertEqual(self.client.get('/v1/upah-minimum?jenis_upah=lainnya').status_code,422)
        self.assertEqual(self.client.get('/v1/statistik-upah?metrik=pendapatan').status_code,422)

    def test_endpoint_tidak_membocorkan_data_draf(self):
        # Data buatan HANYA untuk uji API; tidak menjadi data proyek yang dipublikasikan.
        with sqlite3.connect(self.dbfile) as con:
            con.execute("INSERT INTO wilayah_administratif VALUES (?,?,?,?,?,?,?,?)",
                        ('UJI','000','Provinsi Uji','provinsi',None,'CURATED-BOOTSTRAP','draf',None))
            con.execute("INSERT INTO upah_minimum VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        ('UJI-001','UJI','000',2026,'UMP',1000000,'2026-01-01','CURATED-BOOTSTRAP','draf',None,'Uji internal'))
            con.execute("INSERT INTO statistik_upah VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        ('UJI-002','UJI','000',2026,None,None,'rata_rata',900000,'per_bulan','semua','estimasi',None,'CURATED-BOOTSTRAP','draf',None,'Uji internal'))
        self.assertEqual(self.client.get('/v1/wilayah').json()['data'],[])
        self.assertEqual(self.client.get('/v1/upah-minimum').json()['data'],[])
        self.assertEqual(self.client.get('/v1/statistik-upah').json()['data'],[])

    def test_fixture_terverifikasi_terlihat_dan_terlabel(self):
        # Seluruh kode/nominal di bawah SINTETIS dan hanya tersimpan di tmp test.
        with sqlite3.connect(self.dbfile) as con:
            con.execute("INSERT INTO data_sources VALUES (?,?,?,?,?,?,?)",
                        ('UJI-DATA','Sumber pengujian, bukan dokumen resmi','Penerbit Uji',
                         'Uji-1','https://example.invalid/uji','official','Hanya data tes'))
            con.execute("INSERT INTO wilayah_administratif VALUES (?,?,?,?,?,?,?,?)",
                        ('KODE-UJI','000','Provinsi Sintetis','provinsi',None,'UJI-DATA','terverifikasi','2026-01-01'))
            con.execute("INSERT INTO wilayah_administratif VALUES (?,?,?,?,?,?,?,?)",
                        ('KODE-UJI','001','Kota Sintetis','kota','000','UJI-DATA','terverifikasi','2026-01-01'))
            con.execute("INSERT INTO upah_minimum VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        ('UPAH-UJI','KODE-UJI','000',2025,'UMP',123456,'2025-01-01','UJI-DATA','terverifikasi','2026-01-01','UJI'))
            con.execute("INSERT INTO statistik_upah VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        ('STAT-UJI','KODE-UJI','001',2025,None,None,'rata_rata',654321,'per_bulan','formal',
                         'survei',100,'UJI-DATA','terverifikasi','2026-01-01','UJI'))
        minimum=self.client.get('/v1/upah-minimum',params={'tahun':2025}).json()
        self.assertEqual(minimum['pagination']['total'],1)
        self.assertEqual(minimum['data'][0]['nilai_rupiah'],123456)
        self.assertEqual(minimum['data'][0]['jenis_upah'],'UMP')
        self.assertEqual(self.client.get('/v1/upah-minimum?tahun=2026').json()['data'],[])
        statistik=self.client.get('/v1/statistik-upah?metrik=rata_rata').json()
        self.assertEqual(statistik['pagination']['total'],1)
        self.assertEqual(statistik['data'][0]['jenis_data'],'survei')
        self.assertEqual(statistik['data'][0]['jumlah_sampel'],100)
        self.assertEqual(self.client.get('/v1/wilayah').json()['pagination']['total'],2)

    def test_rilis_csv_json_sqlite_dan_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            hasil=create_release(output=Path(tmp))
            self.assertEqual(hasil['version'],'0.3.0')
            self.assertEqual(hasil['counts']['jabatan_nasional'],3)
            self.assertEqual(json.loads((Path(tmp)/'statistik_upah.json').read_text()),[])
            with (Path(tmp)/'jabatan_nasional.csv').open(encoding='utf-8') as f:
                self.assertEqual(len(list(csv.DictReader(f))),3)
            self.assertIn('wilayah_administratif.json',hasil['files'])
            self.assertIn('pekerjaan.csv',hasil['files'])
            self.assertIn('nama_pekerjaan',json.loads((Path(tmp)/'pekerjaan.json').read_text())[0])

    def test_validasi_data_bawaan(self):
        galat,stats=check(ROOT)
        self.assertEqual(galat,[])
        self.assertEqual(stats['upah_minimum'],0)
        self.assertEqual(stats['statistik_upah'],0)


if __name__ == '__main__':
    unittest.main()
