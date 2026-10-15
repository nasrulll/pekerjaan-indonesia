"""Pemeriksaan checksum dan status peninjauan paket sumber secara lokal.

Tidak mengunduh, memvalidasi keaslian penerbit, menerbitkan sumber,
mengubah database, atau mengesahkan kode pekerjaan/upah.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

try:
    from scripts.validasi_manifest_sumber import validasi_manifest
except ModuleNotFoundError:
    from validasi_manifest_sumber import validasi_manifest


def hash_berkas(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for potong in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(potong)
    return digest.hexdigest()


def periksa_paket(manifest: dict, berkas_primer: Path, berkas_csv: Path | None = None):
    masalah = validasi_manifest(manifest)
    hasil = {
        "status": "ditolak",
        "keterangan": "Pemeriksaan teknis lokal; BUKAN verifikasi keaslian instansi atau izin hukum.",
        "galat": masalah,
    }
    if not isinstance(manifest, dict):
        return hasil
    if manifest.get("status") != "terverifikasi":
        masalah.append("Paket belum mendapat persetujuan peninjau manusia.")
    if manifest.get("izin_distribusi") != "diizinkan":
        masalah.append("Hak redistribusi belum dinyatakan diizinkan.")
    if not manifest.get("peninjau"):
        masalah.append("Identitas peninjau manusia diperlukan.")
    if not masalah:
        aktual = hash_berkas(berkas_primer)
        hasil["hash_primer_aktual"] = aktual
        if aktual.lower() != str(manifest.get("sha256_berkas_sumber", "")).lower():
            masalah.append("Checksum berkas primer tidak cocok dengan manifest.")
    if berkas_csv is not None and not masalah:
        with berkas_csv.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            headers = next(reader, [])
            if not headers or len(headers) != len(set(headers)):
                masalah.append("CSV hasil olahan tidak memiliki header unik dan valid.")
            else:
                hasil["jumlah_baris_csv"] = sum(1 for _ in reader)
        hasil["sha256_csv_olahan"] = hash_berkas(berkas_csv)
    if not masalah:
        hasil["status"] = "lulus_pemeriksaan_teknis"
    return hasil


def main() -> int:
    parser = argparse.ArgumentParser(description="Periksa bukti hash paket sumber RPI")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--berkas-primer", type=Path, required=True)
    parser.add_argument("--csv-olahan", type=Path)
    parser.add_argument("--laporan", type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = periksa_paket(manifest, args.berkas_primer, args.csv_olahan)
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        parser.error(f"Gagal memeriksa paket: {exc}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.laporan:
        args.laporan.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return int(result["status"] != "lulus_pemeriksaan_teknis")


if __name__ == "__main__":
    raise SystemExit(main())
