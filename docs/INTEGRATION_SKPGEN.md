# Potensi Integrasi SKPGen AI

Repo ini **mandiri**; tidak disambungkan ke repositori SKPGen pengguna tanpa izin. Contoh desain integrasi:

```text
Pengguna memilih pekerjaan
  → occupation_id (stabil)
  → pilih jabatan instansi dan status kepegawaian
  → tentukan unit kerja & tugas pokok
  → validasi nomenklatur jabatan dan regulasi yang berlaku
  → generate *usulan* RHK + indikator + target + bukti dukung
  → review/koreksi manusia sebelum finalisasi SKP
```

## Kontrak data anjuran

```json
{
  "occupation_id": "ID-OCC-000001",
  "occupation_name": "contoh",
  "organizational_title": "contoh",
  "employment_contexts": ["ASN-PNS"],
  "official_kbji": null,
  "regulation_source": null,
  "requires_human_review": true
}
```

Contoh tersebut adalah *skema* saja, bukan payload pekerjaan nyata. Pastikan SKPGen menggunakan peraturan dan nomenklatur jabatan ASN yang berlaku secara terpisah; kode KBJI **tidak otomatis menentukan** RHK atau indikator ASN. Sebuah profesi dapat memiliki banyak jabatan/jenjang dan satu jabatan dapat bertanggung jawab pada lebih dari satu pekerjaan.

## Rekomendasi integrasi teknis

- Sediakan snapshot JSON bertanda versi; simpan `occupation_id` sebagai foreign reference pada sistem pemakai.
- Hindari mengkopi kode profesi terverifikasi secara tidak terkontrol; gunakan changelog, versi, serta provenance sumber.
- Pisahkan data publik pekerjaan dari data personal ASN (privasi).
- Jangan gunakan data awal `draft` untuk membenarkan persyaratan lisensi, klaim kepatuhan, atau keputusan administratif otomatis.
