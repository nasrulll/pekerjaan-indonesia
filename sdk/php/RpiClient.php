<?php
declare(strict_types=1);
/** Contoh klien baca-saja PHP; untuk produksi gunakan HTTPS. */
final class KlienRPI {
    public function __construct(private string $asal) {
        if (!str_starts_with($asal, 'https://') && !preg_match('~^http://(localhost|127\.0\.0\.1)(:\d+)?$~', $asal)) {
            throw new InvalidArgumentException('Gunakan HTTPS untuk server publik');
        }
    }
    public function pekerjaan(string $nama = ''): array {
        $url = rtrim($this->asal, '/') . '/v1/pekerjaan?' . http_build_query(['nama' => $nama]);
        $ctx = stream_context_create(['http' => ['timeout' => 15, 'method' => 'GET']]);
        $body = file_get_contents($url, false, $ctx);
        if ($body === false) throw new RuntimeException('Gagal mengakses API RPI');
        return json_decode($body, true, flags: JSON_THROW_ON_ERROR);
    }
}
