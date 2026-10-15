"""Pengujian UMP/UMK menggunakan angka dan wilayah sintetis, bukan upah resmi."""
import unittest
from scripts.audit_upah_minimum import audit_upah


class TestAuditUpahMinimum(unittest.TestCase):
    def setUp(self):
        self.wilayah = [
            dict(sistem_kode="UJI", edisi="E1", kode_wilayah="01",
                 nama_wilayah="Provinsi Sintetis", jenis_wilayah="provinsi", kode_induk=""),
            dict(sistem_kode="UJI", edisi="E1", kode_wilayah="0101",
                 nama_wilayah="Kabupaten Sintetis", jenis_wilayah="kabupaten", kode_induk="01"),
        ]
        self.upah = [
            dict(sistem_kode="UJI", edisi_wilayah="E1", kode_wilayah="01",
                 tahun="2026", jenis_upah="UMP", nilai_rupiah="100000",
                 tanggal_mulai="2026-01-01", penerbit="Lembaga sintetis",
                 nomor_keputusan="SURAT-UJI-1", tanggal_keputusan="2025-12-01",
                 url_dokumen="https://example.org/contoh", status_keputusan="berlaku",
                 nomor_keputusan_digantikan="")
        ]

    def test_valid_simulasi(self):
        self.assertEqual(audit_upah(self.upah, self.wilayah)["galat"], [])

    def test_ump_bukan_untuk_kabupaten(self):
        self.upah[0]["kode_wilayah"] = "0101"
        self.assertIn("UMP", str(audit_upah(self.upah, self.wilayah)["galat"]))

    def test_umk_bukan_untuk_provinsi(self):
        self.upah[0]["jenis_upah"] = "UMK"
        self.assertIn("UMK", str(audit_upah(self.upah, self.wilayah)["galat"]))

    def test_edisi_wilayah_salah(self):
        self.upah[0]["edisi_wilayah"] = "E2"
        self.assertIn("tidak ditemukan", str(audit_upah(self.upah, self.wilayah)["galat"]))

    def test_nominal_bukan_pecahan(self):
        self.upah[0]["nilai_rupiah"] = "100.5"
        self.assertIn("nominal", str(audit_upah(self.upah, self.wilayah)["galat"]))

    def test_tanggal_tidak_ada(self):
        self.upah[0]["tanggal_mulai"] = "2026-02-30"
        self.assertIn("tanggal", str(audit_upah(self.upah, self.wilayah)["galat"]))

    def test_satu_keputusan_berlaku(self):
        lain = dict(self.upah[0], nomor_keputusan="SURAT-UJI-2")
        self.assertIn("dua keputusan", str(audit_upah(self.upah + [lain], self.wilayah)["galat"]))

    def test_historis_diganti_bukan_dua_aktif(self):
        lama = dict(self.upah[0], nomor_keputusan="SURAT-UJI-0", status_keputusan="diganti")
        self.assertEqual(audit_upah([lama] + self.upah, self.wilayah)["galat"], [])

    def test_dataset_kosong_tidak_dianggap_selesai(self):
        self.assertTrue(audit_upah([], self.wilayah)["galat"])


if __name__ == "__main__":
    unittest.main()
