"""Seluruh input wilayah sintetis; tidak ada data pemerintah."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, select
from nor_id.skema_histori import metadata_histori, wilayah
from nor_id.impor_wilayah_ditinjau import siapkan_paket, terapkan_paket


class UjiImporWilayah(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.root = Path(self.d.name)
        self.db = self.root / "uji.sqlite3"
        e = create_engine("sqlite+pysqlite:///" + str(self.db))
        metadata_histori.create_all(e)
        e.dispose()
        self.url = "sqlite+pysqlite:///" + str(self.db)
        self.asli = self.root / "dokumen.txt"
        self.asli.write_text("SINTETIS BUKAN DATA RESMI")
        self.sha = hashlib.sha256(self.asli.read_bytes()).hexdigest()
        self.csv = self.root / "wilayah.csv"
        self.rows = [
            dict(sistem_kode="UJI", edisi="ED-1", kode_wilayah="01",
                 nama_wilayah="Provinsi Uji", jenis_wilayah="provinsi", kode_induk=""),
            dict(sistem_kode="UJI", edisi="ED-1", kode_wilayah="0101",
                 nama_wilayah="Kota Uji", jenis_wilayah="kota", kode_induk="01"),
        ]
        self.tulis_csv()
        self.manifest = self.root / "manifest.json"
        self.m = dict(
            jenis_sumber="kode_wilayah", penerbit="Penerbit Contoh", judul="Sumber uji",
            edisi="ED-1", url_resmi="https://example.org/uji",
            tanggal_terbit=None, tanggal_diperiksa=None, izin_distribusi="diizinkan",
            rujukan_izin="https://example.org/izin", sha256_berkas_sumber=self.sha,
            status="menunggu_verifikasi",
        )
        self.tulis_m()
        self.approval = self.root / "persetujuan.json"
        self.ap = dict(
            sha256_csv_diolah=hashlib.sha256(self.csv.read_bytes()).hexdigest(),
            sha256_berkas_sumber=self.sha, edisi="ED-1", sistem_kode="UJI",
            peninjau="Penguji Sintetis", tanggal_persetujuan="2026-10-15",
            status="disetujui_untuk_impor_ditinjau",
        )
        self.tulis_ap()

    def tulis_csv(self):
        with self.csv.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(self.rows[0]))
            w.writeheader()
            w.writerows(self.rows)

    def tulis_m(self):
        self.manifest.write_text(json.dumps(self.m))

    def tulis_ap(self):
        self.approval.write_text(json.dumps(self.ap))

    def ready(self):
        return siapkan_paket(self.csv, self.manifest, self.asli, self.approval)

    def test_impor_idempoten_ditinjau(self):
        args = self.ready()
        self.assertEqual(terapkan_paket(self.url, *args)["baris_baru"], 2)
        self.assertEqual(terapkan_paket(self.url, *args)["baris_baru"], 0)
        e = create_engine(self.url)
        with e.connect() as c:
            result = c.execute(select(wilayah)).mappings().all()
            self.assertEqual(len(result), 2)
            self.assertTrue(all(x["status_verifikasi"] == "ditinjau" for x in result))
        e.dispose()

    def test_asli_berubah_ditolak(self):
        self.asli.write_text("BERUBAH")
        with self.assertRaisesRegex(ValueError, "Checksum"):
            self.ready()

    def test_induk_salah_ditolak(self):
        self.rows[1]["kode_induk"] = "99"
        self.tulis_csv()
        with self.assertRaisesRegex(ValueError, "Audit wilayah"):
            self.ready()

    def test_edisi_tidak_cocok_ditolak(self):
        self.rows[1]["edisi"] = "ED-2"
        self.tulis_csv()
        with self.assertRaisesRegex(ValueError, "Edisi"):
            self.ready()

    def test_persetujuan_csv_tidak_cocok(self):
        self.ap["sha256_csv_diolah"] = "0" * 64
        self.tulis_ap()
        with self.assertRaisesRegex(ValueError, "persetujuan"):
            self.ready()

    def test_tanpa_izin_ditolak(self):
        self.m["izin_distribusi"] = "belum_diperiksa"
        self.tulis_m()
        with self.assertRaisesRegex(ValueError, "redistribusi"):
            self.ready()

    def test_perubahan_ditolak_dan_rollback(self):
        args = self.ready()
        terapkan_paket(self.url, *args)
        args[0][1]["nama_wilayah"] = "NAMA BEDA"
        with self.assertRaisesRegex(ValueError, "berbeda"):
            terapkan_paket(self.url, *args)
        e = create_engine(self.url)
        with e.connect() as c:
            self.assertEqual(
                c.execute(select(wilayah.c.nama_wilayah).where(wilayah.c.kode_wilayah == "0101")).scalar_one(),
                "Kota Uji",
            )
        e.dispose()

    def test_database_tanpa_migrasi_ditolak(self):
        args = self.ready()
        kosong = self.root / "kosong.sqlite3"
        kosong.touch()
        with self.assertRaisesRegex(RuntimeError, "migrasi"):
            terapkan_paket("sqlite+pysqlite:///" + str(kosong), *args)


if __name__ == "__main__":
    unittest.main()
