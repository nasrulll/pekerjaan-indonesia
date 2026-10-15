"""Pengujian API historis menggunakan kode dan upah SINTETIS saja."""
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert, update

from nor_id.api import build_app
from nor_id.skema_histori import metadata_histori, sumber, wilayah, taksonomi_kbji, keputusan

URL_K = "/v1/kbji/terverifikasi"
URL_W = "/v1/wilayah-historis/terverifikasi"
URL_U = "/v1/upah-minimum-historis/terverifikasi"
SETUJU = {"RPI_PUBLIKASI_HISTORIS": "aktif",
          "RPI_SUMBER_DISETUJUI_PUBLIK": "SUM-K,SUM-W,SUM-U"}


class TestAPIHistoris(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.url = "sqlite+pysqlite:///" + str(Path(self.tmp.name) / "kandidat.sqlite3")
        engine = create_engine(self.url)
        metadata_histori.create_all(engine)
        with engine.begin() as c:
            for identity, kind, edition in (
                ("SUM-K", "klasifikasi_kbji", "E-KBJI"),
                ("SUM-W", "kode_wilayah", "E-WIL"),
                ("SUM-U", "upah_minimum", "2025"),
                ("SUM-D", "klasifikasi_kbji", "E-KBJI"),
            ):
                c.execute(insert(sumber).values(
                    id_sumber=identity, jenis_sumber=kind, penerbit="Penerbit Sintetis",
                    judul="Dokumen contoh, bukan resmi", edisi=edition,
                    url_resmi="https://example.org/dokumen-uji", sha256_berkas_asli="a" * 64,
                    izin_distribusi="diizinkan", rujukan_izin="https://example.org/izin-uji",
                    status_verifikasi="terverifikasi", peninjau="Reviewer uji",
                    tanggal_verifikasi=date(2026, 10, 15),
                ))
            for code, parent, level, status in (
                ("1", None, 1, "terverifikasi"),
                ("11", "1", 2, "terverifikasi"),
                ("12", "1", 2, "ditinjau"),
            ):
                c.execute(insert(taksonomi_kbji).values(
                    edisi="E-KBJI", kode=code, nama="Jabatan Contoh " + code,
                    kode_induk=parent, tingkat=level, id_sumber="SUM-K",
                    status_verifikasi=status
                ))
            c.execute(insert(taksonomi_kbji).values(
                edisi="E-KBJI", kode="13", nama="Hanya kandidat",
                kode_induk="1", tingkat=2, id_sumber="SUM-D",
                status_verifikasi="ditinjau"
            ))
            for code, kind, parent, status in (
                ("01", "provinsi", None, "terverifikasi"),
                ("0101", "kota", "01", "terverifikasi"),
                ("0199", "kabupaten", "01", "ditinjau"),
                ("02", "provinsi", None, "ditinjau"),
                ("0201", "kota", "02", "terverifikasi"),
            ):
                c.execute(insert(wilayah).values(
                    sistem_kode="UJI", edisi="E-WIL", kode_wilayah=code,
                    nama_wilayah="Wilayah Contoh " + code,
                    jenis_wilayah=kind, kode_induk=parent, id_sumber="SUM-W",
                    status_verifikasi=status
                ))
            for row in (
                ("U-1", "01", "UMP", 100000, "berlaku", "terverifikasi"),
                ("U-2", "0101", "UMK", 125000, "berlaku", "terverifikasi"),
                ("U-3", "01", "UMP", 99999, "diganti", "terverifikasi"),
                ("U-4", "0101", "UMK", 130000, "diganti", "ditinjau"),
                ("U-5", "0199", "UMK", 140000, "berlaku", "terverifikasi"),
                ("U-6", "0201", "UMK", 141000, "berlaku", "terverifikasi"),
            ):
                uid, kode, jenis, nilai, status, verifikasi = row
                c.execute(insert(keputusan).values(
                    id_keputusan=uid, sistem_kode="UJI", edisi_wilayah="E-WIL",
                    kode_wilayah=kode, tahun=2025, jenis_upah=jenis,
                    nilai_rupiah=nilai, tanggal_mulai=date(2025, 1, 1),
                    nomor_keputusan=uid, tanggal_keputusan=date(2024, 12, 1),
                    status_keputusan=status, id_sumber="SUM-U",
                    status_verifikasi=verifikasi,
                ))
        engine.dispose()
        self.client = TestClient(build_app(self.url))
        self.client.__enter__()
        self.addCleanup(lambda: self.client.__exit__(None, None, None))

    def payload(self, url, config=None, params=None):
        # patch.dict with clear=True makes tests independent of runner env.
        with patch.dict(os.environ, config or {}, clear=True):
            return self.client.get(url, params=params)

    def test_default_tertutup_walaupun_data_berstatus_terverifikasi(self):
        for path in (URL_K, URL_W, URL_U):
            r = self.payload(path)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["data"], [])
            self.assertEqual(r.json()["pagination"]["total"], 0)
            self.assertFalse(r.json()["data_tersedia"])

    def test_aktif_tanpa_allowlist_tertutup(self):
        self.assertEqual(
            self.payload(URL_K, {"RPI_PUBLIKASI_HISTORIS": "aktif"}).json()["data"], []
        )

    def test_kbji_hanya_status_sumber_dan_induk_terverifikasi(self):
        r = self.payload(URL_K, SETUJU).json()
        self.assertEqual([x["kode"] for x in r["data"]], ["1", "11"])
        self.assertEqual(r["pagination"]["total"], 2)
        self.assertTrue(all(x["id_sumber"] == "SUM-K" for x in r["data"]))
        self.assertNotIn("peninjau", r["data"][0])

    def test_wilayah_menyembunyikan_draf_dan_induk_draf(self):
        r = self.payload(URL_W, SETUJU).json()
        self.assertEqual([x["kode_wilayah"] for x in r["data"]], ["01", "0101"])

    def test_ump_umk_hanya_berlaku_dan_wilayah_terverifikasi(self):
        r = self.payload(URL_U, SETUJU).json()
        self.assertEqual([x["id_keputusan"] for x in r["data"]], ["U-1", "U-2"])
        self.assertEqual([x["nilai_rupiah"] for x in r["data"]], [100000, 125000])
        self.assertTrue(all(x["tahun"] == 2025 for x in r["data"]))
        self.assertNotIn("peninjau", r["data"][0])

    def test_sumber_upah_tidak_disetujui_tidak_boleh_terlihat(self):
        cfg = dict(SETUJU, RPI_SUMBER_DISETUJUI_PUBLIK="SUM-K,SUM-W")
        self.assertEqual(self.payload(URL_U, cfg).json()["data"], [])

    def test_sumber_wilayah_tidak_disetujui_tidak_boleh_terlihat(self):
        cfg = dict(SETUJU, RPI_SUMBER_DISETUJUI_PUBLIK="SUM-K,SUM-U")
        self.assertEqual(self.payload(URL_W, cfg).json()["data"], [])
        self.assertEqual(self.payload(URL_U, cfg).json()["data"], [])

    def test_sumber_tidak_berizin_ditolak(self):
        e = create_engine(self.url)
        with e.begin() as c:
            c.execute(update(sumber).where(sumber.c.id_sumber == "SUM-U").values(
                izin_distribusi="belum_diperiksa",
            ))
        e.dispose()
        self.assertEqual(self.payload(URL_U, SETUJU).json()["data"], [])

    def test_sumber_belum_verifikasi_ditolak(self):
        e = create_engine(self.url)
        with e.begin() as c:
            c.execute(update(sumber).where(sumber.c.id_sumber == "SUM-K").values(
                status_verifikasi="ditinjau",
            ))
        e.dispose()
        self.assertEqual(self.payload(URL_K, SETUJU).json()["data"], [])

    def test_dua_keputusan_berlaku_dalam_kelompok_sama_ditolak(self):
        e = create_engine(self.url)
        with e.begin() as c:
            c.execute(insert(keputusan).values(
                id_keputusan="U-DUP", sistem_kode="UJI", edisi_wilayah="E-WIL",
                kode_wilayah="01", tahun=2025, jenis_upah="UMP",
                nilai_rupiah=105000, tanggal_mulai=date(2025, 1, 1),
                tanggal_keputusan=date(2024, 12, 2), nomor_keputusan="U-DUP",
                status_keputusan="berlaku", id_sumber="SUM-U",
                status_verifikasi="ditinjau",
            ))
        e.dispose()
        r = self.payload(URL_U, SETUJU).json()
        self.assertEqual([x["id_keputusan"] for x in r["data"]], ["U-2"])

    def test_filter_dan_paginasi(self):
        kbji = self.payload(URL_K, SETUJU, {"edisi": "E-KBJI", "kode": "11"}).json()
        self.assertEqual([x["kode"] for x in kbji["data"]], ["11"])
        wilayah_ = self.payload(URL_W, SETUJU, {"jenis_wilayah": "kota"}).json()
        self.assertEqual([x["kode_wilayah"] for x in wilayah_["data"]], ["0101"])
        upah = self.payload(URL_U, SETUJU, {"tahun": 2025, "jenis_upah": "UMK"}).json()
        self.assertEqual([x["id_keputusan"] for x in upah["data"]], ["U-2"])
        page = self.payload(URL_K, SETUJU, {"batas": 1, "mulai": 1}).json()
        self.assertEqual([x["kode"] for x in page["data"]], ["11"])
        self.assertFalse(page["pagination"]["has_more"])

    def test_validasi_parameter_http(self):
        self.assertEqual(self.payload(URL_K, SETUJU, {"batas": 0}).status_code, 422)
        self.assertEqual(self.payload(URL_W, SETUJU, {"jenis_wilayah": "negara"}).status_code, 422)
        self.assertEqual(self.payload(URL_U, SETUJU, {"jenis_upah": "rata_rata"}).status_code, 422)
        self.assertEqual(self.payload(URL_U, SETUJU, {"tahun": 100}).status_code, 422)

    def test_kandidat_sumber_tidak_dapat_diaktifkan(self):
        config = dict(SETUJU, RPI_SUMBER_DISETUJUI_PUBLIK="KANDIDAT-KBJI-123")
        self.assertEqual(self.payload(URL_K, config).json()["data"], [])

    def test_aktif_tetapi_skema_belum_dipasang_503(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "kosong.sqlite3"
            e = create_engine("sqlite+pysqlite:///" + str(p))
            with e.begin() as c:
                c.exec_driver_sql("CREATE TABLE dummy(id INTEGER)")
            e.dispose()
            with TestClient(build_app("sqlite+pysqlite:///" + str(p))) as client:
                with patch.dict(os.environ, SETUJU, clear=True):
                    r = client.get(URL_K)
                    self.assertEqual(r.status_code, 503)

    def test_kompatibilitas_openapi_tidak_terputus(self):
        r = self.payload("/openapi.json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("/v1/occupations", r.json()["paths"])
        self.assertIn(URL_K, r.json()["paths"])
        self.assertIn(URL_W, r.json()["paths"])
        self.assertIn(URL_U, r.json()["paths"])


if __name__ == "__main__":
    unittest.main()
