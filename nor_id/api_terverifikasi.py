"""Endpoint historis RPI: fail-closed, hanya subset sumber yang diizinkan operator.

Status 'terverifikasi' adalah metadata hasil tinjauan, bukan bukti pemerintah.
Tabel kandidat tetap nonpublik. Endpoint v0.4 lama tidak diubah.
"""
from __future__ import annotations

import os
import re
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from sqlalchemy import and_, exists, func, inspect, or_, select
from sqlalchemy.orm import aliased

from .skema_histori import keputusan, sumber, taksonomi_kbji, wilayah


CATATAN = (
    "Data historis hanya dirilis melalui persetujuan operator dan pemeriksaan "
    "metadata. Status terverifikasi tidak menggantikan pembuktian sumber primer."
)


def sumber_dibolehkan() -> tuple[str, ...]:
    """Dua gerbang eksplisit, default deny. Impor KANDIDAT tidak dapat diaktifkan."""
    if os.getenv("RPI_PUBLIKASI_HISTORIS", "").strip().lower() != "aktif":
        return ()
    values = os.getenv("RPI_SUMBER_DISETUJUI_PUBLIK", "")
    ids = {s.strip() for s in values.split(",") if s.strip()}
    return tuple(sorted(
        s for s in ids if re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", s)
        and not s.upper().startswith(("KANDIDAT-", "KAND-"))
    ))


def sumber_lolos(s, allowed, jenis, edisi=None):
    syarat = [
        s.c.id_sumber.in_(allowed),
        s.c.status_verifikasi == "terverifikasi",
        s.c.jenis_sumber == jenis,
        s.c.izin_distribusi == "diizinkan",
        s.c.rujukan_izin.is_not(None),
        s.c.rujukan_izin != "",
        s.c.peninjau.is_not(None),
        s.c.peninjau != "",
        s.c.tanggal_verifikasi.is_not(None),
        func.length(s.c.sha256_berkas_asli) == 64,
        s.c.url_resmi.like("https://%"),
    ]
    if edisi is not None:
        syarat.append(s.c.edisi == edisi)
    return and_(*syarat)


def kosong(batas, mulai, status):
    return {
        "data": [], "pagination": {"total": 0, "limit": batas, "offset": mulai, "has_more": False},
        "data_tersedia": False, "status_layanan": status, "catatan": CATATAN,
    }


def query_hal(conn, table_expr, fields, syarat, urutan, batas, mulai):
    total = conn.execute(select(func.count()).select_from(table_expr).where(*syarat)).scalar_one()
    records = [
        dict(item) for item in conn.execute(
            select(*fields).select_from(table_expr).where(*syarat)
            .order_by(*urutan).limit(batas).offset(mulai)
        ).mappings()
    ]
    return {
        "data": records,
        "pagination": {"total": total, "limit": batas, "offset": mulai,
                       "has_more": mulai + len(records) < total},
        "data_tersedia": bool(records),
        "status_layanan": "aktif_terkendali",
        "catatan": CATATAN,
    }


def butuh_skema(conn, table_names):
    if not set(table_names).issubset(set(inspect(conn).get_table_names())):
        raise HTTPException(
            status_code=503, detail="Skema historis belum lengkap; lakukan migrasi Alembic."
        )


