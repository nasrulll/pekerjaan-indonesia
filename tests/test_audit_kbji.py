"""Seluruh kode dan nama dalam pengujian adalah sintetis, bukan KBJI resmi."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from scripts.audit_kbji import audit_taksonomi, kandidat_cocok, jalankan


class TestAuditKBJI(unittest.TestCase):
    def setUp(self):
        self.rows = [
            dict(edisi="Edisi uji", kode="0", nama="Kelompok uji", kode_induk="", tingkat="1"),
            dict(edisi="Edisi uji", kode="01", nama="Peran Uji", kode_induk="0", tingkat="2"),
        ]

    def test_valid_hierarchy(self):
        result = audit_taksonomi(self.rows, "Edisi uji")
        self.assertEqual(result["galat"], [])
        self.assertEqual(result["jumlah_kode_unik"], 2)
        self.assertEqual(self.rows[1]["kode"], "01")

    def test_duplicate(self):
        self.assertIn("duplikat", str(audit_taksonomi(self.rows + [self.rows[1]], "Edisi uji")["galat"]))

    def test_missing_parent(self):
        self.rows[1]["kode_induk"] = "99"
        self.assertIn("tidak ditemukan", str(audit_taksonomi(self.rows, "Edisi uji")["galat"]))

    def test_invalid_level(self):
        self.rows[1]["tingkat"] = "4"
        self.assertIn("tingkat", str(audit_taksonomi(self.rows, "Edisi uji")["galat"]))

    def test_cycle(self):
        self.rows[0]["kode_induk"] = "01"
        self.assertIn("siklus", str(audit_taksonomi(self.rows, "Edisi uji")["galat"]))

    def test_edition_mismatch(self):
        self.rows[1]["edisi"] = "lain"
        self.assertIn("edisi", str(audit_taksonomi(self.rows, "Edisi uji")["galat"]))

    def test_candidate_never_official(self):
        occ = [dict(occupation_id="ID-OCC-000001", preferred_name_id=" PERAN  UJI ")]
        suggestions = kandidat_cocok(occ, self.rows)
        self.assertEqual(suggestions[0]["status"], "kandidat_belum_diverifikasi")

    def test_manifest_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = dict(
                jenis_sumber="klasifikasi_kbji", penerbit="Penguji", judul="Data sintetis",
                edisi="Edisi uji", url_resmi="https://example.org/uji", tanggal_terbit=None,
                tanggal_diperiksa=None, izin_distribusi="belum_diperiksa", rujukan_izin=None,
                sha256_berkas_sumber=None, status="menunggu_verifikasi")
            (root / "sumber.json").write_text(json.dumps(manifest))
            with (root / "kbji.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=self.rows[0])
                writer.writeheader()
                writer.writerows(self.rows)
            report, _ = jalankan(root / "kbji.csv", root / "sumber.json")
            self.assertEqual(report["galat"], [])
            self.assertEqual(report["status_keluaran"], "audit_internal_belum_resmi")
            manifest.update(
                status="terverifikasi", izin_distribusi="diizinkan", rujukan_izin="Simulasi",
                tanggal_diperiksa="2026-10-15", sha256_berkas_sumber="a" * 64, peninjau="Penguji")
            (root / "sumber.json").write_text(json.dumps(manifest))
            report, _ = jalankan(root / "kbji.csv", root / "sumber.json")
            self.assertTrue(report["galat"])


if __name__ == "__main__":
    unittest.main()
