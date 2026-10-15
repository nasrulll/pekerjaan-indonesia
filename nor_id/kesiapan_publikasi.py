"""Audit integritas klaim verifikasi RPI; BUKAN otorisasi data pemerintah.

Hanya memeriksa relasi dan bukti metadata dalam basis data historis.
Tidak mempromosikan status data, mengubah database, atau memublikasikan nominal.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import re

from sqlalchemy import inspect, select

from .skema_histori import sumber, wilayah, taksonomi_kbji, keputusan

TABEL = (sumber, wilayah, taksonomi_kbji, keputusan)
SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
STATUS = ("draf", "ditinjau", "terverifikasi")


def audit_kesiapan(engine):
    """Keluarkan laporan ringkas tanpa nama peninjau atau nominal upah."""
    laporan = {
        "jenis": "audit_integritas_teknis_bukan_pengesahan_pemerintah",
        "skema_lengkap": False,
        "jumlah": {},
        "temuan": [],
        "peringatan": [],
        "status_kesiapan": "belum_diperiksa",
        "publikasi_diizinkan_otomatis": False,
    }
    with engine.connect() as conn:
        tersedia = set(inspect(conn).get_table_names())
        hilang = [t.name for t in TABEL if t.name not in tersedia]
        if hilang:
            laporan["temuan"] = [f"TABEL_HILANG:{nama}" for nama in hilang]
            laporan["status_kesiapan"] = "skema_belum_siap"
            return laporan
        laporan["skema_lengkap"] = True
        data = {t.name: [dict(row) for row in conn.execute(select(t)).mappings()] for t in TABEL}

    temuan = set()
    sources = {r["id_sumber"]: r for r in data[sumber.name]}
    regions = {(r["sistem_kode"], r["edisi"], r["kode_wilayah"]): r
               for r in data[wilayah.name]}
    kbji = {(r["edisi"], r["kode"]): r for r in data[taksonomi_kbji.name]}
    decisions = {r["id_keputusan"]: r for r in data[keputusan.name]}
    verified_total = 0

    for table in TABEL:
        records = data[table.name]
        counts = Counter(x["status_verifikasi"] for x in records)
        laporan["jumlah"][table.name] = {s: counts.get(s, 0) for s in STATUS}
        laporan["jumlah"][table.name]["total"] = len(records)
        for r in records:
            if r["status_verifikasi"] not in STATUS:
                temuan.add(f"STATUS_TIDAK_SAH:{table.name}")
            if r["status_verifikasi"] == "terverifikasi" and table is not sumber:
                verified_total += 1

    for s in data[sumber.name]:
        if s["status_verifikasi"] != "terverifikasi":
            continue
        kode = s["id_sumber"]
        if s["izin_distribusi"] != "diizinkan" or not s["rujukan_izin"]:
            temuan.add(f"SUMBER_IZIN_BELUM_MEMADAI:{kode}")
        if not s["sha256_berkas_asli"] or not SHA256.fullmatch(s["sha256_berkas_asli"]):
            temuan.add(f"SUMBER_CHECKSUM_TIDAK_SAH:{kode}")
        if not s["peninjau"] or not s["tanggal_verifikasi"]:
            temuan.add(f"SUMBER_PENINJAU_BELUM_LENGKAP:{kode}")
        if not s["penerbit"] or not s["judul"] or not s["url_resmi"].startswith("https://"):
            temuan.add(f"SUMBER_IDENTITAS_TIDAK_MEMADAI:{kode}")

    def check_source(record, identifier, jenis, edisi=None):
        src = sources.get(record["id_sumber"])
        if src is None or src["status_verifikasi"] != "terverifikasi":
            temuan.add(f"ENTRI_TANPA_SUMBER_TERVERIFIKASI:{identifier}")
            return
        if src["jenis_sumber"] != jenis:
            temuan.add(f"ENTRI_JENIS_SUMBER_TIDAK_COCOK:{identifier}")
        if edisi is not None and src["edisi"] != str(edisi):
            temuan.add(f"ENTRI_EDISI_SUMBER_TIDAK_COCOK:{identifier}")

    for r in data[kbji_table_name := taksonomi_kbji.name]:
        if r["status_verifikasi"] != "terverifikasi":
            continue
        key = (r["edisi"], r["kode"])
        nama = f"KBJI:{r['edisi']}:{r['kode']}"
        check_source(r, nama, "klasifikasi_kbji", r["edisi"])
        parent_code = r["kode_induk"]
        if not r["kode"].isascii() or not r["kode"].isdigit() or not 1 <= len(r["kode"]) <= 8:
            temuan.add(f"KBJI_KODE_TIDAK_SAH:{nama}")
        if parent_code:
            parent = kbji.get((r["edisi"], parent_code))
            if parent is None or parent["status_verifikasi"] != "terverifikasi":
                temuan.add(f"KBJI_INDUK_TIDAK_TERVERIFIKASI:{nama}")
            elif r["tingkat"] != parent["tingkat"] + 1:
                temuan.add(f"KBJI_HIERARKI_TIDAK_SESUAI:{nama}")
        elif r["tingkat"] != 1:
            temuan.add(f"KBJI_AKAR_TINGKAT_TIDAK_SAH:{nama}")

    for r in data[wilayah.name]:
        if r["status_verifikasi"] != "terverifikasi":
            continue
        nama = f"WILAYAH:{r['sistem_kode']}:{r['edisi']}:{r['kode_wilayah']}"
        check_source(r, nama, "kode_wilayah", r["edisi"])
        parent_code = r["kode_induk"]
        if r["jenis_wilayah"] == "provinsi":
            if parent_code:
                temuan.add(f"WILAYAH_PROVINSI_PUNYA_INDUK:{nama}")
        elif r["jenis_wilayah"] in ("kabupaten", "kota"):
            parent = regions.get((r["sistem_kode"], r["edisi"], parent_code))
            if parent is None or parent["jenis_wilayah"] != "provinsi" or parent["status_verifikasi"] != "terverifikasi":
                temuan.add(f"WILAYAH_INDUK_TIDAK_TERVERIFIKASI:{nama}")
        else:
            temuan.add(f"WILAYAH_JENIS_TIDAK_SAH:{nama}")

    aktif = defaultdict(list)
    successors = defaultdict(list)
    for r in data[keputusan.name]:
        if r["status_verifikasi"] != "terverifikasi":
            continue
        nama = f"UPAH:{r['id_keputusan']}"
        check_source(r, nama, "upah_minimum", r["tahun"])
        ref = (r["sistem_kode"], r["edisi_wilayah"], r["kode_wilayah"])
        w = regions.get(ref)
        if w is None or w["status_verifikasi"] != "terverifikasi":
            temuan.add(f"UPAH_WILAYAH_TIDAK_TERVERIFIKASI:{nama}")
        elif (r["jenis_upah"] == "UMP" and w["jenis_wilayah"] != "provinsi") or (
            r["jenis_upah"] == "UMK" and w["jenis_wilayah"] not in ("kabupaten", "kota")
        ):
            temuan.add(f"UPAH_TINGKAT_WILAYAH_TIDAK_SESUAI:{nama}")
        group = (*ref, r["tahun"], r["jenis_upah"])
        if r["status_keputusan"] == "berlaku":
            aktif[group].append(r["id_keputusan"])
        if r["id_keputusan_digantikan"]:
            lama = decisions.get(r["id_keputusan_digantikan"])
            if lama is None or lama["status_verifikasi"] != "terverifikasi":
                temuan.add(f"UPAH_PENDAHULU_TIDAK_TERVERIFIKASI:{nama}")
            else:
                grup_lama = (lama["sistem_kode"], lama["edisi_wilayah"], lama["kode_wilayah"], lama["tahun"], lama["jenis_upah"])
                if group != grup_lama or lama["status_keputusan"] != "diganti":
                    temuan.add(f"UPAH_RANTAI_TIDAK_KONSISTEN:{nama}")
            successors[r["id_keputusan_digantikan"]].append(r["id_keputusan"])
        if r["status_keputusan"] not in ("berlaku", "diganti", "dicabut"):
            temuan.add(f"UPAH_STATUS_KEPUTUSAN_TIDAK_SAH:{nama}")
        if r["nilai_rupiah"] <= 0:
            temuan.add(f"UPAH_NOMINAL_TIDAK_SAH:{nama}")

    for group, ids in aktif.items():
        if len(ids) > 1:
            temuan.add(f"UPAH_KEPUTUSAN_AKTIF_GANDA:{'/'.join(map(str, group))}")
    for r in data[keputusan.name]:
        if r["status_verifikasi"] != "terverifikasi":
            continue
        ident = r["id_keputusan"]
        if len(successors.get(ident, [])) > 1:
            temuan.add(f"UPAH_KEPUTUSAN_PENGGANTI_GANDA:{ident}")
        if r["status_keputusan"] == "diganti" and not successors.get(ident):
            temuan.add(f"UPAH_PENGGANTI_BELUM_TERVERIFIKASI:{ident}")
        seen = set()
        cur = ident
        while cur and cur in decisions and decisions[cur]["status_verifikasi"] == "terverifikasi":
            if cur in seen:
                temuan.add(f"UPAH_RANTAI_SIKLUS:{ident}")
                break
            seen.add(cur)
            cur = decisions[cur]["id_keputusan_digantikan"]

    laporan["temuan"] = sorted(temuan)
    if verified_total == 0:
        laporan["peringatan"].append("Belum ada entri historis yang dinyatakan terverifikasi.")
    if laporan["temuan"]:
        laporan["status_kesiapan"] = "perlu_perbaikan_integritas"
    elif verified_total == 0:
        laporan["status_kesiapan"] = "menunggu_dataset_resmi"
    else:
        laporan["status_kesiapan"] = "lolos_pemeriksaan_teknis_menunggu_otorisasi_manusia"
    return laporan
