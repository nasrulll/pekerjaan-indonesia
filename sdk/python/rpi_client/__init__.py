"""Klien Python ringan (dependensi stdlib); API baca-saja."""
from urllib.parse import urlencode
from urllib.request import urlopen
import json

class KlienRPI:
    def __init__(self, alamat, timeout=15):
        if not alamat.startswith(('https://','http://127.0.0.1:','http://localhost:')):
            raise ValueError('Gunakan HTTPS untuk server publik')
        self.alamat=alamat.rstrip('/')
        self.timeout=timeout

    def ambil(self, rute, **parameter):
        if not rute.startswith('/v1/'):
            raise ValueError('Rute baca-saja harus dimulai /v1/')
        param={k:v for k,v in parameter.items() if v is not None}
        url=self.alamat+rute+('?' + urlencode(param) if param else '')
        with urlopen(url,timeout=self.timeout) as resp:
            return json.load(resp)

    def pekerjaan(self,nama='',batas=25):
        return self.ambil('/v1/pekerjaan',nama=nama,batas=batas)

    def wilayah(self,sistem_kode=None):
        return self.ambil('/v1/wilayah',sistem_kode=sistem_kode)
