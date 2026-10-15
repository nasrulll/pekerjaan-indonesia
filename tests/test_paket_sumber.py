"""Semua berkas dalam tes sintetis dan bukan publikasi pemerintah."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.periksa_paket_sumber import periksa_paket


class TestPemeriksaanPaket(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.raw = self.root / "uji-sumber.txt"
        self.raw.write_bytes(b"DATA SINTETIS; BUKAN PUBLIKASI RESMI")
        self.csv = self.root / "uji.csv"
        self.csv.write_text("edisi,kode,nama\nE-UJI,01,Contoh\n", encoding="utf-8")
        self.manifest = {
            "jenis_sumber": "klasifikasi_kbji",
            "penerbit": "Penerbit Simulasi",
            "judul": "Contoh Tidak Resmi",
            "edisi": "E-UJI",
            "url_resmi": "https://example.org/sintetis",
            "tanggal_terbit": "2026-01-01",
            "tanggal_diperiksa": "2026-10-15",
            "izin_distribusi": "diizinkan",
            "rujukan_izin": "Hanya uji internal",
            "sha256_berkas_sumber": hashlib.sha256(self.raw.read_bytes()).hexdigest(),
            "status": "terverifikasi",
            "peninjau": "Peninjau uji",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_checksum_dan_review_valid(self):
        result = periksa_paket(self.manifest, self.raw, self.csv)
        self.assertEqual(result["status"], "lulus_pemeriksaan_teknis")
        self.assertEqual(result["jumlah_baris_csv"], 1)
        self.assertIn("BUKAN", result["keterangan"])

    def test_berkas_primer_diubah_ditolak(self):
        self.raw.write_bytes(b"rusak")
        self.assertIn("Checksum", str(periksa_paket(self.manifest, self.raw)["galat"]))

    def test_review_hilang_ditolak(self):
        self.manifest["peninjau"] = ""
        self.assertEqual(periksa_paket(self.manifest, self.raw)["status"], "ditolak")

    def test_izin_belum_diperiksa_ditolak(self):
        self.manifest["izin_distribusi"] = "belum_diperiksa"
        self.assertEqual(periksa_paket(self.manifest, self.raw)["status"], "ditolak")

    def test_manifest_masih_draf_ditolak(self):
        self.manifest["status"] = "menunggu_verifikasi"
        self.assertEqual(periksa_paket(self.manifest, self.raw)["status"], "ditolak")

    def test_csv_header_duplikat_ditolak(self):
        self.csv.write_text("kode,kode\n01,01\n", encoding="utf-8")
        self.assertEqual(periksa_paket(self.manifest, self.raw, self.csv)["status"], "ditolak")


if __name__ == "__main__":
    unittest.main()
