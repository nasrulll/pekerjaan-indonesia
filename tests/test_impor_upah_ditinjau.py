"""Seluruh nilai UMP/UMK adalah SINTETIS dan bukan data resmi."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, insert, select
from nor_id.skema_histori import metadata_histori, sumber, wilayah, keputusan
from nor_id.impor_upah_ditinjau import siapkan_paket, terapkan_paket


class UjiImporUpah(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.db = self.base / "uji.sqlite3"
        self.url = "sqlite+pysqlite:///" + str(self.db)
        e = create_engine(self.url)
        metadata_histori.create_all(e)
        with e.begin() as c:
            c.execute(insert(sumber).values(
                id_sumber="WIL-UJI", jenis_sumber="kode_wilayah", penerbit="Penerbit Uji",
                judul="Wilayah Sintetis", edisi="ED-UJI", url_resmi="https://example.org/wilayah",
                sha256_berkas_asli="a" * 64, izin_distribusi="diizinkan", status_verifikasi="ditinjau"))
            c.execute(insert(wilayah).values(
                sistem_kode="UJI", edisi="ED-UJI", kode_wilayah="01",
                nama_wilayah="Provinsi Sintetis", jenis_wilayah="provinsi",
                id_sumber="WIL-UJI", status_verifikasi="ditinjau"))
            c.execute(insert(wilayah).values(
                sistem_kode="UJI", edisi="ED-UJI", kode_wilayah="0101",
                nama_wilayah="Kabupaten Sintetis", jenis_wilayah="kabupaten",
                kode_induk="01", id_sumber="WIL-UJI", status_verifikasi="ditinjau"))
        e.dispose()
        self.regions = [
            dict(sistem_kode="UJI", edisi="ED-UJI", kode_wilayah="01",
                 nama_wilayah="Provinsi Sintetis", jenis_wilayah="provinsi", kode_induk=""),
            dict(sistem_kode="UJI", edisi="ED-UJI", kode_wilayah="0101",
                 nama_wilayah="Kabupaten Sintetis", jenis_wilayah="kabupaten", kode_induk="01"),
        ]
        self.region_file = self.base / "region.csv"
        self.csv_write(self.region_file, self.regions)
        base = dict(sistem_kode="UJI", edisi_wilayah="ED-UJI",
                    kode_wilayah="01", tahun="2026", jenis_upah="UMP",
                    nilai_rupiah="100000", tanggal_mulai="2026-01-01",
                    penerbit="Instansi Uji", tanggal_keputusan="2025-12-01",
                    url_dokumen="https://example.org/keputusan")
        self.rows = [
            dict(base, nomor_keputusan="KEP-UJI-1", status_keputusan="diganti",
                 nomor_keputusan_digantikan=""),
            dict(base, nomor_keputusan="KEP-UJI-2", nilai_rupiah="110000",
                 status_keputusan="berlaku", nomor_keputusan_digantikan="KEP-UJI-1"),
        ]
        self.csv = self.base / "upah.csv"
        self.csv_write(self.csv, self.rows)
        self.original = self.base / "asli.txt"
        self.original.write_text("KEPUTUSAN SINTETIS BUKAN RESMI")
        self.sha = hashlib.sha256(self.original.read_bytes()).hexdigest()
        self.manifest = self.base / "manifest.json"
        self.m = dict(
            jenis_sumber="upah_minimum", penerbit="Penerbit Uji", judul="Keputusan Sintetis",
            edisi="2026", url_resmi="https://example.org/dokumen",
            tanggal_terbit=None, tanggal_diperiksa=None, izin_distribusi="diizinkan",
            rujukan_izin="https://example.org/izin", sha256_berkas_sumber=self.sha,
            status="menunggu_verifikasi")
        self.write_m()
        self.approval = self.base / "review.json"
        self.ap = dict(
            sha256_csv_diolah=hashlib.sha256(self.csv.read_bytes()).hexdigest(),
            sha256_csv_wilayah=hashlib.sha256(self.region_file.read_bytes()).hexdigest(),
            sha256_berkas_sumber=self.sha, sistem_kode="UJI", edisi_wilayah="ED-UJI",
            tahun="2026", status="disetujui_untuk_impor_ditinjau", peninjau="Peninjau Uji",
            tanggal_persetujuan="2026-10-15")
        self.write_ap()

    @staticmethod
    def csv_write(path, rows):
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def write_m(self):
        self.manifest.write_text(json.dumps(self.m))

    def write_ap(self):
        self.approval.write_text(json.dumps(self.ap))

    def ready(self):
        return siapkan_paket(self.csv, self.region_file, self.manifest,
                              self.original, self.approval)

    def test_dua_keputusan_historis_idempoten(self):
        args = self.ready()
        self.assertEqual(terapkan_paket(self.url, *args)["baris_baru"], 2)
        self.assertEqual(terapkan_paket(self.url, *args)["baris_baru"], 0)
        e = create_engine(self.url)
        with e.connect() as c:
            records = c.execute(select(keputusan)).mappings().all()
            self.assertEqual(len(records), 2)
            self.assertTrue(all(x["status_verifikasi"] == "ditinjau" for x in records))
            later = next(r for r in records if r["status_keputusan"] == "berlaku")
            self.assertIn(later["id_keputusan_digantikan"], [r["id_keputusan"] for r in records])
        e.dispose()

    def test_wilayah_db_hilang_ditolak(self):
        args = self.ready()
        e = create_engine(self.url)
        with e.begin() as c:
            c.execute(wilayah.delete().where(wilayah.c.kode_wilayah == "01"))
        e.dispose()
        with self.assertRaises(ValueError):
            terapkan_paket(self.url, *args)

    def test_dua_keputusan_berlaku_antar_paket_ditolak(self):
        args = self.ready()
        terapkan_paket(self.url, *args)
        new = dict(args[0][1], nomor_keputusan="KEP-UJI-3",
                   nomor_keputusan_digantikan="", status_keputusan="berlaku")
        with self.assertRaisesRegex(ValueError, "berlaku berbeda"):
            terapkan_paket(self.url, [new], args[1], args[2], args[3])

    def test_checksum_dokumen_ditolak(self):
        self.original.write_text("DIUBAH")
        with self.assertRaisesRegex(ValueError, "Checksum"):
            self.ready()

    def test_persetujuan_tidak_cocok(self):
        self.ap["sha256_csv_diolah"] = "0" * 64
        self.write_ap()
        with self.assertRaisesRegex(ValueError, "persetujuan"):
            self.ready()

    def test_rantai_keputusan_putus(self):
        self.rows[1]["nomor_keputusan_digantikan"] = "TIDAK-ADA"
        self.csv_write(self.csv, self.rows)
        with self.assertRaisesRegex(ValueError, "Rantai"):
            self.ready()

    def test_ump_pada_kabupaten_ditolak(self):
        for r in self.rows:
            r["kode_wilayah"] = "0101"
        self.csv_write(self.csv, self.rows)
        with self.assertRaisesRegex(ValueError, "Audit UMP/UMK"):
            self.ready()

    def test_izin_tidak_ada_ditolak(self):
        self.m["izin_distribusi"] = "belum_diperiksa"
        self.write_m()
        with self.assertRaisesRegex(ValueError, "redistribusi"):
            self.ready()

    def test_nominal_nol_ditolak(self):
        self.rows[1]["nilai_rupiah"] = "0"
        self.csv_write(self.csv, self.rows)
        with self.assertRaisesRegex(ValueError, "Audit UMP/UMK"):
            self.ready()

    def test_keputusan_tidak_dapat_ditimpa(self):
        args = self.ready()
        terapkan_paket(self.url, *args)
        args[0][1]["nilai_rupiah"] = "200000"
        with self.assertRaisesRegex(ValueError, "isi berbeda"):
            terapkan_paket(self.url, *args)


if __name__ == "__main__":
    unittest.main()
