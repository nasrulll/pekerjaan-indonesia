"""Validasi relasi, sumber, dan angka untuk tabel berbahasa Indonesia v0.3."""
from __future__ import annotations
import csv
import re
from datetime import date
from pathlib import Path
from catalog_tables import COLUMNS

FILES = {table: f'data/{table}.csv' for table in (
    'jabatan_nasional','wilayah_administratif','pemetaan_jabatan_kbji',
    'kompetensi_jabatan','upah_minimum','statistik_upah','kelas_gaji','pemetaan_internasional')}


def validasi(root: Path, pembaca):
    galat: list[str] = []
    data = {}
    for tabel, filename in FILES.items():
        path = root / filename
        try:
            with path.open(encoding='utf-8-sig', newline='') as handle:
                header = next(csv.reader(handle), [])
            if len(header) != len(set(header)) or set(header) != set(COLUMNS[tabel]):
                galat.append(f'{filename}: kolom tidak sesuai kontrak')
            data[tabel] = pembaca(path)
        except (OSError, UnicodeError, csv.Error) as exc:
            galat.append(f'{filename}: gagal dibaca: {exc}')
            data[tabel] = []
    if galat:
        return galat, {}

    pekerjaan = {x['occupation_id'] for x in pembaca(root / 'data/occupations.csv')}
    sumber = {x['source_id']: x for x in pembaca(root / 'data/sources.csv')}
    konteks = {x['context_code'] for x in pembaca(root / 'data/reference/employment_contexts.csv')}
    jabatan = {x['id_jabatan']: x for x in data['jabatan_nasional']}
    wilayah = {(x['sistem_kode'], x['kode_wilayah']): x for x in data['wilayah_administratif']}
    kbji = set()

    def unik(tabel, kunci):
        dilihat = set()
        for nomor, baris in enumerate(data[tabel], 2):
            nilai = tuple(baris.get(k, '') for k in kunci)
            if not all(nilai) or nilai in dilihat:
                galat.append(f'{tabel}:{nomor}: kunci utama kosong atau ganda {nilai}')
            dilihat.add(nilai)

    def cek_sumber(tabel, nomor, baris):
        ref = sumber.get(baris.get('sumber_id', ''))
        if ref is None:
            galat.append(f'{tabel}:{nomor}: sumber tidak tercatat')
        elif baris.get('status_verifikasi') == 'terverifikasi' and not ref.get('uri'):
            galat.append(f'{tabel}:{nomor}: sumber terverifikasi membutuhkan URI bukti')
        if baris.get('status_verifikasi') == 'terverifikasi' and not tanggal(baris.get('tanggal_verifikasi', '')):
            galat.append(f'{tabel}:{nomor}: tanggal verifikasi wajib')
        return ref

    def tanggal(value):
        try:
            date.fromisoformat(value)
            return True
        except (ValueError, TypeError):
            return False

    def uang(tabel, nomor, baris, field='nilai_rupiah', positif=True):
        value = baris.get(field, '')
        try:
            if not re.fullmatch(r'\d+', value): raise ValueError()
            nominal = int(value)
            if nominal < (1 if positif else 0): raise ValueError()
        except (TypeError, ValueError):
            galat.append(f'{tabel}:{nomor}: nominal {field} tidak valid')

    def tahun(tabel, nomor, baris):
        try:
            value = int(baris['tahun'])
            if not (1900 <= value <= 2200): raise ValueError()
        except (ValueError, KeyError):
            galat.append(f'{tabel}:{nomor}: tahun tidak valid')

    for tabel, pk in [
        ('jabatan_nasional',['id_jabatan']),
        ('wilayah_administratif',['sistem_kode','kode_wilayah']),
        ('pemetaan_jabatan_kbji',['id_jabatan','edisi_kbji','kode_kbji']),
        ('kompetensi_jabatan',['id_kompetensi']),('upah_minimum',['id_upah']),
        ('statistik_upah',['id_statistik']),('kelas_gaji',['id_kelas_gaji']),
        ('pemetaan_internasional',['id_pemetaan'])
    ]:
        unik(tabel, pk)

    for i, item in enumerate(data['jabatan_nasional'], 2):
        cek_sumber('jabatan_nasional', i, item)
        if not item['nama_jabatan'] or item['id_pekerjaan'] not in pekerjaan:
            galat.append(f'jabatan_nasional:{i}: pekerjaan atau nama jabatan tidak valid')
        if item['id_jabatan_induk'] and item['id_jabatan_induk'] not in jabatan:
            galat.append(f'jabatan_nasional:{i}: induk jabatan tidak ditemukan')
        if item['kode_konteks'] and item['kode_konteks'] not in konteks:
            galat.append(f'jabatan_nasional:{i}: konteks tidak ditemukan')
        if item['status_verifikasi'] not in ('draf','terverifikasi'):
            galat.append(f'jabatan_nasional:{i}: status tidak valid')
    for idj in jabatan:
        sudah = set()
        induk = idj
        while induk and induk in jabatan:
            if induk in sudah:
                galat.append(f'jabatan_nasional:{idj}: hierarki berputar')
                break
            sudah.add(induk)
            induk = jabatan[induk]['id_jabatan_induk']

    for i, item in enumerate(data['wilayah_administratif'], 2):
        cek_sumber('wilayah_administratif',i,item)
        if item['jenis_wilayah'] not in ('provinsi','kabupaten','kota'):
            galat.append(f'wilayah_administratif:{i}: jenis wilayah tidak valid')
        if item['status_verifikasi'] not in ('draf','terverifikasi'):
            galat.append(f'wilayah_administratif:{i}: status tidak valid')
        if item['jenis_wilayah']=='provinsi' and item['kode_induk']:
            galat.append(f'wilayah_administratif:{i}: provinsi tidak boleh punya induk')
        if item['jenis_wilayah'] in ('kabupaten','kota'):
            induk = wilayah.get((item['sistem_kode'],item['kode_induk']))
            if not induk or induk['jenis_wilayah']!='provinsi':
                galat.append(f'wilayah_administratif:{i}: induk harus provinsi dalam sistem kode yang sama')

    for i,item in enumerate(data['pemetaan_jabatan_kbji'], 2):
        cek_sumber('pemetaan_jabatan_kbji',i,item)
        if item['id_jabatan'] not in jabatan or not re.fullmatch(r'[0-9]{1,8}', item['kode_kbji']):
            galat.append(f'pemetaan_jabatan_kbji:{i}: jabatan/kode tidak valid')
        if not item['nama_kbji'] or not item['edisi_kbji'] or not item['diverifikasi_oleh'] or not tanggal(item['tanggal_verifikasi']):
            galat.append(f'pemetaan_jabatan_kbji:{i}: bukti verifikasi wajib')

    for i,item in enumerate(data['kompetensi_jabatan'],2):
        cek_sumber('kompetensi_jabatan',i,item)
        if item['id_jabatan'] not in jabatan or not item['nama_kompetensi'] or not item['kategori']:
            galat.append(f'kompetensi_jabatan:{i}: jabatan/kompetensi tidak valid')
        if item['status_verifikasi'] not in ('draf','terverifikasi'):
            galat.append(f'kompetensi_jabatan:{i}: status tidak valid')

    wilayah_upah = set()
    for i,item in enumerate(data['upah_minimum'],2):
        sumber_upah = cek_sumber('upah_minimum',i,item)
        if sumber_upah and sumber_upah['kind'] != 'official':
            galat.append(f'upah_minimum:{i}: UMP/UMK harus berasal dari sumber pemerintah resmi')
        tempat = wilayah.get((item['sistem_kode'],item['kode_wilayah']))
        if not tempat or tempat['status_verifikasi']!='terverifikasi':
            galat.append(f'upah_minimum:{i}: wilayah harus sudah terverifikasi')
        elif item['jenis_upah'] == 'UMP' and tempat['jenis_wilayah']!='provinsi' or item['jenis_upah']=='UMK' and tempat['jenis_wilayah'] not in ('kabupaten','kota'):
            galat.append(f'upah_minimum:{i}: UMP hanya provinsi, UMK hanya kabupaten/kota')
        if item['jenis_upah'] not in ('UMP','UMK') or item['status_verifikasi'] not in ('draf','terverifikasi'):
            galat.append(f'upah_minimum:{i}: jenis/status upah tidak valid')
        key=(item['sistem_kode'],item['kode_wilayah'],item['tahun'],item['jenis_upah'])
        if key in wilayah_upah: galat.append(f'upah_minimum:{i}: duplikat wilayah/tahun/jenis')
        wilayah_upah.add(key)
        tahun('upah_minimum',i,item)
        uang('upah_minimum',i,item)
        if not tanggal(item['tanggal_mulai']): galat.append(f'upah_minimum:{i}: tanggal berlaku tidak valid')

    for i,item in enumerate(data['statistik_upah'],2):
        sumber_item = cek_sumber('statistik_upah',i,item)
        tempat = wilayah.get((item['sistem_kode'],item['kode_wilayah']))
        if not tempat or tempat['status_verifikasi']!='terverifikasi':
            galat.append(f'statistik_upah:{i}: wilayah harus terverifikasi')
        if item['id_pekerjaan'] and item['id_pekerjaan'] not in pekerjaan:
            galat.append(f'statistik_upah:{i}: pekerjaan tidak ditemukan')
        if item['id_jabatan'] and item['id_jabatan'] not in jabatan:
            galat.append(f'statistik_upah:{i}: jabatan tidak ditemukan')
        if item['jenis_data']=='resmi' and sumber_item and sumber_item['kind']!='official':
            galat.append(f'statistik_upah:{i}: statistik resmi harus bersumber dari lembaga resmi')
        if item['jenis_data'] not in ('resmi','survei','estimasi') or item['metrik'] not in ('rata_rata','median','persentil_25','persentil_75'):
            galat.append(f'statistik_upah:{i}: metode/jenis statistik tidak valid')
        if item['satuan'] not in ('per_bulan','per_jam') or item['cakupan_pekerja'] not in ('semua','formal','informal'):
            galat.append(f'statistik_upah:{i}: satuan/cakupan tidak valid')
        if item['status_verifikasi'] not in ('draf','terverifikasi'):
            galat.append(f'statistik_upah:{i}: status tidak valid')
        if item['jumlah_sampel'] and (not item['jumlah_sampel'].isdigit()):
            galat.append(f'statistik_upah:{i}: jumlah sampel tidak valid')
        tahun('statistik_upah',i,item)
        uang('statistik_upah',i,item,positif=False)

    kelas = set()
    for i,item in enumerate(data['kelas_gaji'],2):
        cek_sumber('kelas_gaji',i,item)
        k=(item['sistem_penggajian'],item['kode_kelas'],item['tahun'])
        if k in kelas: galat.append(f'kelas_gaji:{i}: kelas gaji ganda')
        kelas.add(k)
        if not item['sistem_penggajian'] or not item['kode_kelas'] or item['status_verifikasi'] not in ('draf','terverifikasi'):
            galat.append(f'kelas_gaji:{i}: kelas/status tidak valid')
        tahun('kelas_gaji',i,item)
        if item['nilai_dasar_rupiah']: uang('kelas_gaji',i,item,'nilai_dasar_rupiah',False)
    kunci_internasional=set()
    for i,item in enumerate(data['pemetaan_internasional'],2):
        sumber_item=sumber.get(item['sumber_id'])
        if item['id_pekerjaan'] not in pekerjaan or not sumber_item or sumber_item['kind']!='official':
            galat.append(f'pemetaan_internasional:{i}: pekerjaan/sumber resmi tidak valid')
        if not all(item.get(k) for k in ('sistem_klasifikasi','edisi','kode','nama_resmi','diverifikasi_oleh')) or not tanggal(item['tanggal_verifikasi']):
            galat.append(f'pemetaan_internasional:{i}: verifikasi dan edisi wajib')
        if item['sistem_klasifikasi'] not in ('ISCO','ESCO','O_NET'):
            galat.append(f'pemetaan_internasional:{i}: klasifikasi tidak didukung')
        if not sumber_item or not sumber_item.get('uri'):
            galat.append(f'pemetaan_internasional:{i}: URI sumber resmi wajib')
        kunci=(item['id_pekerjaan'],item['sistem_klasifikasi'],item['edisi'],item['kode'])
        if kunci in kunci_internasional: galat.append(f'pemetaan_internasional:{i}: pemetaan duplikat')
        kunci_internasional.add(kunci)
    return galat, {key:len(rows) for key,rows in data.items()}
