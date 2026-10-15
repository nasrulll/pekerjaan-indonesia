/** Klien RPI baca-saja. Gunakan HTTPS pada produksi. */
export class KlienRPI {
  constructor(private readonly asal: string) {
    if (!(asal.startsWith('https://') || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(asal))) {
      throw new Error('Server publik wajib HTTPS');
    }
  }
  async ambil(rute: `/v1/${string}`, opsi: Record<string, string | number | undefined> = {}) {
    const url = new URL(rute, this.asal);
    Object.entries(opsi).forEach(([k, v]) => { if (v !== undefined) url.searchParams.set(k, String(v)); });
    const res = await fetch(url, {method:'GET', headers:{Accept:'application/json'}});
    if (!res.ok) throw new Error(`RPI HTTP ${res.status}`);
    return res.json();
  }
  pekerjaan(nama = '', batas = 25) { return this.ambil('/v1/pekerjaan', {nama, batas}); }
  upahMinimum(tahun?: number) { return this.ambil('/v1/upah-minimum', {tahun}); }
}