def pasang_rute_terverifikasi(app: FastAPI, ambil_db):
    @app.get("/v1/kbji/terverifikasi", tags=["data historis terverifikasi"])
    def kbji_terverifikasi(
        request: Request,
        edisi: Annotated[str | None, Query(max_length=80)] = None,
        kode: Annotated[str | None, Query(max_length=8)] = None,
        batas: Annotated[int, Query(ge=1, le=100)] = 25,
        mulai: Annotated[int, Query(ge=0, le=1000000)] = 0,
    ):
        allowed = sumber_dibolehkan()
        if not allowed:
            return kosong(batas, mulai, "dinonaktifkan_menunggu_persetujuan_operator")
        k, s = taksonomi_kbji, sumber.alias("s")
        parent, ps = taksonomi_kbji.alias("induk"), sumber.alias("s_induk")
        from_ = (
            k.join(s, k.c.id_sumber == s.c.id_sumber)
            .outerjoin(parent, and_(k.c.edisi == parent.c.edisi,
                                    k.c.kode_induk == parent.c.kode))
            .outerjoin(ps, parent.c.id_sumber == ps.c.id_sumber)
        )
        syarat = [
            k.c.status_verifikasi == "terverifikasi",
            sumber_lolos(s, allowed, "klasifikasi_kbji", k.c.edisi),
            or_(
                and_(k.c.kode_induk.is_(None), k.c.tingkat == 1),
                and_(parent.c.status_verifikasi == "terverifikasi",
                     parent.c.tingkat == k.c.tingkat - 1,
                     sumber_lolos(ps, allowed, "klasifikasi_kbji", parent.c.edisi)),
            ),
        ]
        if edisi is not None:
            syarat.append(k.c.edisi == edisi)
        if kode is not None:
            syarat.append(k.c.kode == kode)
        fields = [
            k.c.edisi, k.c.kode, k.c.nama, k.c.kode_induk, k.c.tingkat,
            k.c.id_sumber, s.c.penerbit.label("penerbit"),
            s.c.url_resmi.label("url_sumber"),
            s.c.rujukan_izin.label("rujukan_izin"),
        ]
        with ambil_db(request).connect() as conn:
            butuh_skema(conn, [k.name, s.name])
            return query_hal(conn, from_, fields, syarat, [k.c.edisi, k.c.kode], batas, mulai)

    @app.get("/v1/wilayah-historis/terverifikasi", tags=["data historis terverifikasi"])
    def wilayah_terverifikasi(
        request: Request,
        sistem_kode: Annotated[str | None, Query(max_length=40)] = None,
        edisi: Annotated[str | None, Query(max_length=80)] = None,
        jenis_wilayah: Annotated[str | None, Query(pattern="^(provinsi|kabupaten|kota)$")] = None,
        kode_wilayah: Annotated[str | None, Query(max_length=48)] = None,
        batas: Annotated[int, Query(ge=1, le=100)] = 25,
        mulai: Annotated[int, Query(ge=0, le=1000000)] = 0,
    ):
        allowed = sumber_dibolehkan()
        if not allowed:
            return kosong(batas, mulai, "dinonaktifkan_menunggu_persetujuan_operator")
        w, s = wilayah, sumber.alias("s")
        parent, ps = wilayah.alias("induk"), sumber.alias("s_induk")
        from_ = (
            w.join(s, w.c.id_sumber == s.c.id_sumber)
            .outerjoin(parent, and_(w.c.sistem_kode == parent.c.sistem_kode,
                                    w.c.edisi == parent.c.edisi,
                                    w.c.kode_induk == parent.c.kode_wilayah))
            .outerjoin(ps, parent.c.id_sumber == ps.c.id_sumber)
        )
        syarat = [
            w.c.status_verifikasi == "terverifikasi",
            sumber_lolos(s, allowed, "kode_wilayah", w.c.edisi),
            or_(
                and_(w.c.jenis_wilayah == "provinsi", w.c.kode_induk.is_(None)),
                and_(
                    w.c.jenis_wilayah.in_(("kabupaten", "kota")),
                    parent.c.jenis_wilayah == "provinsi",
                    parent.c.status_verifikasi == "terverifikasi",
                    sumber_lolos(ps, allowed, "kode_wilayah", parent.c.edisi),
                ),
            ),
        ]
        if sistem_kode is not None:
            syarat.append(w.c.sistem_kode == sistem_kode)
        if edisi is not None:
            syarat.append(w.c.edisi == edisi)
        if jenis_wilayah is not None:
            syarat.append(w.c.jenis_wilayah == jenis_wilayah)
        if kode_wilayah is not None:
            syarat.append(w.c.kode_wilayah == kode_wilayah)
        fields = [w.c.sistem_kode, w.c.edisi, w.c.kode_wilayah, w.c.nama_wilayah,
                  w.c.jenis_wilayah, w.c.kode_induk, w.c.id_sumber,
                  s.c.penerbit.label("penerbit"), s.c.url_resmi.label("url_sumber")]
        with ambil_db(request).connect() as conn:
            butuh_skema(conn, [w.name, s.name])
            return query_hal(
                conn, from_, fields, syarat,
                [w.c.sistem_kode, w.c.edisi, w.c.kode_wilayah], batas, mulai
            )

    @app.get("/v1/upah-minimum-historis/terverifikasi", tags=["data historis terverifikasi"])
    def upah_terverifikasi(
        request: Request,
        sistem_kode: Annotated[str | None, Query(max_length=40)] = None,
        edisi_wilayah: Annotated[str | None, Query(max_length=80)] = None,
        kode_wilayah: Annotated[str | None, Query(max_length=48)] = None,
        tahun: Annotated[int | None, Query(ge=1900, le=2200)] = None,
        jenis_upah: Annotated[str | None, Query(pattern="^(UMP|UMK)$")] = None,
        batas: Annotated[int, Query(ge=1, le=100)] = 25,
        mulai: Annotated[int, Query(ge=0, le=1000000)] = 0,
    ):
        allowed = sumber_dibolehkan()
        if not allowed:
            return kosong(batas, mulai, "dinonaktifkan_menunggu_persetujuan_operator")
        d, s = keputusan, sumber.alias("s")
        w, ws = wilayah.alias("w"), sumber.alias("s_wilayah")
        parent, ps = wilayah.alias("induk"), sumber.alias("s_induk")
        from_ = (
            d.join(s, d.c.id_sumber == s.c.id_sumber)
            .join(w, and_(
                d.c.sistem_kode == w.c.sistem_kode,
                d.c.edisi_wilayah == w.c.edisi,
                d.c.kode_wilayah == w.c.kode_wilayah,
            ))
            .join(ws, w.c.id_sumber == ws.c.id_sumber)
            .outerjoin(parent, and_(
                w.c.sistem_kode == parent.c.sistem_kode,
                w.c.edisi == parent.c.edisi,
                w.c.kode_induk == parent.c.kode_wilayah,
            ))
            .outerjoin(ps, parent.c.id_sumber == ps.c.id_sumber)
        )
        # Fail closed bila terdapat lebih dari satu keputusan berlaku untuk kelompok yang sama.
        duplikat = keputusan.alias("duplikat")
        ada_keputusan_lain = exists(
            select(1).select_from(duplikat).where(and_(
                duplikat.c.id_keputusan != d.c.id_keputusan,
                duplikat.c.sistem_kode == d.c.sistem_kode,
                duplikat.c.edisi_wilayah == d.c.edisi_wilayah,
                duplikat.c.kode_wilayah == d.c.kode_wilayah,
                duplikat.c.tahun == d.c.tahun,
                duplikat.c.jenis_upah == d.c.jenis_upah,
                duplikat.c.status_keputusan == "berlaku",
            ))
        )
        syarat = [
            d.c.status_verifikasi == "terverifikasi",
            d.c.status_keputusan == "berlaku",
            d.c.nilai_rupiah > 0,
            ~ada_keputusan_lain,
            sumber_lolos(s, allowed, "upah_minimum", None),
            s.c.edisi == d.c.tahun.cast(s.c.edisi.type),
            w.c.status_verifikasi == "terverifikasi",
            sumber_lolos(ws, allowed, "kode_wilayah", w.c.edisi),
            or_(
                and_(d.c.jenis_upah == "UMP", w.c.jenis_wilayah == "provinsi",
                     w.c.kode_induk.is_(None)),
                and_(d.c.jenis_upah == "UMK",
                     w.c.jenis_wilayah.in_(("kabupaten", "kota")),
                     parent.c.jenis_wilayah == "provinsi",
                     parent.c.status_verifikasi == "terverifikasi",
                     sumber_lolos(ps, allowed, "kode_wilayah", parent.c.edisi)),
            ),
        ]
        if sistem_kode is not None:
            syarat.append(d.c.sistem_kode == sistem_kode)
        if edisi_wilayah is not None:
            syarat.append(d.c.edisi_wilayah == edisi_wilayah)
        if kode_wilayah is not None:
            syarat.append(d.c.kode_wilayah == kode_wilayah)
        if tahun is not None:
            syarat.append(d.c.tahun == tahun)
        if jenis_upah is not None:
            syarat.append(d.c.jenis_upah == jenis_upah)
        fields = [
            d.c.id_keputusan, d.c.sistem_kode, d.c.edisi_wilayah, d.c.kode_wilayah,
            w.c.nama_wilayah, d.c.tahun, d.c.jenis_upah, d.c.nilai_rupiah,
            d.c.tanggal_mulai, d.c.nomor_keputusan, d.c.tanggal_keputusan,
            d.c.status_keputusan, d.c.id_sumber, s.c.penerbit.label("penerbit"),
            s.c.url_resmi.label("url_sumber"), s.c.rujukan_izin.label("rujukan_izin"),
        ]
        with ambil_db(request).connect() as conn:
            butuh_skema(conn, [d.name, s.name, wilayah.name])
            return query_hal(
                conn, from_, fields, syarat,
                [d.c.tahun.desc(), d.c.sistem_kode, d.c.kode_wilayah, d.c.id_keputusan],
                batas, mulai,
            )
