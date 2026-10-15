"""Audit calon kode wilayah lintas sistem dan edisi; tidak menulis database.

Kolom wajib: sistem_kode, edisi, kode_wilayah, nama_wilayah,
jenis_wilayah, kode_induk. Peninjauan manusia wajib sebelum publikasi.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

KOLOM = {"sistem_kode", "edisi", "kode_wilayah", "nama_wilayah", "jenis_wilayah", "kode_induk"}
JENIS = {"provinsi", "kabupaten", "kota"}


def audit_wilayah(rows):
    galat = []
    indeks = {}
    for nomor, r in enumerate(rows, 2):
        kunci = tuple((r.get(k) or "").strip() for k in ("sistem_kode", "edisi", "kode_wilayah"))
        jenis = (r.get("jenis_wilayah") or "").strip()
        if not all(kunci) or not (r.get("nama_wilayah") or "").strip():
            galat.append(f"baris {nomor}: kode, edisi, nama, sistem kode wajib diisi")
        if jenis not in JENIS:
            galat.append(f"baris {nomor}: jenis_wilayah tidak dikenal")
        if kunci in indeks:
            galat.append(f"baris {nomor}: duplikat sistem, edisi, kode wilayah")
        if kunci not in indeks:
            indeks[kunci] = r
    for (sistem, edisi, kode), r in indeks.items():
        jenis, induk = r.get("jenis_wilayah") or "", (r.get("kode_induk") or "").strip()
        if jenis == "provinsi":
            if induk:
                galat.append(f"{sistem}/{edisi}/{kode}: provinsi tidak boleh mempunyai induk")
        elif jenis in ("kabupaten", "kota"):
            if not induk:
                galat.append(f"{sistem}/{edisi}/{kode}: kabupaten/kota wajib memiliki induk")
            else:
                parent = indeks.get((sistem, edisi, induk))
                if parent is None or parent.get("jenis_wilayah") != "provinsi":
                    galat.append(f"{sistem}/{edisi}/{kode}: induk harus provinsi pada sistem dan edisi yang sama")
        if induk == kode:
            galat.append(f"{sistem}/{edisi}/{kode}: induk diri sendiri")
    return {
        "jumlah_baris": len(rows), "jumlah_kunci_unik": len(indeks),
        "jumlah_jenis": dict(Counter(x.get("jenis_wilayah") for x in rows)),
        "galat": sorted(set(galat)), "status": "audit_internal_bukan_data_resmi",
    }


def main():
    parser = argparse.ArgumentParser(description="Audit calon kode wilayah, tanpa memublikasikan data")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--laporan", type=Path)
    args = parser.parse_args()
    try:
        with args.csv.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            header = reader.fieldnames or []
            if len(header) != len(set(header)) or not KOLOM.issubset(header):
                parser.error("Kolom wajib: " + ", ".join(sorted(KOLOM)))
            hasil = audit_wilayah(list(reader))
    except (OSError, UnicodeError, csv.Error) as exc:
        parser.error(f"Berkas tidak dapat dibaca: {exc}")
    print(json.dumps(hasil, ensure_ascii=False, indent=2))
    if args.laporan:
        args.laporan.write_text(json.dumps(hasil, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return int(bool(hasil["galat"]))


if __name__ == "__main__":
    raise SystemExit(main())
