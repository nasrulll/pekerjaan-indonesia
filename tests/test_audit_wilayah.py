"""Semua nama dan kode wilayah di sini sintetis, bukan data pemerintah."""
import unittest
from scripts.audit_wilayah import audit_wilayah


class TestAuditWilayah(unittest.TestCase):
    def setUp(self):
        self.rows = [
            dict(sistem_kode="SISTEM-UJI", edisi="E-1", kode_wilayah="01",
                 nama_wilayah="Provinsi Uji", jenis_wilayah="provinsi", kode_induk=""),
            dict(sistem_kode="SISTEM-UJI", edisi="E-1", kode_wilayah="0101",
                 nama_wilayah="Kabupaten Uji", jenis_wilayah="kabupaten", kode_induk="01"),
        ]

    def test_valid(self):
        self.assertEqual(audit_wilayah(self.rows)["galat"], [])

    def test_missing_parent(self):
        self.rows[1]["kode_induk"] = "99"
        self.assertTrue(audit_wilayah(self.rows)["galat"])

    def test_edition_isolation(self):
        self.rows[1]["edisi"] = "E-2"
        self.assertTrue(audit_wilayah(self.rows)["galat"])

    def test_system_isolation(self):
        self.rows[1]["sistem_kode"] = "SISTEM-LAIN"
        self.assertTrue(audit_wilayah(self.rows)["galat"])

    def test_duplicate(self):
        self.assertIn("duplikat", str(audit_wilayah(self.rows + [self.rows[1]])["galat"]))

    def test_province_has_no_parent(self):
        self.rows[0]["kode_induk"] = "000"
        self.assertTrue(audit_wilayah(self.rows)["galat"])

    def test_no_fake_official_status(self):
        self.assertEqual(audit_wilayah(self.rows)["status"], "audit_internal_bukan_data_resmi")


if __name__ == "__main__":
    unittest.main()
