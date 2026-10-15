import unittest
from scripts.validasi_manifest_sumber import validasi_manifest

class TestValidasiManifest(unittest.TestCase):
    def setUp(self):
        self.data = dict(
            jenis_sumber="klasifikasi_kbji", penerbit="Penerbit uji",
            judul="Sumber uji", edisi="Edisi uji", url_resmi="https://example.org/sumber",
            tanggal_terbit=None, tanggal_diperiksa=None,
            izin_distribusi="belum_diperiksa", rujukan_izin=None,
            sha256_berkas_sumber=None, status="menunggu_verifikasi")

    def test_draf_lulus_struktur(self):
        self.assertEqual(validasi_manifest(self.data), [])

    def test_belum_berizin_tidak_boleh_terverifikasi(self):
        self.data["status"] = "terverifikasi"
        self.assertTrue(validasi_manifest(self.data))

    def test_url_non_https_ditolak(self):
        self.data["url_resmi"] = "http://example.org"
        self.assertTrue(any("HTTPS" in x for x in validasi_manifest(self.data)))

    def test_checksum_tidak_valid_ditolak(self):
        self.data["sha256_berkas_sumber"] = "abc"
        self.assertTrue(any("sha256" in x for x in validasi_manifest(self.data)))

if __name__ == "__main__":
    unittest.main()
