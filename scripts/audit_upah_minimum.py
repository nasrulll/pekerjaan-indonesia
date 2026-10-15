"""Audit calon data UMP/UMK dan revisi keputusan; tidak menulis database.

Alat ini tidak mengesahkan asal data atau menampilkan nominal sebagai fakta resmi.
Data aktual hanya boleh diterbitkan setelah dokumen keputusan dan izin ditinjau.
"""
import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

try:
    from scripts.audit_wilayah import audit_wilayah
except ModuleNotFoundError:
    from audit_wilayah import audit_wilayah

KOLOM = {
    "sistem_kode", "edisi_wilayah", "kode_wilayah", "tahun", "jenis_upah",
    "nilai_rupiah", "tanggal_mulai", "penerbit", "nomor_keputusan",
    "tanggal_keputusan", "url_dokumen", "status_keputusan",
    "nomor_keputusan_digantikan",
}
STATUS = {"berlaku", "diganti", "dicabut"}
UPAH = {"UMP": "provinsi", "UMK": ("kabupaten", "kota")}


def tanggal_sah(s):
    try:
        return date.fromisoformat(s).isoformat() == s
    except (ValueError, TypeError):
        return False


def url_sah(s):
    try:
        if not isinstance(s, str) or any(c.isspace() for c in s):
            return False
        parsed = urlsplit(s)
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def audit_upah(rows, wilayah):
    galat = list(audit_wilayah(wilayah)["galat"])
    wilayah_indeks = {
        (r["sistem_kode"], r["edisi"], r["kode_wilayah"]): r
        for r in wilayah
    }
    dilihat = set()
    aktif = set()
    status = Counter()
    for nomor, r in enumerate(rows, 2):
        key_w = (r.get("sistem_kode"), r.get("edisi_wilayah"), r.get("kode_wilayah"))
        jenis = r.get("jenis_upah")
        keputusan = (r.get("nomor_keputusan") or "").strip()
        kunci = key_w + (r.get("tahun"), jenis, keputusan)
        if kunci in dilihat:
            galat.append(f"baris {nomor}: keputusan wilayah/tahun/jenis ganda")
        dilihat.add(kunci)
        w = wilayah_indeks.get(key_w)
        if w is None:
            galat.append(f"baris {nomor}: wilayah/sistem/edisi tidak ditemukan")
        elif jenis == "UMP" and w["jenis_wilayah"] != "provinsi":
            galat.append(f"baris {nomor}: UMP hanya berlaku di provinsi")
        elif jenis == "UMK" and w["jenis_wilayah"] not in ("kabupaten", "kota"):
            galat.append(f"baris {nomor}: UMK hanya berlaku di kabupaten/kota")
        if jenis not in UPAH:
            galat.append(f"baris {nomor}: jenis upah harus UMP atau UMK")
        try:
            tahun = int(r.get("tahun", ""))
            if not 1900 <= tahun <= 2200:
                raise ValueError
        except (ValueError, TypeError):
            galat.append(f"baris {nomor}: tahun tidak sah")
        nominal = r.get("nilai_rupiah") or ""
        if not re.fullmatch(r"[1-9][0-9]*", nominal):
            galat.append(f"baris {nomor}: nominal harus rupiah positif tanpa tanda desimal")
        if not tanggal_sah(r.get("tanggal_mulai")) or not tanggal_sah(r.get("tanggal_keputusan")):
            galat.append(f"baris {nomor}: tanggal kalender tidak sah")
        if not keputusan or not (r.get("penerbit") or "").strip() or not url_sah(r.get("url_dokumen")):
            galat.append(f"baris {nomor}: penerbit, nomor dan URL HTTPS keputusan wajib")
        st = r.get("status_keputusan")
        if st not in STATUS:
            galat.append(f"baris {nomor}: status keputusan tidak dikenal")
        status[st] += 1
        if st == "berlaku":
            key_active = key_w + (r.get("tahun"), jenis)
            if key_active in aktif:
                galat.append(f"baris {nomor}: terdapat dua keputusan berstatus berlaku pada wilayah/tahun/jenis")
            aktif.add(key_active)
    if not rows:
        galat.append("Dataset kandidat upah kosong; tidak ada keputusan yang dapat diaudit")
    return {
        "jumlah_baris": len(rows),
        "menurut_jenis": dict(Counter(r.get("jenis_upah") for r in rows)),
        "menurut_status_keputusan": dict(status),
        "galat": sorted(set(galat)),
        "status_data": "audit_internal_belum_dinilai_resmi",
    }


def baca(path, required):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        if len(header) != len(set(header)) or not required.issubset(header):
            raise ValueError("Kolom wajib tidak tersedia: " + ", ".join(sorted(required)))
        return list(reader)


def main():
    parser = argparse.ArgumentParser(description="Audit calon upah minimum berbasis keputusan resmi")
    parser.add_argument("--csv-upah", type=Path, required=True)
    parser.add_argument("--csv-wilayah", type=Path, required=True)
    parser.add_argument("--laporan", type=Path)
    args = parser.parse_args()
    try:
        records = baca(args.csv_upah, KOLOM)
        wilayah = baca(args.csv_wilayah, {
            "sistem_kode", "edisi", "kode_wilayah", "nama_wilayah", "jenis_wilayah", "kode_induk"})
        report = audit_upah(records, wilayah)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        parser.error(f"Gagal membaca data: {exc}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.laporan:
        args.laporan.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return int(bool(report["galat"]))


if __name__ == "__main__":
    raise SystemExit(main())
