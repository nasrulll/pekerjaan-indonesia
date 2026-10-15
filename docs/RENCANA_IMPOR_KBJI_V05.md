# Rencana impor klasifikasi pekerjaan dan verifikasi sumber — v0.5.0

Status: **belum ada data KBJI resmi yang diimpor**. Dokumen ini mendefinisikan gerbang verifikasi; bukan bukti validitas suatu edisi.

## Pekerjaan prioritas (issue #1)

1. Identifikasi publikasi KBJI BPS yang berlaku beserta **edisi**, URL resmi, penerbit, tanggal terbit, cakupan, dan berkas sumber.
2. Pastikan lisensi atau izin redistribusi terpisah dari ketersediaan untuk diunduh. Simpan catatan persetujuan.
3. Catat hash SHA-256 sumber asli dan waktu unduh; arsipkan metadata provenans. Jangan unggah konten yang tidak boleh didistribusikan.
4. Uji konsistensi hierarki kode dan judul pekerjaan, keunikan pasangan `(edisi, kode)`, karakter Unicode, serta duplikasi sinonim.
5. Bandingkan setiap judul dari 811 pekerjaan kurasi dengan data KBJI melalui kandidat pemetaan; **kandidat bukan pemetaan resmi**.
6. Wajib tinjauan manusia sebelum mengubah `status_verifikasi` menjadi `terverifikasi`; simpan nama peninjau, keputusan dan jejak perubahan.
7. Jalankan pengujian kontrak API lama dan baru, migrasi database, serta pembuatan snapshot/checksum sebelum merge.

## Manifest sumber (contoh struktur; nilai contoh tidak boleh diterbitkan sebagai data resmi)

```json
{
  "jenis_sumber": "klasifikasi_kbji",
  "penerbit": "",
  "judul": "",
  "edisi": "",
  "url_resmi": "",
  "tanggal_terbit": null,
  "tanggal_diperiksa": null,
  "izin_distribusi": "belum_diperiksa",
  "rujukan_izin": null,
  "sha256_berkas_sumber": null,
  "status": "menunggu_verifikasi"
}
```

## Kebijakan publikasi

- Tidak menebak kode KBJI dari kesamaan nama atau AI.
- Simpan edisi kode dan periode berlaku; jangan menimpa kode historis.
- Bedakan *judul pekerjaan draf*, *jabatan organisasi*, *klasifikasi resmi*, dan *alias*.
- Data yang tidak ditemukan tetap kosong, tidak diisi kode palsu.
- Merge hanya setelah data bersumber resmi, berizin, diuji dan disetujui peninjau.

## Kelanjutan

Issue #2 mengatur edisi kode wilayah; issue #3 mengatur sumber keputusan upah minimum. Data upah tidak boleh disamakan dengan rata-rata penghasilan.

## Bukti CI tersedia

- PostgreSQL dan MariaDB: https://github.com/nasrulll/pekerjaan-indonesia/actions/runs/38728621066
- Validasi katalog dan API: https://github.com/nasrulll/pekerjaan-indonesia/actions/runs/38728620628
