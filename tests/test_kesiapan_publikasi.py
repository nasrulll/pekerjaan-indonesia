"""Pengujian integritas dengan data SINTETIS; tidak memuat data BPS/UMP resmi."""
import tempfile
import unittest
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, event, insert, update

from nor_id.kesiapan_publikasi import audit_kesiapan
from nor_id.skema_histori import metadata_histori, sumber, wilayah, taksonomi_kbji, keputusan


class TestGerbangIntegritas(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        @event.listens_for(self.engine, "connect")
        def _fk(conn, _):
            conn.execute("PRAGMA foreign_keys=ON")
        metadata_histori.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def add_source(self, id_sumber, jenis, edisi, **overrides):
        src = dict(
            id_sumber=id_sumber, jenis_sumber=jenis, penerbit="Penerbit Sintetis",
            judul="Dokumen Sintetis", edisi=edisi, url_resmi="https://example.org/sintetis",
            sha256_berkas_asli="a" * 64, izin_distribusi="diizinkan",
            rujukan_izin="https://example.org/izin-sintetis", status_verifikasi="terverifikasi",
            peninjau="Peninjau Pengujian", tanggal_verifikasi=date(2026, 10, 15),
        )
        src.update(overrides)
        with self.engine.begin() as c:
            c.execute(insert(sumber).values(src))

    def add_wilayah(self, kode, jenis="provinsi", induk=None, status="terverifikasi"):
        with self.engine.begin() as c:
            c.execute(insert(wilayah).values(
                sistem_kode="UJI", edisi="ED-UJI", kode_wilayah=kode,
                nama_wilayah="Wilayah Sintetis", jenis_wilayah=jenis,
                kode_induk=induk, id_sumber="WIL-UJI", status_verifikasi=status
            ))

    def add_kbji(self, kode, tingkat=1, induk=None, status="terverifikasi"):
        with self.engine.begin() as c:
            c.execute(insert(taksonomi_kbji).values(
                edisi="ED-KBJI-UJI", kode=kode, nama="Pekerjaan Sintetis",
                kode_induk=induk, tingkat=tingkat, id_sumber="KBJI-UJI",
                status_verifikasi=status
            ))

    def add_upah(self, id_keputusan, kode="01", jenis="UMP", tahun=2026,
                 status="berlaku", ganti=None, verifikasi="terverifikasi"):
        with self.engine.begin() as c:
            c.execute(insert(keputusan).values(
                id_keputusan=id_keputusan, sistem_kode="UJI", edisi_wilayah="ED-UJI",
                kode_wilayah=kode, tahun=tahun, jenis_upah=jenis, nilai_rupiah=100000,
                tanggal_mulai=date(2026, 1, 1), nomor_keputusan=id_keputusan,
                tanggal_keputusan=date(2025, 12, 1), status_keputusan=status,
                id_keputusan_digantikan=ganti, id_sumber="UPAH-UJI",
                status_verifikasi=verifikasi
            ))

    def source_set(self):
        self.add_source("KBJI-UJI", "klasifikasi_kbji", "ED-KBJI-UJI")
        self.add_source("WIL-UJI", "kode_wilayah", "ED-UJI")
        self.add_source("UPAH-UJI", "upah_minimum", "2026")

    def test_tabel_kosong_tidak_mengaku_ada_data_resmi(self):
        result = audit_kesiapan(self.engine)
        self.assertFalse(result["temuan"])
        self.assertEqual(result["status_kesiapan"], "menunggu_dataset_resmi")
        self.assertFalse(result["publikasi_diizinkan_otomatis"])

    def test_skema_terpotong_ditolak(self):
        e = create_engine("sqlite+pysqlite:///:memory:")
        try:
            result = audit_kesiapan(e)
            self.assertEqual(result["status_kesiapan"], "skema_belum_siap")
            self.assertTrue(any("TABEL_HILANG" in t for t in result["temuan"]))
        finally:
            e.dispose()

    def test_data_lengkap_tetap_harus_review_manusia(self):
        self.source_set()
        self.add_kbji("1")
        self.add_kbji("11", 2, "1")
        self.add_wilayah("01")
        self.add_wilayah("0101", jenis="kabupaten", induk="01")
        self.add_upah("K-UJI-1")
        result = audit_kesiapan(self.engine)
        self.assertEqual(result["temuan"], [])
        self.assertEqual(result["status_kesiapan"], "lolos_pemeriksaan_teknis_menunggu_otorisasi_manusia")
        self.assertFalse(result["publikasi_diizinkan_otomatis"])
        self.assertEqual(result["jumlah"]["taksonomi_kbji_per_edisi"]["terverifikasi"], 2)

    def test_sumber_tanpa_izin_ditolak(self):
        self.add_source("KBJI-UJI", "klasifikasi_kbji", "ED-KBJI-UJI",
                        izin_distribusi="belum_diperiksa", rujukan_izin=None)
        self.add_kbji("1")
        result = audit_kesiapan(self.engine)
        self.assertTrue(any("SUMBER_IZIN_BELUM_MEMADAI" in t for t in result["temuan"]))

    def test_taksonomi_induk_belum_verifikasi_ditolak(self):
        self.add_source("KBJI-UJI", "klasifikasi_kbji", "ED-KBJI-UJI")
        self.add_kbji("1", status="ditinjau")
        self.add_kbji("11", 2, "1")
        result = audit_kesiapan(self.engine)
        self.assertTrue(any("KBJI_INDUK_TIDAK_TERVERIFIKASI" in t for t in result["temuan"]))

    def test_wilayah_induk_belum_verifikasi_ditolak(self):
        self.add_source("WIL-UJI", "kode_wilayah", "ED-UJI")
        self.add_wilayah("01", status="ditinjau")
        self.add_wilayah("0101", jenis="kabupaten", induk="01")
        result = audit_kesiapan(self.engine)
        self.assertTrue(any("WILAYAH_INDUK_TIDAK_TERVERIFIKASI" in t for t in result["temuan"]))

    def test_upah_ketika_wilayah_belum_verifikasi_ditolak(self):
        self.source_set()
        self.add_wilayah("01", status="ditinjau")
        self.add_upah("K-UJI-1")
        result = audit_kesiapan(self.engine)
        self.assertTrue(any("UPAH_WILAYAH_TIDAK_TERVERIFIKASI" in t for t in result["temuan"]))

    def test_keputusan_aktif_ganda_ditolak(self):
        self.source_set()
        self.add_wilayah("01")
        self.add_upah("K-UJI-1")
        self.add_upah("K-UJI-2")
        result = audit_kesiapan(self.engine)
        self.assertTrue(any("UPAH_KEPUTUSAN_AKTIF_GANDA" in t for t in result["temuan"]))

    def test_revisi_tahun_berbeda_ditolak(self):
        self.source_set()
        self.add_wilayah("01")
        self.add_upah("K-UJI-1", tahun=2025, status="diganti")
        self.add_upah("K-UJI-2", tahun=2026, ganti="K-UJI-1")
        result = audit_kesiapan(self.engine)
        self.assertTrue(any("UPAH_RANTAI_TIDAK_KONSISTEN" in t for t in result["temuan"]))

    def test_jenis_sumber_tidak_cocok_ditolak(self):
        self.add_source("KBJI-UJI", "kode_wilayah", "ED-KBJI-UJI")
        self.add_kbji("1")
        result = audit_kesiapan(self.engine)
        self.assertTrue(any("ENTRI_JENIS_SUMBER_TIDAK_COCOK" in t for t in result["temuan"]))

    def test_entri_berstatus_ditinjau_tidak_terhitung_terverifikasi(self):
        self.add_source("KBJI-UJI", "klasifikasi_kbji", "ED-KBJI-UJI",
                        status_verifikasi="ditinjau")
        self.add_kbji("1", status="ditinjau")
        result = audit_kesiapan(self.engine)
        self.assertEqual(result["status_kesiapan"], "menunggu_dataset_resmi")
        self.assertEqual(result["jumlah"]["taksonomi_kbji_per_edisi"]["ditinjau"], 1)
        self.assertEqual(result["jumlah"]["taksonomi_kbji_per_edisi"]["terverifikasi"], 0)


if __name__ == "__main__":
    unittest.main()
