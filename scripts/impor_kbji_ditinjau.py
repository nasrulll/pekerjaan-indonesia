"""CLI: validasi paket KBJI calon, lalu impor status ditinjau jika --terapkan."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from nor_id.impor_kbji_ditinjau import siapkan_paket, terapkan_paket


def main() -> int:
    p = argparse.ArgumentParser(description="Impor KBJI berstatus ditinjau, bukan pengesahan resmi")
    p.add_argument("--csv", required=True, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--berkas-asli", required=True, type=Path)
    p.add_argument("--persetujuan", required=True, type=Path)
    p.add_argument("--terapkan", action="store_true", help="Tuliskan ke RPI_DATABASE_URL sesudah validasi")
    args = p.parse_args()
    try:
        rows, manifest, bukti = siapkan_paket(args.csv, args.manifest, args.berkas_asli, args.persetujuan)
        result = {"jumlah_baris": len(rows), "id_sumber": bukti["id_sumber"],
                  "status": "siap_impor_ditinjau", "diterapkan": False}
        if args.terapkan:
            url = os.environ.get("RPI_DATABASE_URL")
            if not url:
                raise ValueError("RPI_DATABASE_URL wajib untuk --terapkan")
            result.update(terapkan_paket(url, rows, manifest, bukti))
            result["diterapkan"] = True
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as err:
        p.error(str(err))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
