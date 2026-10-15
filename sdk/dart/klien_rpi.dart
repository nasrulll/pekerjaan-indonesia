import 'dart:convert';
import 'dart:io';

/// Dart/Flutter: contoh klien HTTP baca-saja.
class KlienRPI {
  KlienRPI(this.asal) {
    if (Uri.parse(asal).scheme != 'https') {
      throw ArgumentError('Server publik harus HTTPS');
    }
  }
  final String asal;
  Future<Map<String, dynamic>> pekerjaan(String nama) async {
    final uri = Uri.parse(asal).resolve('/v1/pekerjaan').replace(queryParameters: {'nama': nama});
    final client = HttpClient()..connectionTimeout = const Duration(seconds: 15);
    try {
      final request = await client.getUrl(uri);
      final response = await request.close();
      if (response.statusCode != 200) throw HttpException('RPI HTTP ${response.statusCode}');
      return jsonDecode(await utf8.decoder.bind(response).join()) as Map<String, dynamic>;
    } finally {
      client.close();
    }
  }
}
