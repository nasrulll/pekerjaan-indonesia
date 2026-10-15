"""Validasi metadata sumber resmi sebelum proses impor RPI v0.5.0.

Tidak mengunduh sumber atau menandai data sebagai terverifikasi.
"""
import argparse
import json
import re
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit

BIDANG_WAJIB = ("jenis_sumber", "penerbit", "judul", "edisi", "url_resmi",
                "tanggal_terbit", "tanggal_diperiksa", "izin_distribusi",
                "rujukan_izin", "sha256_berkas_sumber", "status")

def validasi_manifest(data):
    masalah = []
    if not isinstance(data, dict):
        return ["Manifest harus berupa objek JSON."]
    for bidang in BIDANG_WAJIB:
        if bidang not in data:
            masalah.append(f"Kolom wajib hilang: {bidang}")
    if masalah:
        return masalah
    for bidang in ("jenis_sumber", "penerbit", "judul", "edisi"):
        if not isinstance(data[bidang], str) or not data[bidang].strip():
            masalah.append(f"{bidang} harus diisi.")
    url = data["url_resmi"]
    if not isinstance(url, str) or any(x.isspace() for x in url):
        masalah.append("url_resmi harus URL HTTPS resmi yang dapat diperiksa.")
    else:
        try:
            bagian = urlsplit(url)
            if bagian.scheme != "https" or not bagian.hostname or bagian.username or bagian.password:
                masalah.append("url_resmi harus URL HTTPS resmi yang dapat diperiksa.")
        except ValueError:
            masalah.append("url_resmi harus URL HTTPS resmi yang dapat diperiksa.")
    # URL HTTPS secara sintaksis tidak membuktikan kepemilikan instansi.
    if data["izin_distribusi"] not in ("diizinkan", "dilarang", "belum_diperiksa"):
        masalah.append("Status izin_distribusi tidak dikenal.")
    if data["status"] not in ("menunggu_verifikasi", "ditolak", "terverifikasi"):
        masalah.append("Status verifikasi tidak dikenal.")
    sha = data["sha256_berkas_sumber"]
    if sha is not None and (not isinstance(sha, str) or re.fullmatch(r"[0-9a-fA-F]{64}", sha) is None):
        masalah.append("sha256_berkas_sumber harus berupa 64 karakter hex.")
    for field in ("tanggal_terbit", "tanggal_diperiksa"):
        val = data[field]
        if val is None:
            continue
        try:
            if not isinstance(val, str) or date.fromisoformat(val).isoformat() != val:
                raise ValueError()
        except ValueError:
            masalah.append(f"{field} harus tanggal ISO valid YYYY-MM-DD atau null.")
    if data["status"] == "terverifikasi":
        if data["izin_distribusi"] != "diizinkan":
            masalah.append("Tidak boleh verifikasi jika izin redistribusi belum diizinkan.")
        for field in ("rujukan_izin", "sha256_berkas_sumber", "tanggal_diperiksa"):
            if not data[field]:
                masalah.append(f"{field} wajib untuk sumber terverifikasi.")
        if not data.get("peninjau"):
            masalah.append("peninjau manusia wajib untuk sumber terverifikasi.")
    return masalah

def main():
    parser = argparse.ArgumentParser(description="Periksa metadata provenance dataset")
    parser.add_argument("berkas", type=Path)
    args = parser.parse_args()
    data = json.loads(args.berkas.read_text(encoding="utf-8"))
    errors = validasi_manifest(data)
    if errors:
        for e in errors:
            print("GALAT:", e)
        raise SystemExit(1)
    print("Metadata valid secara struktur; bukan konfirmasi keaslian/izin sumber.")

if __name__ == "__main__":
    main()
