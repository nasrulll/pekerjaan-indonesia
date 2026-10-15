"""Uji paket audit dengan DATA SINTETIS; bukan referensi pemerintah."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_paket_nasional import audit_paket, audit_rantai_keputusan, baca_tabel


class UjiAuditPaketNasional(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.primer = self.base / 'berkas-uji.txt'
        self.primer.write_text('dokumen sintetis, bukan publikasi resmi', encoding='utf-8')
        self.sha = hashlib.sha256(self.primer.read_bytes()).hexdigest()
        self.kbji = [dict(edisi='UJI-EDISI', kode='1', nama='Contoh Grup', kode_induk='', tingkat='1'),
                     dict(edisi='UJI-EDISI', kode='11', nama='Pekerjaan Contoh', kode_induk='1', tingkat='2')]
        self.wilayah = [dict(sistem_kode='UJI', edisi='UJI-WIL', kode_wilayah='01',
                             nama_wilayah='Provinsi Sintetis', jenis_wilayah='provinsi', kode_induk=''),
                        dict(sistem_kode='UJI', edisi='UJI-WIL', kode_wilayah='0101',
                             nama_wilayah='Kota Sintetis', jenis_wilayah='kota', kode_induk='01')]
        dasar = dict(sistem_kode='UJI', edisi_wilayah='UJI-WIL', kode_wilayah='01', tahun='2026',
                     jenis_upah='UMP', tanggal_mulai='2026-01-01', penerbit='Penerbit Sintetis',
                     tanggal_keputusan='2025-12-01', url_dokumen='https://example.org/uji')
        self.upah = [dict(dasar, nilai_rupiah='100000', nomor_keputusan='UJI-001',
                          nomor_keputusan_digantikan='', status_keputusan='diganti'),
                     dict(dasar, nilai_rupiah='120000', nomor_keputusan='UJI-002',
                          nomor_keputusan_digantikan='UJI-001', status_keputusan='berlaku')]

    def tulis_csv(self, filename, rows):
        path = self.base / filename
        with path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def tulis_manifest(self, filename, jenis, edisi, **extra):
        manifest = dict(jenis_sumber=jenis, penerbit='Instansi sintetis', judul='Sumber uji',
                        edisi=edisi, url_resmi='https://example.org/uji', tanggal_terbit=None,
                        tanggal_diperiksa=None, izin_distribusi='belum_diperiksa',
                        rujukan_izin=None, sha256_berkas_sumber=self.sha,
                        status='menunggu_verifikasi', **extra)
        path = self.base / filename
        path.write_text(json.dumps(manifest), encoding='utf-8')
        return path

    def berkas(self):
        return {
            'kbji': (self.tulis_csv('kbji.csv', self.kbji),
                     self.tulis_manifest('kbji.json', 'klasifikasi_kbji', 'UJI-EDISI'), self.primer),
            'wilayah': (self.tulis_csv('wilayah.csv', self.wilayah),
                        self.tulis_manifest('wilayah.json', 'kode_wilayah', 'UJI-WIL'), self.primer),
            'upah': (self.tulis_csv('upah.csv', self.upah),
                     self.tulis_manifest('upah.json', 'upah_minimum', '2026', edisi_wilayah='UJI-WIL'), self.primer),
        }

    def test_rantai_keputusan_valid(self):
        self.assertEqual(audit_rantai_keputusan(self.upah), [])

    def test_rantai_putus_ditolak(self):
        self.upah[1]['nomor_keputusan_digantikan'] = 'TIDAK-ADA'
        self.assertTrue(audit_rantai_keputusan(self.upah))

    def test_pengganti_ganda_ditolak(self):
        self.upah.append(dict(self.upah[1], nomor_keputusan='UJI-003'))
        self.assertTrue(any('lebih dari satu' in e for e in audit_rantai_keputusan(self.upah)))

    def test_mengganti_diri_sendiri_ditolak(self):
        self.upah[1]['nomor_keputusan_digantikan'] = 'UJI-002'
        self.assertTrue(any('diri sendiri' in e for e in audit_rantai_keputusan(self.upah)))

    def test_pengganti_beda_wilayah_ditolak(self):
        self.upah[1]['kode_wilayah'] = '0101'
        self.assertTrue(any('tidak ada' in e for e in audit_rantai_keputusan(self.upah)))

    def test_csv_kolom_ekstra_ditolak(self):
        f = self.base / 'rusak.csv'
        f.write_text('kode,nama\n1,dua,tiga\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            baca_tabel(f, {'kode','nama'})

    def test_cli_dieksekusi_langsung(self):
        import subprocess
        import sys
        paket = self.berkas()
        result = subprocess.run(
            [sys.executable, "scripts/audit_paket_nasional.py",
             "--kbji", str(paket["kbji"][0]), "--manifest-kbji", str(paket["kbji"][1]),
             "--wilayah", str(paket["wilayah"][0]), "--manifest-wilayah", str(paket["wilayah"][1]),
             "--upah", str(paket["upah"][0]), "--manifest-upah", str(paket["upah"][1])],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(json.loads(result.stdout)["status_publikasi"],
                         "DIBLOKIR_MENUNGGU_PERSETUJUAN_MANUSIA")

    def test_paket_valid_tetap_tidak_diterbitkan(self):
        paket = self.berkas()
        hasil = audit_paket(paket)
        self.assertEqual(hasil['galat'], [])
        self.assertTrue(hasil['layak_diajukan_untuk_tinjauan'])
        self.assertEqual(hasil['status_publikasi'], 'DIBLOKIR_MENUNGGU_PERSETUJUAN_MANUSIA')
        self.assertEqual(hasil['dataset']['upah']['jumlah_baris'], 2)
        self.assertTrue(all(x['bukti_primer_diperiksa'] for x in hasil['dataset'].values()))
        self.assertFalse(any('terverifikasi' in x for x in hasil['dataset']))

    def test_checksum_primer_salah_ditolak(self):
        paket = self.berkas()
        manifest_path = paket['kbji'][1]
        m = json.loads(manifest_path.read_text(encoding='utf-8'))
        m['sha256_berkas_sumber'] = 'b' * 64
        manifest_path.write_text(json.dumps(m), encoding='utf-8')
        hasil = audit_paket(paket)
        self.assertTrue(any('checksum' in e for e in hasil['galat']))

    def test_edisi_wilayah_mismatch_ditolak(self):
        paket = self.berkas()
        self.wilayah[0]['edisi'] = 'UJI-LAIN'
        paket['wilayah'] = (self.tulis_csv('wilayah.csv', self.wilayah), *paket['wilayah'][1:])
        hasil = audit_paket(paket)
        self.assertTrue(any('edisi CSV' in e for e in hasil['galat']))

    def test_upah_tanpa_wilayah_ditolak(self):
        paket = self.berkas()
        hasil = audit_paket({'upah': paket['upah']})
        self.assertTrue(any('memerlukan dataset wilayah' in e for e in hasil['galat']))

    def test_sumber_asli_tidak_diserahkan_hanya_peringatan(self):
        paket = self.berkas()
        a,b,_ = paket['kbji']
        paket['kbji'] = (a,b,None)
        hasil = audit_paket(paket)
        self.assertTrue(any('belum diberikan' in e for e in hasil['peringatan']))
        self.assertFalse(hasil['dataset']['kbji']['bukti_primer_diperiksa'])
        self.assertEqual(hasil['status_publikasi'], 'DIBLOKIR_MENUNGGU_PERSETUJUAN_MANUSIA')


if __name__ == '__main__':
    unittest.main()
