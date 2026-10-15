"""Pencarian inklusif, statistik terverifikasi dan interoperabilitas API."""
import re
import unicodedata
from typing import Annotated
from fastapi import Query, Request
from sqlalchemy import text


def normal(nama):
    return ' '.join(unicodedata.normalize('NFKD',nama).casefold().split())


def pasang_fitur(app, ambil_db, halaman):
    @app.get('/v1/cari-pekerjaan',tags=['pencarian'])
    def cari(request:Request,kata: Annotated[str,Query(min_length=1,max_length=150)],
             batas:Annotated[int,Query(ge=1,le=50)]=20):
        """Pencarian nama/alias literal dengan peringkat deterministik, bukan pemetaan resmi AI."""
        cari_asli=kata.strip().lower().replace('!', '!!').replace('%','!%').replace('_','!_')
        pattern='%'+cari_asli+'%'
        sql=text('''SELECT o.occupation_id AS id_pekerjaan,
            o.preferred_name_id AS nama_pekerjaan,o.alternative_names AS sinonim,
            o.record_status AS status_data, s.sector_name AS sektor
            FROM occupations o JOIN sectors s ON s.sector_id=o.sector_id
            WHERE LOWER(o.preferred_name_id) LIKE :q ESCAPE '!'
               OR LOWER(o.alternative_names) LIKE :q ESCAPE '!'
            ORDER BY o.preferred_name_id,o.occupation_id''')
        with ambil_db(request).connect() as c:
            rows=[dict(x) for x in c.execute(sql,{'q':pattern}).mappings()]
        k=normal(kata)
        def peringkat(x):
            nama=normal(x['nama_pekerjaan']); alias=normal(x['sinonim'] or '')
            return (0 if nama==k else 1 if nama.startswith(k) else 2 if k in nama else 3 if k in alias else 4,nama)
        rows.sort(key=peringkat)
        for row in rows[:batas]:
            row['sinonim']=[a.strip() for a in (row['sinonim'] or '').split('|') if a.strip()]
        return {'data':rows[:batas],'jumlah_ditemukan':len(rows),
                'catatan':'Kecocokan nama/sinonim; bukan pembuktian kode KBJI atau kewenangan profesi.'}

    @app.get('/v1/pemetaan-internasional',tags=['interoperabilitas'])
    def daftar_pemetaan(request:Request,
             sistem_klasifikasi: Annotated[str | None,Query(pattern='^(ISCO|ESCO|O_NET)$')]=None,
             id_pekerjaan:Annotated[str|None,Query(max_length=40)]=None,
             batas:Annotated[int,Query(ge=1,le=100)]=25,
             mulai:Annotated[int,Query(ge=0,le=1000000)]=0):
        where=[]; param={}
        if sistem_klasifikasi: where.append('p.sistem_klasifikasi=:sistem');param['sistem']=sistem_klasifikasi
        if id_pekerjaan: where.append('p.id_pekerjaan=:id');param['id']=id_pekerjaan
        syarat='WHERE '+' AND '.join(where) if where else ''
        with ambil_db(request).connect() as c:
            return halaman(c,'FROM pemetaan_internasional p JOIN data_sources s ON s.source_id=p.sumber_id',
                'p.id_pemetaan,p.id_pekerjaan,p.sistem_klasifikasi,p.edisi,p.kode,p.nama_resmi,p.sumber_id,s.uri AS tautan_sumber',
                syarat,param,'p.sistem_klasifikasi,p.kode',batas,mulai)

    @app.get('/v1/analisis/pengupahan',tags=['analisis'])
    def analisis(request:Request,
                tahun:Annotated[int|None,Query(ge=1900,le=2200)]=None,
                sistem_kode:Annotated[str|None,Query(max_length=50)]=None,
                jenis_data:Annotated[str|None,Query(pattern='^(resmi|survei|estimasi)$')]=None):
        """Ringkas statistik hanya setelah lulus verifikasi, bukan perhitungan UMP dari statistik."""
        syarat=["s.status_verifikasi='terverifikasi'","w.status_verifikasi='terverifikasi'"]
        p={}
        if tahun is not None: syarat.append('s.tahun=:tahun');p['tahun']=tahun
        if sistem_kode: syarat.append('s.sistem_kode=:sistem');p['sistem']=sistem_kode
        if jenis_data: syarat.append('s.jenis_data=:jenis');p['jenis']=jenis_data
        sql=text('''SELECT s.tahun,s.sistem_kode,s.metrik,s.jenis_data,s.satuan,
                 s.cakupan_pekerja,COUNT(*) AS jumlah_rekaman,
                 MIN(s.nilai_rupiah) AS nilai_terendah_rupiah,
                 MAX(s.nilai_rupiah) AS nilai_tertinggi_rupiah
                 FROM statistik_upah s JOIN wilayah_administratif w
                  ON w.sistem_kode=s.sistem_kode AND w.kode_wilayah=s.kode_wilayah
                 WHERE '''+' AND '.join(syarat)+'''
                 GROUP BY s.tahun,s.sistem_kode,s.metrik,s.jenis_data,s.satuan,s.cakupan_pekerja
                 ORDER BY s.tahun DESC,s.sistem_kode,s.metrik''')
        with ambil_db(request).connect() as c:
            hasil=[dict(x) for x in c.execute(sql,p).mappings()]
        return {'data':hasil,'data_tersedia':bool(hasil),
            'catatan':'MIN/MAX hanya rentang antarobservasi sejenis; bukan upah rata-rata gabungan. Satuan, sumber dan cakupan harus dibandingkan konsisten. UMP/UMK tidak digabung.'}
