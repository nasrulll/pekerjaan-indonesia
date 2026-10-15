"""CLI RPI untuk memasukkan calon wilayah, bukan kode resmi."""
import argparse
import json
import os
from pathlib import Path
from nor_id.impor_wilayah_ditinjau import siapkan_paket, terapkan_paket

def main():
    p = argparse.ArgumentParser(description="Impor wilayah berstatus ditinjau")
    for field in ("csv", "manifest", "berkas-asli", "persetujuan"):
        p.add_argument("--" + field, required=True, type=Path)
    p.add_argument("--terapkan", action="store_true")
    args = p.parse_args()
    try:
        rows, manifest, bukti = siapkan_paket(args.csv, args.manifest, args.berkas_asli, args.persetujuan)
        hasil = {"jumlah_baris": len(rows), "diterapkan": False, "status": "siap_impor_ditinjau"}
        if args.terapkan:
            url = os.environ.get("RPI_DATABASE_URL")
            if not url:
                raise ValueError("RPI_DATABASE_URL belum disetel")
            hasil.update(terapkan_paket(url, rows, manifest, bukti))
            hasil["diterapkan"] = True
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    print(json.dumps(hasil, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
