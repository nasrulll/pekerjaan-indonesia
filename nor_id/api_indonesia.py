"""Rute tambahan Bahasa Indonesia; API lama tetap aktif demi kompatibilitas."""
from __future__ import annotations
from typing import Annotated
from fastapi import FastAPI, HTTPException, Query, Request
from sqlalchemy import text

KETERANGAN_UPAH = (
    'UMP/UMK adalah upah minimum yang ditetapkan; bukan rata-rata penghasilan. '
    'Data upah hanya ditampilkan jika sudah diverifikasi dan memiliki rujukan.'
)
KETERANGAN_WILAYAH = 'Kode wilayah disimpan sebagai teks dan mengikuti sistem kode yang disebutkan.'


def pasang_rute(app: FastAPI, ambil_db, cari_literal, halaman, daftar_pekerjaan_lama):
    def ubah_pekerjaan(baris):
        status={'draft':'draf','reviewed':'ditinjau','published':'dipublikasikan','archived':'diarsipkan'}
        return {
            'id_pekerjaan': baris['occupation_id'],
            'nama_pekerjaan': baris['preferred_name_id'],
            'nama_alternatif': baris['aliases'],
            'id_sektor': baris['sector_id'],
            'nama_sektor': baris['sector_name'],
            'uraian': baris['description_id'],
            'status_data': status.get(baris['record_status'],baris['record_status']),
            'id_sumber': baris['source_id'],
            'kode_kbji_terverifikasi': [x['kbji_code'] for x in baris['kbji_mappings']],
        }

    @app.get('/v1/pekerjaan', tags=['pekerjaan'])
    def daftar_pekerjaan(request: Request,
            nama: Annotated[str,Query(max_length=150)]='',
            id_sektor: Annotated[str|None,Query(max_length=20)]=None,
            batas: Annotated[int,Query(ge=1,le=100)]=25,
            mulai: Annotated[int,Query(ge=0,le=1000000)]=0):
        syarat=[];param={}
        if nama.strip():
            syarat.append("(LOWER(o.preferred_name_id) LIKE :nama ESCAPE '!' OR LOWER(o.alternative_names) LIKE :nama ESCAPE '!')")
            param['nama']=cari_literal(nama)
        if id_sektor:
            syarat.append('o.sector_id=:id_sektor');param['id_sektor']=id_sektor
        where='WHERE '+' AND '.join(syarat) if syarat else ''
        with ambil_db(request).connect() as conn:
            hasil=daftar_pekerjaan_lama(conn,where,param,batas,mulai)
        hasil['data']=[ubah_pekerjaan(x) for x in hasil['data']]
        hasil['catatan']='Sektor editorial dan pekerjaan draf tidak otomatis setara kode KBJI resmi.'
        return hasil

    @app.get('/v1/pekerjaan/{id_pekerjaan}', tags=['pekerjaan'])
    def detail_pekerjaan(request: Request,id_pekerjaan: str):
        with ambil_db(request).connect() as conn:
            hasil=daftar_pekerjaan_lama(conn,'WHERE o.occupation_id=:id',{'id':id_pekerjaan},1,0)
        if not hasil['data']:
            raise HTTPException(status_code=404,detail='Pekerjaan tidak ditemukan')
        return {'data':ubah_pekerjaan(hasil['data'][0]),'catatan':'Periksa status data sebelum dipakai sebagai rujukan resmi.'}

    @app.get('/v1/status-registri', tags=['metadata'])
    def status_registri(request: Request):
        daftar=('occupations','jabatan_nasional','wilayah_administratif','upah_minimum','statistik_upah','kbji_mappings')
        hasil={}
        with ambil_db(request).connect() as conn:
            for tabel in daftar:  # Daftar nama tabel tetap, bukan berasal dari parameter pengguna.
                hasil[tabel]=conn.execute(text(f'SELECT COUNT(*) FROM {tabel}')).scalar_one()
        return {'versi':'0.4.0','nama':'Registri Pekerjaan Indonesia',
                'jumlah_pekerjaan_draf_atau_lainnya':hasil['occupations'],
                'jumlah_jabatan':hasil['jabatan_nasional'],
                'jumlah_wilayah':hasil['wilayah_administratif'],
                'jumlah_upah_minimum':hasil['upah_minimum'],
                'jumlah_statistik_upah':hasil['statistik_upah'],
                'jumlah_pemetaan_kbji_lama':hasil['kbji_mappings'],
                'status_sumber':'CSV tervalidasi dalam Git',
                'catatan': 'Hanya daftar jabatan contoh tersedia; belum ada statistik upah terverifikasi.'}

    @app.get('/v1/jabatan', tags=['jabatan'])
    def daftar_jabatan(request: Request,
            nama: Annotated[str, Query(max_length=150)] = '',
            id_pekerjaan: Annotated[str | None, Query(max_length=40)] = None,
            jenis_jabatan: Annotated[str | None, Query(max_length=50)] = None,
            batas: Annotated[int, Query(ge=1,le=100)] = 25,
            mulai: Annotated[int, Query(ge=0,le=1000000)] = 0):
        syarat=[]; param={}
        if nama.strip():
            syarat.append("LOWER(j.nama_jabatan) LIKE :nama ESCAPE '!'")
            param['nama']=cari_literal(nama)
        if id_pekerjaan:
            syarat.append('j.id_pekerjaan=:id_pekerjaan');param['id_pekerjaan']=id_pekerjaan
        if jenis_jabatan:
            syarat.append('j.jenis_jabatan=:jenis_jabatan');param['jenis_jabatan']=jenis_jabatan
        where='WHERE '+' AND '.join(syarat) if syarat else ''
        from_sql='FROM jabatan_nasional j JOIN occupations p ON p.occupation_id=j.id_pekerjaan'
        select_sql='j.id_jabatan,j.nama_jabatan,j.id_pekerjaan,p.preferred_name_id AS nama_pekerjaan,j.jenis_jabatan,j.id_jabatan_induk,j.jenjang,j.kode_konteks,j.status_verifikasi,j.sumber_id'
        with ambil_db(request).connect() as conn:
            hasil=halaman(conn,from_sql,select_sql,where,param,'j.nama_jabatan,j.id_jabatan',batas,mulai)
        hasil['catatan']='Jabatan contoh/draf bukan nomenklatur ASN atau KBJI resmi.'
        return hasil

    @app.get('/v1/wilayah', tags=['wilayah'])
    def daftar_wilayah(request: Request,
            sistem_kode: Annotated[str | None, Query(max_length=50)] = None,
            kode_induk: Annotated[str | None, Query(max_length=40)] = None,
            jenis_wilayah: Annotated[str | None, Query(pattern='^(provinsi|kabupaten|kota)$')] = None,
            batas: Annotated[int, Query(ge=1,le=100)] = 25,
            mulai: Annotated[int, Query(ge=0,le=1000000)] = 0):
        syarat=["w.status_verifikasi='terverifikasi'"];param={}
        if sistem_kode: syarat.append('w.sistem_kode=:sistem');param['sistem']=sistem_kode
        if kode_induk: syarat.append('w.kode_induk=:induk');param['induk']=kode_induk
        if jenis_wilayah: syarat.append('w.jenis_wilayah=:jenis');param['jenis']=jenis_wilayah
        with ambil_db(request).connect() as conn:
            hasil=halaman(conn,'FROM wilayah_administratif w','w.sistem_kode,w.kode_wilayah,w.nama_wilayah,w.jenis_wilayah,w.kode_induk,w.sumber_id',
                'WHERE '+' AND '.join(syarat),param,'w.sistem_kode,w.kode_wilayah',batas,mulai)
        hasil['catatan']=KETERANGAN_WILAYAH
        hasil['data_tersedia']=bool(hasil['pagination']['total'])
        return hasil

    @app.get('/v1/upah-minimum', tags=['pengupahan'])
    def daftar_upah_minimum(request: Request,
            sistem_kode: Annotated[str | None, Query(max_length=50)] = None,
            kode_wilayah: Annotated[str | None, Query(max_length=40)] = None,
            tahun: Annotated[int | None, Query(ge=1900, le=2200)] = None,
            jenis_upah: Annotated[str | None, Query(pattern='^(UMP|UMK)$')] = None,
            batas: Annotated[int, Query(ge=1,le=100)] = 25,
            mulai: Annotated[int, Query(ge=0,le=1000000)] = 0):
        syarat=["u.status_verifikasi='terverifikasi'"];param={}
        for nama,nilai,kolom in [('sistem_kode',sistem_kode,'u.sistem_kode'),('kode_wilayah',kode_wilayah,'u.kode_wilayah'),('tahun',tahun,'u.tahun'),('jenis_upah',jenis_upah,'u.jenis_upah')]:
            if nilai is not None: syarat.append(f'{kolom}=:{nama}');param[nama]=nilai
        sql='FROM upah_minimum u JOIN wilayah_administratif w ON w.sistem_kode=u.sistem_kode AND w.kode_wilayah=u.kode_wilayah AND w.status_verifikasi=\'terverifikasi\' JOIN data_sources s ON s.source_id=u.sumber_id'
        select='u.id_upah,u.sistem_kode,u.kode_wilayah,w.nama_wilayah,u.tahun,u.jenis_upah,u.nilai_rupiah,u.tanggal_mulai,u.sumber_id,s.title AS judul_sumber,s.uri AS tautan_sumber,u.status_verifikasi'
        with ambil_db(request).connect() as conn:
            hasil=halaman(conn,sql,select,'WHERE '+' AND '.join(syarat),param,'u.tahun DESC,u.kode_wilayah',batas,mulai)
        for baris in hasil['data']:
            for nama in ('tanggal_mulai',):
                if baris[nama] is not None: baris[nama]=str(baris[nama])
        hasil['catatan']=KETERANGAN_UPAH
        hasil['data_tersedia']=bool(hasil['pagination']['total'])
        return hasil

    @app.get('/v1/statistik-upah', tags=['pengupahan'])
    def daftar_statistik_upah(request: Request,
            sistem_kode: Annotated[str | None, Query(max_length=50)] = None,
            kode_wilayah: Annotated[str | None, Query(max_length=40)] = None,
            tahun: Annotated[int | None, Query(ge=1900,le=2200)] = None,
            id_pekerjaan: Annotated[str | None, Query(max_length=40)] = None,
            id_jabatan: Annotated[str | None, Query(max_length=40)] = None,
            metrik: Annotated[str | None, Query(pattern='^(rata_rata|median|persentil_25|persentil_75)$')] = None,
            batas: Annotated[int, Query(ge=1,le=100)] = 25,
            mulai: Annotated[int, Query(ge=0,le=1000000)] = 0):
        syarat=["u.status_verifikasi='terverifikasi'", "u.jenis_data IN ('resmi','survei','estimasi')"];param={}
        for nama,nilai,kolom in [('sistem_kode',sistem_kode,'u.sistem_kode'),('kode_wilayah',kode_wilayah,'u.kode_wilayah'),('tahun',tahun,'u.tahun'),('id_pekerjaan',id_pekerjaan,'u.id_pekerjaan'),('id_jabatan',id_jabatan,'u.id_jabatan'),('metrik',metrik,'u.metrik')]:
            if nilai is not None: syarat.append(f'{kolom}=:{nama}');param[nama]=nilai
        sql='FROM statistik_upah u JOIN wilayah_administratif w ON w.sistem_kode=u.sistem_kode AND w.kode_wilayah=u.kode_wilayah AND w.status_verifikasi=\'terverifikasi\' JOIN data_sources s ON s.source_id=u.sumber_id'
        select='u.id_statistik,u.sistem_kode,u.kode_wilayah,w.nama_wilayah,u.tahun,u.id_pekerjaan,u.id_jabatan,u.metrik,u.nilai_rupiah,u.satuan,u.cakupan_pekerja,u.jenis_data,u.jumlah_sampel,u.status_verifikasi,u.sumber_id,s.title AS judul_sumber,s.uri AS tautan_sumber'
        with ambil_db(request).connect() as conn:
            hasil=halaman(conn,sql,select,'WHERE '+' AND '.join(syarat),param,'u.tahun DESC,u.kode_wilayah,u.metrik',batas,mulai)
        hasil['catatan']='Jenis data resmi, survei, dan estimasi dipisahkan. Statistik upah bukan UMP/UMK.'
        hasil['data_tersedia']=bool(hasil['pagination']['total'])
        return hasil
