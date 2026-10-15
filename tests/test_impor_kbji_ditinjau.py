"""Pengujian dengan data sintetis; tidak ada data KBJI resmi."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, event, select

from nor_id.impor_kbji_ditinjau import siapkan_paket, terapkan_paket
from nor_id.skema_histori import metadata_histori, sumber, taksonomi_kbji


class TestImporKBJIDitinjau(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "uji.sqlite3"
        e = create_engine("sqlite+pysqlite:///" + str(self.db))
        @event.listens_for(e, "connect")
        def _fk(dbapi, _):
            dbapi.execute("PRAGMA foreign_keys=ON")
        metadata_histori.create_all(e)
        e.dispose()
        self.url = "sqlite+pysqlite:///" + str(self.db)
        self.asli = self.root / "sumber.txt"
        self.asli.write_text("UJI SINTETIS: bukan klasifikasi resmi", encoding="utf-8")
        self.sha = hashlib.sha256(self.asli.read_bytes()).hexdigest()
        self.csv = self.root / "taksonomi.csv"
        self.rows = [
            dict(edisi="E-UJI", kode="1", nama="Grup Contoh", kode_induk="", tingkat="1"),
            dict(edisi="E-UJI", kode="11", nama="Pekerjaan Contoh", kode_induk="1", tingkat="2"),
        ]
        self._csv()
        self.manifest = self.root / "manifest.json"
        self.metadata = dict(
            jenis_sumber="klasifikasi_kbji", penerbit="Instansi Uji",
            judul="Dokumen Uji", edisi="E-UJI", url_resmi="https://example.org/uji",
            tanggal_terbit="2026-01-01", tanggal_diperiksa="2026-10-15",
            izin_distribusi="diizinkan", rujukan_izin="https://example.org/izin-uji",
            sha256_berkas_sumber=self.sha, status="menunggu_verifikasi",
        )
        self._manifest()
        self.approval = self.root / "persetujuan.json"
        self.review = dict(
            sha256_csv_diolah=hashlib.sha256(self.csv.read_bytes()).hexdigest(),
            sha256_berkas_sumber=self.sha, edisi="E-UJI",
            peninjau="Peninjau Contoh", tanggal_persetujuan="2026-10-15",
            status="disetujui_untuk_impor_ditinjau",
        )
        self._approval()

    def _csv(self):
        with self.csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(self.rows[0]))
            w.writeheader()
            w.writerows(self.rows)

    def _manifest(self):
        self.manifest.write_text(json.dumps(self.metadata), encoding="utf-8")

    def _approval(self):
        self.approval.write_text(json.dumps(self.review), encoding="utf-8")

    def _prepare(self):
        return siapkan_paket(self.csv, self.manifest, self.asli, self.approval)

    def test_impor_dua_kali_tetap_dua_baris_ditinjau(self):
        r, m, b = self._prepare()
        self.assertEqual(terapkan_paket(self.url, r, m, b)["baris_baru"], 2)
        self.assertEqual(terapkan_paket(self.url, r, m, b)["baris_baru"], 0)
        with create_engine(self.url).connect() as c:
            results = c.execute(select(taksonomi_kbji)).mappings().all()
            self.assertEqual(len(results), 2)
            self.assertTrue(all(x["status_verifikasi"] == "ditinjau" for x in results))
            self.assertEqual(c.execute(select(sumber.c.status_verifikasi)).scalar_one(), "ditinjau")

    def test_checksum_asli_berubah_ditolak(self):
        self.asli.write_text("DIUBAH", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self._prepare()

    def test_checksum_csv_harus_disetujui(self):
        self.rows[1]["nama"] = "Berubah"
        self._csv()
        with self.assertRaisesRegex(ValueError, "Persetujuan"):
            self._prepare()

    def test_tanpa_izin_redistribusi_ditolak(self):
        self.metadata["izin_distribusi"] = "belum_diperiksa"
        self._manifest()
        with self.assertRaisesRegex(ValueError, "redistribusi"):
            self._prepare()

    def test_tanpa_peninjau_ditolak(self):
        self.review["peninjau"] = ""
        self._approval()
        with self.assertRaisesRegex(ValueError, "peninjau"):
            self._prepare()

    def test_induk_tak_ada_ditolak(self):
        self.rows[1]["kode_induk"] = "999"
        self._csv()
        self.review["sha256_csv_diolah"] = hashlib.sha256(self.csv.read_bytes()).hexdigest()
        self._approval()
        with self.assertRaisesRegex(ValueError, "Taksonomi"):
            self._prepare()

    def test_perubahan_existing_ditolak_dan_rollback(self):
        r, m, b = self._prepare()
        terapkan_paket(self.url, r, m, b)
        r[0]["nama"] = "DILARANG DITIMPA"
        with self.assertRaisesRegex(ValueError, "isi berbeda"):
            terapkan_paket(self.url, r, m, b)
        with create_engine(self.url).connect() as c:
            self.assertEqual(
                c.execute(select(taksonomi_kbji.c.nama).where(taksonomi_kbji.c.kode == "1")).scalar_one(),
                "Grup Contoh",
            )

    def test_database_belum_dimigrasi_ditolak(self):
        r, m, b = self._prepare()
        belum = self.root / "kosong.sqlite3"
        belum.touch()
        with self.assertRaisesRegex(RuntimeError, "belum dimigrasi"):
            terapkan_paket("sqlite+pysqlite:///" + str(belum), r, m, b)


if __name__ == "__main__":
    unittest.main()
